"""Roughing Vacuum Gauges A/B por ADCplate address 3, canales S4 y S5.

Escala del sensor: 0 V = 0 % = 1e-3 Torr; 10 V = 100 % = 1000 Torr.
Solo se presenta el voltaje como barra de 0-10 V; no se convierte a Torr.
"""
import math
from hardware_bus import SPI_LOCK
from errores import ControlError

ADC_ADDRESS = 3
ROUGH_SENSORES = {'Rough Manifold A': 'S4', 'Rough Manifold B': 'S5'}
ROUGH_VOLTS = (0.0, 10.0)
ROUGH_TORR = (1e-3, 1000.0)  # Extremos de la escala, solo como referencia visual
ROUGH_TOLERANCE_V = 0.05  # Ruido del ADC aceptado fuera de 0-10 V; la barra se limita a 0-100 %


def voltaje_a_porcentaje(voltage):
    if type(voltage) not in (int, float) or not math.isfinite(voltage):
        raise ControlError('ROUGH_VALUE', 'Voltaje Rough invalido', repr(voltage))
    low, high = ROUGH_VOLTS
    if not low - ROUGH_TOLERANCE_V <= voltage <= high + ROUGH_TOLERANCE_V:
        raise ControlError('ROUGH_RANGE', 'Rough: voltaje fuera de 0-10 V', f'{voltage} V')
    return min(100.0, max(0.0, (voltage - low) / (high - low) * 100.0))


def leer_rough(driver, init_error=None):
    readings = {}
    for name, canal in ROUGH_SENSORES.items():
        context = dict(equipo=name, address=ADC_ADDRESS, canal=canal)
        voltage = None
        try:
            if driver is None:
                raise ControlError('ROUGH_READ', 'ADCplate no disponible', str(init_error), **context)
            try:
                with SPI_LOCK:
                    voltage = driver.getADC(ADC_ADDRESS, canal)
            except Exception as exc:
                raise ControlError('ROUGH_READ', 'No se pudo leer voltaje Rough', repr(exc), **context) from exc
            try:
                percent = voltaje_a_porcentaje(voltage)
            except ControlError as exc:
                raise ControlError(exc.code, exc.message, exc.detail, **context) from exc
            readings[name] = {'volts': voltage, 'percent': percent, 'channel': canal, 'error': None}
        except ControlError as exc:
            readings[name] = {'volts': voltage if type(voltage) in (int, float) and math.isfinite(voltage) else None,
                              'percent': None, 'channel': canal, 'error': exc.payload()}
    return readings
