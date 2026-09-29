"""Configuracion y lectura de termocuplas. Canales fisicos THERMOplate 1-8."""
import logging
import math
import time
from threading import Lock
from errores import ControlError
from hardware_bus import SPI_LOCK

THERMO_ADDRESS = 2
LINE_FREQUENCY = 60
# Equipo: (canal, tipo). Cablear segun CONFIGURACION.md.
TERMOCUPLAS = {
    'Coolant': (1, 'k'),
    'Cool Trap A': (2, 'k'),
    'Cool Trap B': (3, 'k'),
    'Diffusion Pump A': (4, 'k'),
    'Diffusion Pump B': (5, 'k'),
    'Field Magnet A': (6, 'k'),
    'Field Magnet B': (7, 'k'),
}
# Room: sensor independiente pendiente. No asignar a THERMOplate ni usar
# la temperatura de union fria como temperatura de la habitacion.
# ROOM_SENSOR = ...


class Temperaturas:
    def __init__(self):
        self.driver = None
        self.lock = Lock()
        self.next_init = 0
        self.init_error = None
        self.cache = None
        self.next_read = 0
        self.errors = {}

    def _initialize(self):
        try:
            with SPI_LOCK:
                try:
                    import piplates.THERMOplate as driver
                except ImportError as exc:
                    raise ControlError('TEMP_IMPORT', 'No se pudo cargar THERMOplate', repr(exc), address=THERMO_ADDRESS) from exc
                try:
                    identity = driver.getID(THERMO_ADDRESS)
                    if 'THERMOPLATE' not in str(identity).upper():
                        raise RuntimeError(f'Identificacion recibida: {identity!r}')
                except Exception as exc:
                    raise ControlError('TEMP_ID', 'Fallo de identificacion de THERMOplate', repr(exc), address=THERMO_ADDRESS) from exc
                try:
                    channels = [channel for channel, kind in TERMOCUPLAS.values()]
                    if len(set(channels)) != len(channels) or any(type(c) is not int or not 1 <= c <= 8 for c in channels):
                        raise ValueError('Canales invalidos o repetidos')
                    if any(kind not in ('k', 'j') for channel, kind in TERMOCUPLAS.values()):
                        raise ValueError('Tipo de termocupla invalido; usar k o j')
                    driver.setLINEFREQ(THERMO_ADDRESS, LINE_FREQUENCY)
                    for name, (channel, kind) in TERMOCUPLAS.items():
                        try:
                            driver.setTYPE(THERMO_ADDRESS, channel, kind)
                        except Exception as exc:
                            raise ControlError('TEMP_CONFIG', 'No se pudo configurar el canal', repr(exc), equipo=name, address=THERMO_ADDRESS, canal=channel, tipo=kind) from exc
                except ControlError:
                    raise
                except Exception as exc:
                    raise ControlError('TEMP_CONFIG', 'Configuracion de termocuplas invalida o rechazada', repr(exc), address=THERMO_ADDRESS) from exc
            self.driver = driver
            self.init_error = None
        except Exception as exc:
            self.init_error = exc if isinstance(exc, ControlError) else ControlError('TEMP_INIT', 'No se pudo configurar THERMOplate', repr(exc), address=THERMO_ADDRESS)
            self.next_init = time.monotonic() + 5

    def read(self):
        with self.lock:
            if self.cache is not None and time.monotonic() < self.next_read:
                return self.cache
            if self.driver is None and time.monotonic() >= self.next_init:
                self._initialize()
            values = {}
            for name, (channel, kind) in TERMOCUPLAS.items():
                context = dict(equipo=name, address=THERMO_ADDRESS, canal=channel, tipo=kind.upper())
                try:
                    if self.driver is None:
                        raise self.init_error
                    try:
                        with SPI_LOCK:
                            value = self.driver.getTEMP(THERMO_ADDRESS, channel, 'c')
                    except Exception as exc:
                        raise ControlError('TEMP_READ', 'Fallo al leer termocupla', repr(exc), **context) from exc
                    if type(value) not in (int, float) or not math.isfinite(value):
                        raise ControlError('TEMP_VALUE', 'Temperatura no numerica o no finita', repr(value), **context)
                    # Limites de plausibilidad de conversion, no limites operativos del equipo.
                    lower, upper = (-200, 1372) if kind == 'k' else (-210, 1200)
                    if not lower <= value <= upper:
                        raise ControlError('TEMP_RANGE', 'Temperatura fuera del rango de conversion', repr(value), minimo_c=lower, maximo_c=upper, **context)
                    values[name] = {'celsius': value, 'error': None, 'channel': channel}
                    if name in self.errors:
                        logging.info('Temperatura recuperada: %s, canal %s', name, channel)
                        del self.errors[name]
                except ControlError as exc:
                    values[name] = {'celsius': None, 'error': exc.payload(), 'channel': channel}
                    if self.errors.get(name) != str(exc):
                        logging.error('%s', exc)
                        self.errors[name] = str(exc)
            self.cache = {'temperatures': values, 'timestamp': time.time()}
            self.next_read = time.monotonic() + 1
            return self.cache
