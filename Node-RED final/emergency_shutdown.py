"""Paro de software enclavado; no sustituye un paro fisico independiente."""
import logging
from threading import RLock
from hardware_bus import SPI_LOCK
from manual_control import RELAYS
from errores import ControlError


class EmergencyShutdown:
    def __init__(self, control, mass):
        self.control, self.mass = control, mass
        self.lock = RLock()
        self.active = False
        self.result = None

    def command(self, action):
        # Serializa ordenes con el paro: ninguna orden pendiente puede reactivar.
        with self.lock:
            if self.active:
                raise ControlError('STOP_LATCHED', 'Paro activado; mandos bloqueados')
            return action()

    def state(self):
        with self.lock:
            return {'active': self.active, 'result': self.result}

    def stop(self, reason):
        with self.lock:
            self.active = True
            errors = {}
            try:
                self.mass.set_percent(0)
            except Exception as exc:
                errors['mass_flow'] = str(exc)
            # Intentar cada salida aunque una placa o confirmacion falle.
            for name, (address, relay) in RELAYS.items():
                try:
                    with SPI_LOCK:
                        self.control.driver.relayOFF(address, relay)
                except Exception as exc:
                    errors[name] = str(exc)
            for address in sorted({v[0] for v in RELAYS.values()}):
                try:
                    with SPI_LOCK:
                        state = self.control.driver.relaySTATE(address)
                    if type(state) is not int or state != 0:
                        raise RuntimeError(f'Mascara OFF no confirmada: {state!r}')
                except Exception as exc:
                    errors[f'placa_{address}'] = str(exc)
            self.result = {'reason': reason, 'confirmed': not errors, 'errors': errors}
            logging.log(logging.ERROR if errors else logging.WARNING, 'Paro: %s', self.result)
            return self.state()
