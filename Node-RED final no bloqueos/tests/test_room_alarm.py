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

    def test_silence_stops_buzzer_until_next_episode(self):
        ok = lambda c: {'celsius': c, 'error': None, 'channel': 9}
        alarm, control = self.alarm([ok(30), ok(31), ok(28.5), ok(28.0), ok(29.5)])
        alarm.check()
        control.set_relay.assert_called_once_with('Buzzer', True)
        state = alarm.silence()
        control.set_relay.assert_called_with('Buzzer', False)
        self.assertEqual((state['active'], state['silenced'], state['buzzer']), (True, True, False))
        alarm.check(); alarm.check()  # 31 y 28.5 °C: sigue activa, apagada; no vuelve a sonar
        self.assertEqual(control.set_relay.call_count, 2)
        self.assertTrue(alarm.state()['silenced'])
        alarm.check()  # 28.0 °C: se normaliza sin otra orden (el Buzzer ya esta OFF)
        self.assertEqual(control.set_relay.call_count, 2)
        self.assertEqual((alarm.state()['active'], alarm.state()['silenced']), (False, False))
        alarm.check()  # 29.5 °C: episodio nuevo, vuelve a sonar
        control.set_relay.assert_called_with('Buzzer', True)
        self.assertEqual((alarm.state()['active'], alarm.state()['silenced']), (True, False))

    def test_silence_without_alarm_does_nothing(self):
        alarm, control = self.alarm([{'celsius': 22, 'error': None}])
        alarm.check()
        self.assertFalse(alarm.silence()['silenced'])
        control.set_relay.assert_not_called()

    def test_silence_with_emergency_active(self):
        alarm, control = self.alarm([{'celsius': 30, 'error': None}])
        alarm.check()
        alarm.emergency.active = True  # El paro ya dejo los reles en OFF
        state = alarm.silence()
        self.assertEqual((state['silenced'], state['buzzer']), (True, False))
        control.set_relay.assert_called_once_with('Buzzer', True)

    def test_silence_failure_keeps_alarm_ringing(self):
        alarm, control = self.alarm([{'celsius': 30, 'error': None}])
        alarm.check()
        control.set_relay.side_effect = ControlError('HW_WRITE', 'Error al enviar la orden')
        with self.assertRaises(ControlError):
            alarm.silence()
        self.assertEqual((alarm.state()['silenced'], alarm.state()['buzzer']), (False, True))

    def test_silence_route(self):
        import http.client
        import json
        import threading
        from http.server import ThreadingHTTPServer
        from main import handler_for
        alarm, control = self.alarm([{'celsius': 30, 'error': None}])
        alarm.check()
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(control, Mock(), Mock(), Mock(), alarm.emergency, alarm))
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()

        def post(body):
            client = http.client.HTTPConnection(*server.server_address)
            client.request('POST', '/api/room-alarm/silence', body=json.dumps(body), headers={'Content-Type': 'application/json'})
            response = client.getresponse()
            result = (response.status, json.loads(response.read()))
            client.close()
            return result
        try:
            self.assertEqual(post({'x': 1})[0], 400)
            status, state = post({})
            self.assertEqual(status, 200)
            self.assertEqual((state['active'], state['silenced']), (True, True))
            control.set_relay.assert_called_with('Buzzer', False)
        finally:
            server.shutdown(); server.server_close(); worker.join()


if __name__ == '__main__':
    unittest.main()
