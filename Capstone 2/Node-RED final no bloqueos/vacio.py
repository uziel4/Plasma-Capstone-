"""Lectura y conversion de vacio por ADCplate address 3."""
import math
from hardware_bus import SPI_LOCK
from errores import ControlError

# P(Torr) = 10 ** (pendiente * V + offset). Cambiar por sensor si cambia modelo.
SENSORES = {
    'Medium Vacuum': {'canal': 'S0', 'modelo': 'Terranova 906A', 'pendiente': 2.0, 'offset': -3.0},
    'High Vacuum': {'canal': 'S1', 'modelo': 'GP270'},
}


def voltaje_a_torr(voltage, pendiente=2.0, offset=-3.0):
    """Terranova 906A: P(mTorr)=10**(2*V); P(Torr)=10**(2*V-3).

    Su aplicacion requiere que el controlador del sensor use esta transferencia.
    No detecta desconexion ni estados de fallo del controlador por si sola.
    """
    if type(voltage) not in (int, float) or not math.isfinite(voltage):
        raise ControlError('VAC_VALUE', 'Voltaje de vacio invalido', repr(voltage), address=3)
    try:
        pressure = 10.0 ** (pendiente * voltage + offset)
    except OverflowError as exc:
        raise ControlError('VAC_RANGE', 'Voltaje fuera del rango calculable', repr(voltage), address=3) from exc
    if not math.isfinite(pressure) or pressure <= 0:
        raise ControlError('VAC_RANGE', 'Presion fuera del rango calculable', repr(voltage), address=3)
    return pressure


def terranova906a_a_torr(voltage):
    """Manual rev0817NC pp.13-14, salida analogica, unidad Torr/mTorr.

    0 V identifica LO y aproximadamente 3 V OFF/HI. La señal analogica
    no permite distinguir todos los estados; no inferir presion con esos extremos.
    """
    if type(voltage) not in (int, float) or not math.isfinite(voltage):
        raise ControlError('VAC_VALUE', 'Voltaje Terranova invalido', repr(voltage))
    if not 0 < voltage < 3:
        raise ControlError('VAC_TN906_STATE', 'Terranova: salida no utilizable como presion',
                           f'{voltage} V; LO, OFF/HI o señal fuera de rango')
    return voltaje_a_torr(voltage, 2.0, -3.0)


def gp270_a_torr(voltage):
    """GP270, manual 4-8: salida negativa por tramos, no formula 972B.

    Conversion nominal en Torr: cada tramo de 1 V corresponde a una
    escala lineal 0-10 multiplicada por la decada indicada (manual 4-8).
    Esta interpretacion nominal requiere contraste fisico, especialmente
    cerca de las transiciones de autorange. No es una calibracion realizada.
    """
    if type(voltage) not in (int, float) or not math.isfinite(voltage):
        raise ControlError('VAC_VALUE', 'Voltaje GP270 invalido', repr(voltage))
    if -12 <= voltage <= -10:
        raise ControlError('VAC_GP270_STATE', 'GP270: salida de estado invalido',
                           f'{voltage} V; posible filamento apagado o rango manual')
    if not -5 <= voltage <= 0:
        raise ControlError('VAC_GP270_RANGE', 'GP270: fuera de 0 a -5 V', f'{voltage} V')
    magnitude = -voltage
    # El extremo entero pertenece al final del tramo anterior: -1 V -> 10e-8.
    tramo = max(0, min(4, math.ceil(magnitude) - 1))
    pressure = (magnitude - tramo) * 10.0 * 10.0 ** (tramo - 8)
    if pressure <= 0:
        raise ControlError('VAC_GP270_ZERO', 'GP270: presion no resoluble a 0 V',
                           'No interpretar cero voltios como vacio perfecto; revisar controlador y cableado')
    return pressure


def leer_vacios(driver, init_error=None):
    readings = {}
    for name, config in SENSORES.items():
        context = dict(equipo=name, address=3, canal=config['canal'], modelo=config['modelo'])
        voltage = None
        try:
            if driver is None:
                raise ControlError('VAC_READ', 'ADCplate no disponible', str(init_error), **context)
            try:
                with SPI_LOCK:
                    voltage = driver.getADC(3, config['canal'])
            except Exception as exc:
                raise ControlError('VAC_READ', 'No se pudo leer voltaje de vacio', repr(exc), **context) from exc
            try:
                pressure = (gp270_a_torr(voltage) if config['modelo'] == 'GP270'
                            else terranova906a_a_torr(voltage))
            except ControlError as exc:
                raise ControlError(exc.code, exc.message, exc.detail, **context) from exc
            readings[name] = {'volts': voltage, 'torr': pressure, 'channel': config['canal'], 'error': None}
        except ControlError as exc:
            readings[name] = {'volts': voltage if type(voltage) in (int, float) and math.isfinite(voltage) else None,
                              'torr': None, 'channel': config['canal'], 'error': exc.payload()}
    return readings
