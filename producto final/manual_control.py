"""Configuracion y operaciones de Manual Control. Numeracion de reles: 1-8."""
from hardware_bus import SPI_LOCK
from errores import ControlError

RELAY_ADDRESSES = (0, 1)
THERMO_ADDRESS = 2
ADC_ADDRESS = 3
# Nombre mostrado en el GUI: (address, rele). None = pendiente de cableado.
RELAYS = {
    'Air Compressor': (0, 1), 'Water Chiller': (0, 2),
    'Booster Pump': (0, 3), 'Cool Trap A': (0, 4), 'Cool Trap B': (0, 5),
    'Chamber Valve A': (0, 8), 'Chamber Valve B': (1, 1),
    'Mechanical Pump A': (1, 2), 'Mechanical Pump B': (1, 3),
    'Diffusion Pump A': (1, 4), 'Diffusion Pump B': (1, 5),
    'Gate Valve A': (1, 6), 'Gate Valve B': (1, 7),
    'Diffuse Valve A': (0, 6), 'Diffuse Valve B': (0, 7),
    'Microwave Cooling': (1, 8),
}


class ManualControl:
    def __init__(self):
        try:
            import piplates.RELAYplate2 as driver
        except ImportError as exc:
            raise ControlError('HW_IMPORT', 'No se pudo cargar Pi-Plates', repr(exc)) from exc
        except Exception as exc:
            raise ControlError('HW_INIT', 'No se pudo inicializar Pi-Plates', repr(exc)) from exc
        self.driver = driver
        self.lock = SPI_LOCK
        for address in RELAY_ADDRESSES:
            try:
                identity = self.driver.getID(address)
            except Exception as exc:
                raise ControlError('HW_ID', 'No se pudo identificar la placa', repr(exc), address=address) from exc
            if 'RELAYPLATE2' not in str(identity).upper():
                raise ControlError('HW_ID', 'Se esperaba RELAYplate2', repr(identity), address=address)
        self.states()  # Comprobar lectura antes de abrir el GUI; no cambiar salidas.

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
                   'on': bool(masks[wiring[0]] & (1 << (wiring[1] - 1))) if wiring else None}
            for name, wiring in RELAYS.items()}}

    def states(self):
        with self.lock:
            return self._states()

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
