import sys
import time
import unittest
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from temperaturas import Temperaturas, ROOM_SENSOR, TERMOCUPLAS
from alarma_room import RoomAlarm, ROOM_ALARM_C, ROOM_CLEAR_C
from errores import ControlError


class FakeThermo:
    def __init__(self, room=21.5):
        self.room, self.calls = room, []

    def getTEMP(self, address, channel, scale):
        self.calls.append((address, channel, scale))
        return self.room if channel == 9 else 24.0


class FakeEmergency:
    active = False

    def command(self, action):
        if self.active:
            raise ControlError('STOP_LATCHED', 'Paro activado; mandos bloqueados')
        return action()


class RoomAlarmTests(unittest.TestCase):
    def test_room_reads_thermoplate_address_2_port_9(self):
        self.assertEqual(ROOM_SENSOR, ('Room', 9))
        self.assertNotIn(9, [channel for channel, kind in TERMOCUPLAS.values()])
        temps = Temperaturas()
        temps.driver = FakeThermo(21.75)
        room = temps.read()['temperatures']['Room']
        self.assertEqual(room, {'celsius': 21.75, 'error': None, 'channel': 9})
        self.assertIn((2, 9, 'c'), temps.driver.calls)

    def test_room_out_of_ds18b20_range_is_error(self):
        temps = Temperaturas()
        temps.driver = FakeThermo(130)
        room = temps.read()['temperatures']['Room']
        self.assertIsNone(room['celsius'])
        self.assertEqual(room['error']['code'], 'TEMP_RANGE')

    def alarm(self, readings):
        values = iter(readings)
        temps = Mock()
        temps.read = lambda: {'temperatures': {'Room': next(values)}, 'timestamp': time.time()}
        control = Mock()
        return RoomAlarm(control, temps, FakeEmergency()), control

    def test_buzzer_above_29_until_28(self):
        self.assertEqual((ROOM_ALARM_C, ROOM_CLEAR_C), (29, 28))
        ok = lambda c: {'celsius': c, 'error': None, 'channel': 9}
        alarm, control = self.alarm([ok(21.5), ok(29.0), ok(29.1), ok(31), ok(28.9), ok(28.1), ok(28.0)])
        alarm.check(); alarm.check()
        control.set_relay.assert_not_called()
        self.assertFalse(alarm.state()['active'])
        alarm.check()
        control.set_relay.assert_called_once_with('Buzzer', True)
        self.assertTrue(alarm.state()['active'])
        self.assertEqual(alarm.state()['name'], 'High room temperature')
        alarm.check()  # Sigue alta: no repite la orden
        alarm.check(); alarm.check()  # 28.9 y 28.1 °C: dentro de la banda, sigue activa
        control.set_relay.assert_called_once()
        self.assertTrue(alarm.state()['active'])
        alarm.check()  # 28.0 °C: se desactiva
        control.set_relay.assert_called_with('Buzzer', False)
        self.assertFalse(alarm.state()['active'])

    def test_band_does_not_activate_from_normal(self):
        ok = lambda c: {'celsius': c, 'error': None, 'channel': 9}
        alarm, control = self.alarm([ok(28.5), ok(29.0)])
        alarm.check(); alarm.check()
        self.assertFalse(alarm.state()['active'])
        control.set_relay.assert_not_called()

    def test_invalid_reading_keeps_state(self):
        alarm, control = self.alarm([{'celsius': 30, 'error': None}, {'celsius': None, 'error': {'error': 'Fallo DS18B20'}}])
        alarm.check(); alarm.check()
        self.assertTrue(alarm.state()['active'])
        self.assertEqual(alarm.state()['error'], 'Fallo DS18B20')
        control.set_relay.assert_called_once_with('Buzzer', True)

    def test_emergency_blocks_buzzer_but_keeps_alarm(self):
        alarm, control = self.alarm([{'celsius': 35, 'error': None}])
        alarm.emergency.active = True
        alarm.check()
        control.set_relay.assert_not_called()
        self.assertTrue(alarm.state()['active'])
        self.assertIn('Buzzer no accionado', alarm.state()['error'])


if __name__ == '__main__':
    unittest.main()
