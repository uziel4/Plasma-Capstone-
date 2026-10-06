"""Configuracion y operaciones de Manual Control. Numeracion de reles: 1-8."""
import math
import time
from hardware_bus import SPI_LOCK
from errores import ControlError

RELAY_ADDRESSES = (0, 1)  # RELAYplate2 #1 = address 0, #2 = address 1
THERMO_ADDRESS = 2
ADC_ADDRESS = 3
# Nombre mostrado en el GUI: (address, rele). None = pendiente de cableado.
RELAYS = {
    'Air Compressor': (0, 1),
    'Water Chiller': (0, 2),
    'Booster Pump': (0, 3), 'Cool Trap A': (0, 4), 'Cool Trap B': (0, 5),
    'Chamber Valve A': (0, 8), 'Chamber Valve B': (1, 1),
    'Mechanical Pump A': (1, 2), 'Mechanical Pump B': (1, 3),
    'Diffusion Pump A': (1, 4), 'Diffusion Pump B': (1, 5),
    'Gate Valve A': (1, 6), 'Gate Valve B': (1, 7),
    'Diffuse Valve A': (0, 6), 'Diffuse Valve B': (0, 7),
    'Buzzer': (1, 8),
}


# Permisos manuales permanentes. Booster Pump: siempre habilitado por decision del usuario.
PERMANENT_MANUAL_ALLOWED = frozenset({
    'Air Compressor', 'Water Chiller', 'Cool Trap A', 'Cool Trap B',
    'Mechanical Pump A', 'Mechanical Pump B', 'Booster Pump',
})
# Ampliacion temporal solicitada por el usuario mientras se aclara una duda.
TEMPORARY_MANUAL_ALLOWED = frozenset({'Buzzer'})
# ON manual solo con los equipos de los pasos previos del startup 2026 encendidos.
# OFF sigue permitido. Water Level Solenoid esta excluido del proyecto.
STARTUP_PREREQUISITES = ('Air Compressor', 'Water Chiller', 'Booster Pump', 'Cool Trap A', 'Cool Trap B')
CHAMBER_PREREQUISITES = STARTUP_PREREQUISITES + ('Diffuse Valve A', 'Diffuse Valve B')
# Gate Valve A/B (paso 15): pasos 2-7, 9 y 12 encendidos; 11 vacio; 13 temperatura; 14 Chamber OFF.
GATE_PREREQUISITES = CHAMBER_PREREQUISITES + ('Mechanical Pump A', 'Mechanical Pump B',
                                              'Diffusion Pump A', 'Diffusion Pump B')
GATE_VALVES = ('Gate Valve A', 'Gate Valve B')
GATE_CLOSED = ('Chamber Valve A', 'Chamber Valve B')
GATE_VACUUM_TORR = (0.001, 0.030)  # Paso 11: 1-30 mTorr, mismos limites que startup.py
GATE_TEMPERATURE_C = ((250 - 32) * 5 / 9, (300 - 32) * 5 / 9)  # Paso 13: 250-300 °F
MANUAL_PREREQUISITES = {
    'Diffuse Valve A': STARTUP_PREREQUISITES,
    'Diffuse Valve B': STARTUP_PREREQUISITES,
    'Chamber Valve A': CHAMBER_PREREQUISITES,
    'Chamber Valve B': CHAMBER_PREREQUISITES,
    'Gate Valve A': GATE_PREREQUISITES,
    'Gate Valve B': GATE_PREREQUISITES,
}
INITIAL_MANUAL_ALLOWED = PERMANENT_MANUAL_ALLOWED | TEMPORARY_MANUAL_ALLOWED | frozenset(MANUAL_PREREQUISITES)


class ManualControl:
    def __init__(self, plant=None):
        if plant is None:
            from planta import Planta
            plant = Planta()
        self.driver = plant
        self.lock = plant.lock

    def _states(self):
        masks = {}
        for address in RELAY_ADDRESSES:
            try:
                mask = self.driver.relaySTATE(address)
            except Exception as exc:
                raise ControlError('HW_READ', 'No se pudo leer la placa', repr(exc), address=address, operacion='relaySTATE') from exc
            if type(mask) is not int or not 0 <= mask <= 255:
                raise ControlError('HW_STATE', 'Estado recibido invalido', repr(mask), address=address)
            masks[address] = mask
        return {'relays': {
            name: {'configured': wiring is not None,
                   'manual_allowed': name in INITIAL_MANUAL_ALLOWED,
                   'on': bool(masks[wiring[0]] & (1 << (wiring[1] - 1))) if wiring else None}
            for name, wiring in RELAYS.items()}}

    def states(self):
        with self.lock:
            return self._states()

    @staticmethod
    def diffusion_ready(packet):
        packet = packet or {}
        stamp = packet.get('timestamp')
        entry = (packet.get('vacuum') or {}).get('Medium Vacuum') or {}
        pressure = entry.get('torr')
        return (type(stamp) in (int, float) and math.isfinite(stamp)
                and 0 <= time.time() - stamp <= 3
                and not entry.get('error')
                and type(pressure) in (int, float) and math.isfinite(pressure)
                and 0 < pressure < 0.030)

    @staticmethod
    def missing_prerequisites(name, relays):
        return [item for item in MANUAL_PREREQUISITES.get(name, ()) if relays[item]['on'] is not True]

    @staticmethod
    def fresh_values(packet, group, names, field):
        """Valores validos con antiguedad de 0-3 s; None si falta o tiene error."""
        packet = packet or {}
        stamp = packet.get('timestamp')
        if type(stamp) not in (int, float) or not math.isfinite(stamp) or not 0 <= time.time() - stamp <= 3:
            return [None for _ in names]
        entries = [(packet.get(group) or {}).get(n) or {} for n in names]
        return [e.get(field) if not e.get('error') and type(e.get(field)) in (int, float) and math.isfinite(e.get(field))
                else None for e in entries]

    @classmethod
    def blocked_reasons(cls, name, relays, packet=None, temperatures=None):
        """Motivos que impiden el ON manual; lista vacia si se permite."""
        reasons = []
        missing = cls.missing_prerequisites(name, relays)
        if missing:
            reasons.append('falta encender ' + ', '.join(missing))
        if name in GATE_VALVES:
            opened = [item for item in GATE_CLOSED if relays[item]['on'] is not False]
            if opened:
                reasons.append('falta apagar ' + ', '.join(opened))
            low, high = GATE_VACUUM_TORR
            pressure, = cls.fresh_values(packet, 'vacuum', ['Medium Vacuum'], 'torr')
            if pressure is None or not low <= pressure <= high:
                reasons.append('Medium debe estar entre 0.001 y 0.030 Torr con lectura valida y reciente')
            low, high = GATE_TEMPERATURE_C
            pumps = cls.fresh_values(temperatures, 'temperatures', ['Diffusion Pump A', 'Diffusion Pump B'], 'celsius')
            if any(t is None or not low <= t <= high for t in pumps):
                reasons.append('ambas Diffusion Pump deben estar entre 250 y 300 °F con lectura valida y reciente')
        return reasons

    def manual_states(self, packet=None, temperatures=None):
        result = self.states()
        for name in MANUAL_PREREQUISITES:
            entry = result['relays'][name]
            reasons = self.blocked_reasons(name, result['relays'], packet, temperatures)
            entry['manual_allowed'] = entry['on'] or not reasons
            entry['manual_reason'] = ('Control manual disponible' if entry['manual_allowed']
                                      else 'Encendido bloqueado: ' + '; '.join(reasons))
        ready = self.diffusion_ready(packet)
        for name in ('Diffusion Pump A', 'Diffusion Pump B'):
            entry = result['relays'][name]
            # Permitir apagar incluso si se pierde la condicion de vacio.
            entry['manual_allowed'] = entry['on'] or ready
            entry['manual_reason'] = ('Control manual disponible' if entry['manual_allowed']
                                      else 'Encendido bloqueado: Medium debe ser menor de 0.030 Torr, con lectura valida y reciente')
        return result

    def set_manual_relay(self, name, on, read_pressures=None, read_temperatures=None):
        if type(on) is not bool:
            raise ControlError('INPUT', 'El estado debe ser true o false', equipo=name)
        if name in ('Diffusion Pump A', 'Diffusion Pump B'):
            if on and not self.diffusion_ready(read_pressures() if read_pressures else None):
                raise ControlError('INPUT', 'Encendido bloqueado: Medium debe ser menor de 0.030 Torr con lectura valida y reciente', equipo=name)
        elif name in MANUAL_PREREQUISITES:
            if on:
                needs_readings = name in GATE_VALVES
                reasons = self.blocked_reasons(
                    name, self.states()['relays'],
                    read_pressures() if needs_readings and read_pressures else None,
                    read_temperatures() if needs_readings and read_temperatures else None)
                if reasons:
                    raise ControlError('INPUT', 'Encendido bloqueado: ' + '; '.join(reasons), equipo=name)
        elif name not in INITIAL_MANUAL_ALLOWED:
            raise ControlError('INPUT', 'Equipo bloqueado en la etapa inicial de control manual', equipo=name)
        self.set_relay(name, on)
        return self.manual_states(read_pressures() if read_pressures else None,
                                  read_temperatures() if read_temperatures else None)

    def set_relay(self, name, on):
        if name not in RELAYS or RELAYS[name] is None:
            raise ControlError('INPUT', 'Equipo sin rele configurado', equipo=name)
        if type(on) is not bool:
            raise ControlError('INPUT', 'El estado debe ser true o false', repr(on), equipo=name)
        address, relay = RELAYS[name]
        with self.lock:
            action = self.driver.relayON if on else self.driver.relayOFF
            context = dict(equipo=name, address=address, rele=relay, solicitado='ON' if on else 'OFF')
            try:
                action(address, relay)
            except Exception as exc:
                raise ControlError('HW_WRITE', 'Error al enviar la orden', repr(exc), **context) from exc
            try:
                result = self._states()
            except Exception as exc:
                raise ControlError('HW_CONFIRM', 'Orden enviada sin confirmacion de estado', str(exc), **context) from exc
            if result['relays'][name]['on'] != on:
                raise ControlError('HW_CONFIRM', 'Estado leido distinto al solicitado', observado=result['relays'][name]['on'], **context)
            return result
