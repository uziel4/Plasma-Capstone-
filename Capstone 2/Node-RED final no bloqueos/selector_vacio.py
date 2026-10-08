"""Seleccion Medium/High por lectura valida; no escribe salidas.

Medium valido por encima del limite tiene prioridad para detectar el regreso.
Ver SELECCION_VACIO.md para limites y tratamiento de errores.
"""
import math
from errores import ControlError

HIGH_MIN_TORR = 3e-9
HIGH_MAX_TORR = 1e-3
MAX_EDAD_SEGUNDOS = 3.0
MEDIUM = 'Medium Vacuum'
HIGH = 'High Vacuum'


def _numero(value):
    return type(value) in (int, float) and math.isfinite(value)


def _lectura(readings, name):
    entry = readings.get(name)
    if not isinstance(entry, dict) or entry.get('error'):
        return None
    value = entry.get('torr')
    return value if _numero(value) and value > 0 else None


class SelectorVacio:
    def __init__(self):
        self.sensor = MEDIUM
        self.ultimo_timestamp = None

    def seleccionar(self, readings, timestamp, ahora):
        """Paquete UNIX nuevo. El llamador serializa acceso; errores no dan orden."""
        if (not _numero(timestamp) or not _numero(ahora)
                or not 0 <= ahora - timestamp <= MAX_EDAD_SEGUNDOS
                or (self.ultimo_timestamp is not None and timestamp <= self.ultimo_timestamp)
                or not isinstance(readings, dict)):
            raise ControlError('AUTO_SENSOR', 'Paquete de vacio invalido, vencido o repetido')
        self.ultimo_timestamp = timestamp
        medium = _lectura(readings, MEDIUM)
        high = _lectura(readings, HIGH)
        medium_valid = medium is not None and HIGH_MAX_TORR <= medium <= 1000
        if medium_valid and medium > HIGH_MAX_TORR:
            # Detecta el regreso incluso si High satura o informa un error.
            selected, pressure = MEDIUM, medium
        elif high is not None and HIGH_MIN_TORR <= high <= HIGH_MAX_TORR:
            selected, pressure = HIGH, high
        elif medium_valid:
            # En el limite exacto se usa Medium si High no esta disponible.
            selected, pressure = MEDIUM, medium
        else:
            raise ControlError('AUTO_SENSOR', 'No hay lectura valida para seleccionar Medium o High')
        self.sensor = selected
        return {'sensor': selected, 'torr': pressure}
