"""Presiones Air/Coolant/Water por ADCplate. Vacio se integrara aparte."""
import logging
import math
import time
from threading import Lock
from hardware_bus import SPI_LOCK
from errores import ControlError
from temperatura_agua import leer_corriente
from vacio import leer_vacios
from masscontroll import leer_flujo

ADC_ADDRESS = 3
SENSORES = {
    'Air': {'canal': 'I3', 'max_psi': 232.0},
    'Coolant': {'canal': 'I2', 'max_psi': 232.0},
    'Water': {'canal': 'I1', 'max_psi': 232.0},
}


def calcular_psi(current_ma, max_psi):
    if type(current_ma) not in (float, int) or not math.isfinite(current_ma):
        raise ValueError(f'Corriente invalida: {current_ma!r}')
    return max(0.0, (current_ma - 4.0) / 16.0 * max_psi)


class Presiones:
    def __init__(self):
        self.driver = None
        self.lock = Lock()
        self.next_init = 0
        self.init_error = None
        self.next_read = 0
        self.cache = None
        self.errors = {}

    def _initialize(self):
        try:
            with SPI_LOCK:
                import piplates.ADCplate as driver
                identity = driver.getID(ADC_ADDRESS)
                if 'ADCPLATE' not in str(identity).upper():
                    raise RuntimeError(f'Identificacion inesperada: {identity!r}')
                driver.initADC(ADC_ADDRESS)
                driver.setMODE(ADC_ADDRESS, 'HIGH')
            # Espera de actualizacion sin bloquear las otras placas.
            time.sleep(1)
            self.driver = driver
            self.init_error = None
        except Exception as exc:
            self.init_error = ControlError('PRESS_INIT', 'No se pudo inicializar ADCplate', repr(exc), address=ADC_ADDRESS)
            self.next_init = time.monotonic() + 5

    def read(self):
        with self.lock:
            if self.cache is not None and time.monotonic() < self.next_read:
                return self.cache
            if self.driver is None and time.monotonic() >= self.next_init:
                self._initialize()
            values = {}
            for name, config in SENSORES.items():
                context = dict(equipo=name, address=ADC_ADDRESS, canal=config['canal'])
                current = None
                psi = None
                error = None
                try:
                    if self.driver is None:
                        raise self.init_error
                    try:
                        with SPI_LOCK:
                            current = self.driver.getADC(ADC_ADDRESS, config['canal'])
                    except Exception as exc:
                        raise ControlError('PRESS_READ', 'Fallo al leer corriente', repr(exc), **context) from exc
                    try:
                        psi = calcular_psi(current, config['max_psi'])
                    except ValueError as exc:
                        current = None
                        raise ControlError('PRESS_VALUE', 'Respuesta de corriente invalida', str(exc), **context) from exc
                    if not 4 <= current <= 20:
                        raise ControlError('PRESS_RANGE', 'Presion no confiable: corriente fuera de 4-20 mA', corriente_ma=current, **context)
                except ControlError as exc:
                    error = exc.payload()
                values[name] = {'psi': psi, 'ma': current, 'error': error, 'channel': config['canal']}
                message = error['error'] if error else None
                if message and self.errors.get(name) != message:
                    logging.error('%s', message)
                    self.errors[name] = message
                elif not message and name in self.errors:
                    logging.info('Presion recuperada: %s', name)
                    del self.errors[name]
            water = leer_corriente(self.driver) if self.driver is not None else {
                'ma': None, 'celsius': None, 'channel': 'I0', 'error': self.init_error.payload()}
            vacuum = leer_vacios(self.driver, self.init_error)
            for name, entry in vacuum.items():
                message = entry['error']['error'] if entry['error'] else None
                if message and self.errors.get(name) != message:
                    logging.error('%s', message)
                    self.errors[name] = message
                elif not message and name in self.errors:
                    logging.info('Lectura de vacio recuperada: %s', name)
                    del self.errors[name]
            self.cache = {'pressures': values, 'water_temperature': water, 'vacuum': vacuum, 'mass_flow': leer_flujo(self.driver), 'timestamp': time.time()}
            self.next_read = time.monotonic() + 1
            return self.cache
