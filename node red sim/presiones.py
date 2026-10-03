"""Presiones Air/Coolant/Water por ADCplate. Vacio se integrara aparte."""
import logging
import math
import time
from threading import Lock
from hardware_bus import SPI_LOCK
from errores import ControlError
from temperatura_agua import leer_corriente
from vacio import leer_vacios
# from masscontroll import leer_flujo  # Proximamente para grupos futuros.

ADC_ADDRESS = 3
SENSORES = {
    'Air': {'canal': 'I3', 'max_psi': 232.0},
    'Coolant': {'canal': 'I2', 'max_psi': 232.0},
    'Water': {'canal': 'I1', 'max_psi': 232.0},
}


def calcular_psi(current_ma, max_psi):
    if type(current_ma) not in (float, int) or not math.isfinite(current_ma):
        raise ValueError(f'Corriente invalida: {current_ma!r}')
    return max(0.0, (current_ma - 4.0) / 16.0 * max_psi)


from temperatura_agua import calcular_celsius
from vacio import terranova906a_a_torr, gp270_a_torr
class Presiones:
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
            for name, key, channel, default in [('Air','air_ma','I3',4+p.air/232*16),('Coolant','coolant_ma','I2',4+p.coolant_pressure/232*16),('Water','pressure_water_ma','I1',4+p.water_pressure/232*16)]:
                ma = p.value(key,default)
                error = p.error(key)
                if not 4 <= ma <= 20: error = {'code':'PRESS_RANGE','error':'Corriente fuera de 4–20 mA'}
                values[name] = {'ma':ma,'psi':None if p.error(key) else calcular_psi(ma,232),'channel':channel,'error':error}
            vacuum = {}
            for name,key,channel,default,convert in [('Medium Vacuum','medium_volts','S0',(math.log10(p.pressure)+3)/2,terranova906a_a_torr),('High Vacuum','high_volts','S1',p.high_volts(),gp270_a_torr)]:
                volts = p.value(key,default)
                error = p.error(key)
                pressure = None
                try:
                    if not error: pressure = convert(volts)
                except Exception as exc: error = exc.payload()
                vacuum[name] = {'volts':volts,'torr':pressure,'channel':channel,'error':error}
            ma = p.value('water_ma',4+p.water_temp/6.25)
            error = p.error('water_ma')
            celsius = None
            try:
                if not error: celsius = calcular_celsius(ma)
            except Exception as exc: error = exc.payload()
            return {'pressures':values,'vacuum':vacuum,'water_temperature':{'ma':ma,'celsius':celsius,'channel':'I0','error':error},'mass_flow':None,'timestamp':time.time(),'simulation':True}

