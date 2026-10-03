"""Sensor de temperatura del agua: transmisor de corriente, conversion a Celsius."""
import math
from hardware_bus import SPI_LOCK
from errores import ControlError

ADC_ADDRESS = 3
CANAL = 'I0'  # Indice logico ADC 12; no es el pin fisico 12 de Raspberry.
# Formula confirmada por el usuario: 4-20 mA = 0-100 grados Celsius.

def calcular_celsius(ma):
    if type(ma) not in (int, float) or not math.isfinite(ma):
        raise ControlError('WATER_TEMP_VALUE', 'Corriente de temperatura invalida', repr(ma))
    if not 4 <= ma <= 20:
        raise ControlError('WATER_TEMP_RANGE', 'Corriente fuera de 4-20 mA', repr(ma))
    return (ma - 4) * 6.25



def leer_corriente(driver):
    context = dict(equipo='Temperatura del agua', address=ADC_ADDRESS, canal=CANAL)
    try:
        with SPI_LOCK:
            value = driver.getADC(ADC_ADDRESS, CANAL)
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ControlError('WATER_TEMP_VALUE', 'Corriente de temperatura del agua invalida', repr(value), **context)
        return {'ma': value, 'celsius': calcular_celsius(value), 'channel': CANAL, 'error': None}
    except Exception as exc:
        error = exc if isinstance(exc, ControlError) else ControlError('WATER_TEMP_READ', 'No se pudo leer corriente de temperatura del agua', repr(exc), **context)
        return {'ma': None, 'celsius': None, 'channel': CANAL, 'error': error.payload()}
