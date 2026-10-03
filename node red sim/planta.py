"""Modelo didáctico de planta. Sin acceso a hardware."""
import math
import time
from threading import RLock
from manual_control import RELAYS
from temperaturas import TERMOCUPLAS, ROOM_SENSOR

class Planta:
    def __init__(self):
        self.lock = RLock()
        self.masks = {1: 0, 2: 0}
        self.updated = time.monotonic()
        self.pressure = 760.0
        self.temps = {name: 24.0 for name in TERMOCUPLAS}
        self.air = 0.0
        self.coolant_pressure = 0.0
        self.water_pressure = 0.0
        self.water_temp = 24.0
        self.room = 21.5  # Laboratorio: ronda 21-22 °C
        self.gas_open = False
        self.coils_on = False
        self.overrides = {}
        self.faults = set()

    def on(self, name):
        address, relay = RELAYS[name]
        return bool(self.masks[address] & (1 << (relay-1)))

    def advance(self):
        with self.lock:
            now = time.monotonic()
            dt = min(now-self.updated, 5)
            self.updated = now
            pumping = all(self.on(n) for n in ('Mechanical Pump A', 'Mechanical Pump B', 'Diffuse Valve A', 'Diffuse Valve B'))
            rough_path = self.on('Chamber Valve A') and self.on('Chamber Valve B')
            high_path = all(self.on(n) for n in ('Gate Valve A', 'Gate Valve B', 'Diffusion Pump A', 'Diffusion Pump B')) and all(self.temps[n] >= 121.11 for n in ('Diffusion Pump A', 'Diffusion Pump B'))
            target = (2e-5 if self.gas_open else 5e-7) if pumping and high_path else .01 if pumping and rough_path else self.pressure
            if 'leak' in self.faults: target = 10.0
            self.pressure = math.exp(math.log(target)+(math.log(self.pressure)-math.log(target))*math.exp(-dt/8))
            self.air += ((120 if self.on('Air Compressor') else 0)-self.air)*(1-math.exp(-dt/5))
            chiller = self.on('Water Chiller')
            self.coolant_pressure += ((58 if chiller else 0)-self.coolant_pressure)*(1-math.exp(-dt/5))
            self.water_pressure += ((45 if chiller else 0)-self.water_pressure)*(1-math.exp(-dt/5))
            self.water_temp += ((18 if chiller else 24)-self.water_temp)*(1-math.exp(-dt/10))
            self.room = 21.5 + 0.5*math.sin(time.time()/120)
            for name in self.temps:
                if name.startswith('Diffusion Pump'):
                    target = 135 if self.on(name) else 24
                elif name.startswith('Cool Trap'):
                    target = 8 if self.on(name) and chiller else 24
                elif name == 'Coolant':
                    target = 10 if chiller else 24
                else:
                    target = 65 if self.coils_on else 24
                self.temps[name] += (target-self.temps[name])*(1-math.exp(-dt/8))

    def high_volts(self):
        # Inversa de la transferencia nominal local, solo dentro de rango.
        pressure = self.pressure
        if not 3e-9 <= pressure <= 1e-3:
            return -11.0  # Estado no utilizable; nunca inventar presión high.
        for n in range(5):
            scale = 10.0 ** (n - 7)
            if pressure <= scale:
                return -(n + pressure / scale)
        return -5.0

    def value(self, name, default):
        return self.overrides.get(name, default)

    def error(self, name):
        return {'code': 'SIM_SENSOR', 'error': 'Fallo simulado: '+name} if name in self.faults else None

    def configure(self, data):
        allowed = {'medium_volts', 'high_volts', 'water_ma', 'air_ma', 'coolant_ma', 'pressure_water_ma', *TERMOCUPLAS, ROOM_SENSOR[0]}
        if not isinstance(data, dict) or set(data)-{'overrides', 'faults', 'gas_open', 'coils_on'}:
            raise ValueError('Use overrides y faults')
        overrides = data.get('overrides', {})
        faults = data.get('faults', [])
        if not isinstance(overrides, dict) or set(overrides)-allowed or any(type(v) not in (int,float) or not math.isfinite(v) for v in overrides.values()):
            raise ValueError('Overrides invalidos')
        if not isinstance(faults,list) or any(not isinstance(x,str) or x not in allowed|{'relays', 'leak'} for x in faults):
            raise ValueError('Faults invalidos')
        for key in ('gas_open','coils_on'):
            if key in data and type(data[key]) is not bool: raise ValueError(key+' debe ser booleano')
        with self.lock:
            self.gas_open = data.get('gas_open', self.gas_open)
            self.coils_on = data.get('coils_on', self.coils_on)
            self.overrides = dict(overrides)
            self.faults = set(faults)
        return {'simulation': True, 'overrides': overrides, 'faults': faults}

    def relaySTATE(self, address):
        with self.lock:
            if 'relays' in self.faults:
                raise RuntimeError('Fallo simulado de placa')
            return self.masks[address]

    def relayON(self, address, relay):
        with self.lock:
            if 'relays' in self.faults:
                raise RuntimeError('Fallo simulado de placa')
            self.masks[address] |= 1 << (relay-1)

    def relayOFF(self, address, relay):
        with self.lock:
            if 'relays' in self.faults:
                raise RuntimeError('Fallo simulado de placa')
            self.masks[address] &= ~(1 << (relay-1))

