"""Prueba local de módulos: adelanta deadlines solo dentro de esta prueba."""
import sys
from planta import Planta
from manual_control import ManualControl
from temperaturas import Temperaturas
from presiones import Presiones
from masscontroll import MassControl
from emergency_shutdown import EmergencyShutdown
from startup import Startup
from shutdown import Shutdown
p=Planta(); c=ManualControl(p); t=Temperaturas(p); r=Presiones(p)
e=EmergencyShutdown(c,MassControl()); s=Startup(c,t,r,e); d=Shutdown(c,t,r,e,s)
p.configure({'overrides':{'medium_volts':.6505149978,'Diffusion Pump A':135,'Diffusion Pump B':135}})
s.start(background=False)
for _ in range(80):
    if s.deadline is not None: s.deadline=0
    s.tick()
    if s.status=='awaiting_gas': break
assert s.status=='awaiting_gas',s.state()
s.confirm_gas();assert s.status=='complete'
d.start(background=False);d.confirm_gas()
p.configure({'overrides':{'Diffusion Pump A':30,'Diffusion Pump B':30}})
for _ in range(80):
    if d.deadline is not None: d.deadline=0
    d.tick()
    if d.status=='complete':break
assert d.status=='complete',d.state()
assert not any(x['on'] for x in c.states()['relays'].values())
assert not any(x.startswith('piplates') for x in sys.modules)
print('PASS: startup y shutdown locales completos, sin importar drivers Pi-Plates')
