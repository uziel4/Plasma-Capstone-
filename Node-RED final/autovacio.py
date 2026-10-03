"""Reglas de AutoVacio. Actuacion pendiente de integrar masscontroll.py.

Bombas mecanicas A/B deben permanecer ON durante AutoVacio, incluso al
alcanzar el objetivo. Estas reglas no arrancan bombas ni ejecutan secuencias.
Seleccion por rango implementada en selector_vacio.py, sin exigir concordancia entre sensores; ciclo actuador pendiente.
Faltan ciclo actuador, tolerancia, limites y significado del flujo deseado.
"""
import math
from errores import ControlError
from selector_vacio import SelectorVacio

BOMBAS_CONTINUAS = ('Mechanical Pump A', 'Mechanical Pump B')
SENSOR_CONTROL = None
TOLERANCIA_TORR = None
MASS_FLOW_DISPONIBLE = False


def comprobar_disponibilidad():
    if not MASS_FLOW_DISPONIBLE or SENSOR_CONTROL is None or TOLERANCIA_TORR is None:
        raise ControlError('AUTO_CONFIG', 'AutoVacio aun no puede activarse')


def accion_mass_flow(presion_torr, objetivo_torr, tolerancia_torr):
    """Direccion de ajuste; no calcula caudal, no envia ordenes al hardware."""
    if any(type(v) not in (int, float) or not math.isfinite(v)
           for v in (presion_torr, objetivo_torr, tolerancia_torr)):
        raise ControlError('AUTO_VALUE', 'Presion, objetivo o tolerancia invalidos')
    if presion_torr <= 0 or not 0 < objetivo_torr < 760 or not 0 <= tolerancia_torr < objetivo_torr:
        raise ControlError('AUTO_VALUE', 'Presion, objetivo o tolerancia fuera de rango')
    if presion_torr < objetivo_torr - tolerancia_torr:
        return 'ABRIR_MAS'  # Mas gas eleva presion: reduce el exceso de vacio.
    if presion_torr > objetivo_torr + tolerancia_torr:
        return 'CERRAR_MAS'  # Menos gas permite a las bombas reducir presion.
    return 'MANTENER'


def accion_con_sensores(selector, lecturas, timestamp, ahora, objetivo_torr, tolerancia_torr):
    """Selecciona lectura y calcula direccion; nunca escribe al mass flow."""
    seleccion = selector.seleccionar(lecturas, timestamp, ahora)
    accion = accion_mass_flow(seleccion['torr'], objetivo_torr, tolerancia_torr)
    return {**seleccion, 'accion': accion}
