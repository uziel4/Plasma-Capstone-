"""Recorrido dinámico sin esperas físicas: avanza solo reloj de la planta."""
from planta import Planta
from manual_control import ManualControl
from presiones import Presiones
from vacio import gp270_a_torr
p=Planta(); c=ManualControl(p)
def advance(seconds):
    for _ in range(seconds):
        p.updated-=1
        p.advance()
assert p.pressure==760
for n in ('Water Chiller','Air Compressor','Cool Trap A','Cool Trap B','Mechanical Pump A','Mechanical Pump B','Diffuse Valve A','Diffuse Valve B','Chamber Valve A','Chamber Valve B'):
    c.set_relay(n,True)
advance(100)
assert .001 < p.pressure < .030
assert p.temps['Cool Trap A']<10 and p.water_temp<20 and p.air>100
for n in ('Diffusion Pump A','Diffusion Pump B'):c.set_relay(n,True)
advance(50)
assert all(121.11 < p.temps[n]<148.89 for n in ('Diffusion Pump A','Diffusion Pump B'))
for n in ('Chamber Valve A','Chamber Valve B'):c.set_relay(n,False)
for n in ('Gate Valve A','Gate Valve B'):c.set_relay(n,True)
advance(100)
assert abs(gp270_a_torr(p.high_volts())-p.pressure)<1e-12
assert Presiones(p).read()['vacuum']['High Vacuum']['error'] is None
p.configure({'gas_open':True});advance(100);assert p.pressure>1e-5
p.configure({'faults':['leak']});advance(100);assert p.pressure>1
p.configure({'faults':['medium_volts']});assert Presiones(p).read()['vacuum']['Medium Vacuum']['torr'] is None
for n in ('Diffusion Pump A','Diffusion Pump B'):c.set_relay(n,False)
advance(50);assert p.temps['Diffusion Pump A']<37.777
print('PASS: bombeo, rutas de valvulas, High dinamico, temperaturas, gas, fuga y fallo de sensor')
