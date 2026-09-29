"""Aera analogico: ADC3/S4 lectura, DAQC2 4/DAC0 consigna.

No escribe al arrancar. El pin 1 de override debe estar en modo normal.
Cero consigna no confirma cierre mecanico ni es un aislamiento de gas.
"""
import math
import time
from threading import RLock
from hardware_bus import SPI_LOCK
from errores import ControlError

DAC_ADDRESS = 4
DAC_CHANNEL = 0
ADC_CHANNEL = 'S4'
MAX_VOLTS = 4.095
MAX_PERCENT = round(MAX_VOLTS * 20, 1)
FULL_SCALE_SCCM = None  # Rango activo del gas; no asumir 200 SCCM.


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def percent_to_volts(percent):
    if not number(percent) or not 0 <= percent <= MAX_PERCENT:
        raise ControlError('MFC_INPUT', 'Consigna fuera de rango', f'Use 0 a {MAX_PERCENT}%')
    return round(percent / 20, 3)


def leer_flujo(driver):
    try:
        if driver is None:
            raise RuntimeError('ADCplate no disponible')
        with SPI_LOCK:
            volts = driver.getADC(3, ADC_CHANNEL)
        if not number(volts) or not 0 <= volts <= 5:
            raise ValueError(f'Lectura fuera de 0-5 V: {volts!r}')
        percent = volts * 20
        return {'volts': volts, 'percent': percent,
                'sccm': percent / 100 * FULL_SCALE_SCCM if FULL_SCALE_SCCM else None,
                'error': None}
    except Exception as exc:
        error = ControlError('MFC_READ', 'No se pudo leer el caudal', repr(exc), address=3, canal=ADC_CHANNEL)
        return {'volts': None, 'percent': None, 'sccm': None, 'error': error.payload()}


class MassControl:
    def __init__(self):
        self.driver = None
        self.lock = RLock()

    def _driver(self):
        if self.driver is None:
            import piplates.DAQC2plate as driver
            identity = driver.getID(DAC_ADDRESS)
            if 'DAQC2' not in str(identity).upper():
                raise RuntimeError(f'Identificacion inesperada: {identity!r}')
            self.driver = driver
        return self.driver

    def state(self):
        with self.lock:
            try:
                with SPI_LOCK:
                    volts = self._driver().getDAC(DAC_ADDRESS, DAC_CHANNEL)
                if not number(volts) or not 0 <= volts <= MAX_VOLTS:
                    raise ValueError(f'DAC invalido: {volts!r}')
                return {'command_percent': volts * 20, 'command_volts': volts,
                        'max_percent': MAX_PERCENT, 'timestamp': time.time()}
            except Exception as exc:
                self.driver = None
                raise ControlError('MFC_DAC', 'No se pudo consultar la consigna DAC', repr(exc), address=DAC_ADDRESS, canal=DAC_CHANNEL) from exc

    def set_percent(self, percent):
        volts = percent_to_volts(percent)
        with self.lock:
            try:
                with SPI_LOCK:
                    self._driver().setDAC(DAC_ADDRESS, DAC_CHANNEL, volts)
                result = self.state()
                if abs(result['command_volts'] - volts) > .002:
                    raise RuntimeError(f"Consigna no confirmada: {result['command_volts']} V")
                return result
            except Exception as exc:
                self.driver = None
                raise ControlError('MFC_WRITE', 'No se pudo confirmar la consigna; estado incierto', repr(exc), address=DAC_ADDRESS, canal=DAC_CHANNEL) from exc
