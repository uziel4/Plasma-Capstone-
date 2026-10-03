"""Room (DS18B20, THERMOplate 2 / puerto 9) y alarma High room temperature en la planta simulada."""
from planta import Planta
from manual_control import ManualControl
from temperaturas import Temperaturas
from emergency_shutdown import EmergencyShutdown
from masscontroll import MassControl
from alarma_room import RoomAlarm

plant = Planta()
control = ManualControl(plant)
temps = Temperaturas(plant)
emergency = EmergencyShutdown(control, MassControl())
alarm = RoomAlarm(control, temps, emergency)
buzzer = lambda: control.states()['relays']['Buzzer']['on']

room = temps.read()['temperatures']['Room']
assert room['channel'] == 9 and 21 <= room['celsius'] <= 22, room
alarm.check()
assert not alarm.state()['active'] and not buzzer()
plant.configure({'overrides': {'Room': 29}, 'faults': []})
alarm.check()
assert not alarm.state()['active'] and not buzzer()  # 29 °C exacto no activa
plant.configure({'overrides': {'Room': 30}, 'faults': []})
alarm.check()
assert alarm.state()['active'] and buzzer()
plant.configure({'overrides': {}, 'faults': ['Room']})
alarm.check()
assert alarm.state()['active'] and alarm.state()['error'] and buzzer()  # sin lectura conserva el estado
plant.configure({'overrides': {'Room': 28.5}, 'faults': []})
alarm.check()
assert alarm.state()['active'] and buzzer()  # 28.5 °C: dentro de la banda, sigue activa
plant.configure({'overrides': {'Room': 28}, 'faults': []})
alarm.check()
assert not alarm.state()['active'] and not buzzer()  # 28 °C: se desactiva
plant.configure({'overrides': {'Room': 30}, 'faults': []})
alarm.check()
assert alarm.state()['active'] and buzzer()
plant.configure({'overrides': {}, 'faults': []})
alarm.check()
assert not alarm.state()['active'] and not buzzer()
plant.configure({'overrides': {'Room': 35}, 'faults': []})
emergency.stop('prueba')
alarm.check()
assert alarm.state()['active'] and not buzzer() and 'Buzzer no accionado' in alarm.state()['error']
print('PASS: Room en puerto 9 ronda 21-22 °C; alarma > 29 °C enciende y <= 28 °C apaga el Buzzer; fallo y paro respetados')
