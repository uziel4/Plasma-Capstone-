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
# Room (lab temp): DS18B20 digital en el puerto 9 del mismo THERMOplate (address 2).
# Se lee con getTEMP como las termocuplas; no lleva setTYPE (solo canales 1-8).
ROOM_SENSOR = ('Room', 9)
ROOM_LIMITS_C = (-55, 125)  # Rango de medicion del DS18B20, no limites del laboratorio


class Temperaturas:
    def __init__(self, plant=None):
        if plant is None:
            from planta import Planta
            plant = Planta()
        self.plant = plant
    def read(self):
        p = self.plant
        with p.lock:
            p.advance()
            values = {}
            for name, (channel, kind) in TERMOCUPLAS.items():
                value = p.value(name, p.temps[name])
                error = p.error(name)
                if not -200 <= value <= 1372:
                    error = {'code':'TEMP_RANGE','error':'Temperatura simulada fuera de rango K'}
                values[name] = {'celsius': None if error else value, 'channel':channel, 'error':error}
            name, channel = ROOM_SENSOR
            value = p.value(name, p.room)
            error = p.error(name)
            if not error and not ROOM_LIMITS_C[0] <= value <= ROOM_LIMITS_C[1]:
                error = {'code':'TEMP_RANGE','error':'Temperatura simulada fuera de rango DS18B20'}
            values[name] = {'celsius': None if error else value, 'channel':channel, 'error':error}
            return {'temperatures':values, 'timestamp':time.time(), 'simulation':True}

