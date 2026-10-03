import sys
import time
import unittest
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from manual_control import (ManualControl, INITIAL_MANUAL_ALLOWED, PERMANENT_MANUAL_ALLOWED,
                            TEMPORARY_MANUAL_ALLOWED, MANUAL_PREREQUISITES, STARTUP_PREREQUISITES,
                            CHAMBER_PREREQUISITES, GATE_PREREQUISITES,
                            RELAYS, RELAY_ADDRESSES)
from errores import ControlError

class ManualConditionsTests(unittest.TestCase):
    def packet(self, pressure, age=0, error=None):
        return {'timestamp':time.time()-age, 'vacuum':{'Medium Vacuum':{'torr':pressure,'error':error}}}

    def test_relay_addresses_match_unique_outputs(self):
        self.assertEqual(RELAY_ADDRESSES, (1, 2))
        self.assertEqual(set(RELAYS.values()), {(a,r) for a in (1,2) for r in range(1,9)})
        self.assertEqual(RELAYS['Air Compressor'], (1,1))
        self.assertEqual(RELAYS['Chamber Valve B'], (2,1))
        self.assertEqual(RELAYS['Buzzer'], (2,8))

    def test_temporary_manual_permissions(self):
        self.assertEqual(INITIAL_MANUAL_ALLOWED,
                         set(RELAYS) - {'Diffusion Pump A', 'Diffusion Pump B'})

    def relay_states(self, on=()):
        return {'relays': {name: {'configured': True, 'manual_allowed': name in INITIAL_MANUAL_ALLOWED,
                                  'on': name in on} for name in RELAYS}}

    def test_diffuse_valves_require_startup_prerequisites(self):
        control = ManualControl.__new__(ManualControl)
        control.set_relay = Mock()
        control.manual_states = Mock(return_value={})
        for name in ('Diffuse Valve A', 'Diffuse Valve B'):
            self.assertEqual(MANUAL_PREREQUISITES[name], STARTUP_PREREQUISITES)
            for missing in STARTUP_PREREQUISITES:
                control.states = Mock(return_value=self.relay_states(set(STARTUP_PREREQUISITES) - {missing}))
                with self.assertRaises(ControlError) as error:
                    control.set_manual_relay(name, True)
                self.assertIn(missing, str(error.exception.args) + str(vars(error.exception)))
                control.set_relay.assert_not_called()
                control.set_manual_relay(name, False)  # OFF siempre permitido
                control.set_relay.assert_called_once_with(name, False)
                control.set_relay.reset_mock()
            control.states = Mock(return_value=self.relay_states(STARTUP_PREREQUISITES))
            control.set_manual_relay(name, True)
            control.set_relay.assert_called_once_with(name, True)
            control.set_relay.reset_mock()

    def test_chamber_valves_require_startup_prerequisites(self):
        self.assertEqual(CHAMBER_PREREQUISITES, STARTUP_PREREQUISITES + ('Diffuse Valve A', 'Diffuse Valve B'))
        control = ManualControl.__new__(ManualControl)
        control.set_relay = Mock()
        control.manual_states = Mock(return_value={})
        for name in ('Chamber Valve A', 'Chamber Valve B'):
            self.assertEqual(MANUAL_PREREQUISITES[name], CHAMBER_PREREQUISITES)
            for missing in CHAMBER_PREREQUISITES:
                control.states = Mock(return_value=self.relay_states(set(CHAMBER_PREREQUISITES) - {missing}))
                with self.assertRaises(ControlError) as error:
                    control.set_manual_relay(name, True)
                self.assertIn(missing, error.exception.message)
                control.set_relay.assert_not_called()
                control.set_manual_relay(name, False)  # OFF siempre permitido
                control.set_relay.assert_called_once_with(name, False)
                control.set_relay.reset_mock()
            control.states = Mock(return_value=self.relay_states(CHAMBER_PREREQUISITES))
            control.set_manual_relay(name, True)
            control.set_relay.assert_called_once_with(name, True)
            control.set_relay.reset_mock()
        control.manual_states = ManualControl.manual_states.__get__(control)
        control.states = Mock(return_value=self.relay_states(STARTUP_PREREQUISITES))
        relays = control.manual_states()['relays']
        self.assertFalse(relays['Chamber Valve A']['manual_allowed'])
        self.assertIn('Diffuse Valve A, Diffuse Valve B', relays['Chamber Valve A']['manual_reason'])

    def temps(self, a=135.0, b=135.0, age=0, error=None):
        return {'timestamp': time.time()-age, 'temperatures': {
            'Diffusion Pump A': {'celsius': a, 'error': error}, 'Diffusion Pump B': {'celsius': b, 'error': None}}}

    def gate_control(self, on=GATE_PREREQUISITES):
        control = ManualControl.__new__(ManualControl)
        control.set_relay = Mock()
        control.manual_states = Mock(return_value={})
        control.states = Mock(return_value=self.relay_states(set(on)))
        return control

    def test_gate_valves_follow_startup_steps(self):
        self.assertEqual(GATE_PREREQUISITES, CHAMBER_PREREQUISITES + (
            'Mechanical Pump A', 'Mechanical Pump B', 'Diffusion Pump A', 'Diffusion Pump B'))
        ok_vacuum, ok_temps = (lambda: self.packet(.010)), (lambda: self.temps())
        for name in ('Gate Valve A', 'Gate Valve B'):
            self.assertEqual(MANUAL_PREREQUISITES[name], GATE_PREREQUISITES)
            control = self.gate_control()
            control.set_manual_relay(name, True, ok_vacuum, ok_temps)
            control.set_relay.assert_called_once_with(name, True)
            blocked = [(set(GATE_PREREQUISITES) - {m}, ok_vacuum, ok_temps, m) for m in GATE_PREREQUISITES]
            blocked += [(set(GATE_PREREQUISITES) | {c}, ok_vacuum, ok_temps, 'apagar ' + c) for c in ('Chamber Valve A', 'Chamber Valve B')]
            blocked += [(GATE_PREREQUISITES, lambda v=v: self.packet(v), ok_temps, 'Medium') for v in (.0009, .031, None)]
            blocked += [(GATE_PREREQUISITES, lambda: self.packet(.010, age=4), ok_temps, 'Medium'),
                        (GATE_PREREQUISITES, lambda: self.packet(.010, error={'code': 'VAC'}), ok_temps, 'Medium'),
                        (GATE_PREREQUISITES, None, ok_temps, 'Medium'),
                        (GATE_PREREQUISITES, ok_vacuum, None, '250 y 300'),
                        (GATE_PREREQUISITES, ok_vacuum, lambda: self.temps(age=4), '250 y 300'),
                        (GATE_PREREQUISITES, ok_vacuum, lambda: self.temps(error={'code': 'TEMP'}), '250 y 300')]
            blocked += [(GATE_PREREQUISITES, ok_vacuum, lambda a=a, b=b: self.temps(a, b), '250 y 300')
                        for a, b in ((121.0, 135.0), (135.0, 149.0), (135.0, None))]
            for relays, vacuum, temps, reason in blocked:
                control = self.gate_control(relays)
                with self.assertRaises(ControlError) as error:
                    control.set_manual_relay(name, True, vacuum, temps)
                self.assertIn(reason, error.exception.message)
                control.set_relay.assert_not_called()
                control.set_manual_relay(name, False)  # OFF siempre permitido
                control.set_relay.assert_called_once_with(name, False)
            for limit in (.001, .030):
                control = self.gate_control()
                control.set_manual_relay(name, True, lambda: self.packet(limit), lambda: self.temps(121.12, 148.88))
                control.set_relay.assert_called_once_with(name, True)

    def test_gate_valves_reported_state(self):
        control = self.gate_control(set(GATE_PREREQUISITES) | {'Chamber Valve A'})
        control.manual_states = ManualControl.manual_states.__get__(control)
        relays = control.manual_states(self.packet(.5), self.temps(30, 30))['relays']
        reason = relays['Gate Valve A']['manual_reason']
        self.assertFalse(relays['Gate Valve A']['manual_allowed'])
        for text in ('apagar Chamber Valve A', 'Medium', '250 y 300'):
            self.assertIn(text, reason)
        control.states = Mock(return_value=self.relay_states(GATE_PREREQUISITES))
        self.assertTrue(control.manual_states(self.packet(.010), self.temps())['relays']['Gate Valve B']['manual_allowed'])

    def test_diffuse_valves_reported_state(self):
        control = ManualControl.__new__(ManualControl)
        control.states = Mock(return_value=self.relay_states({'Air Compressor', 'Water Chiller'}))
        relays = control.manual_states()['relays']
        for name in ('Diffuse Valve A', 'Diffuse Valve B'):
            self.assertFalse(relays[name]['manual_allowed'])
            self.assertIn('Booster Pump', relays[name]['manual_reason'])
            self.assertIn('Cool Trap B', relays[name]['manual_reason'])
        control.states = Mock(return_value=self.relay_states(set(STARTUP_PREREQUISITES)))
        relays = control.manual_states()['relays']
        self.assertTrue(relays['Diffuse Valve A']['manual_allowed'])
        control.states = Mock(return_value=self.relay_states({'Diffuse Valve B'}))
        self.assertTrue(control.manual_states()['relays']['Diffuse Valve B']['manual_allowed'])  # para poder apagarla

    def test_booster_pump_permanently_allowed(self):
        self.assertIn('Booster Pump', PERMANENT_MANUAL_ALLOWED)
        self.assertNotIn('Booster Pump', TEMPORARY_MANUAL_ALLOWED)

    def test_threshold_and_bad_readings(self):
        self.assertTrue(ManualControl.diffusion_ready(self.packet(.029)))
        for value in [.030, .031, 0, -1, None, True, float('nan')]:
            self.assertFalse(ManualControl.diffusion_ready(self.packet(value)))
        self.assertFalse(ManualControl.diffusion_ready(self.packet(.02, age=4)))
        self.assertFalse(ManualControl.diffusion_ready(self.packet(.02, error={'code':'VAC_READ'})))

    def test_block_on_but_allow_off(self):
        control = ManualControl.__new__(ManualControl)
        control.set_relay = Mock()
        control.manual_states = Mock(return_value={})
        for name in ('Diffusion Pump A','Diffusion Pump B'):
            with self.assertRaises(ControlError):
                control.set_manual_relay(name, True, lambda:self.packet(.030))
            control.set_relay.assert_not_called()
            control.set_manual_relay(name, False)
            control.set_relay.assert_called_once_with(name,False)
            control.set_relay.reset_mock()
            control.set_manual_relay(name, True, lambda:self.packet(.029))
            control.set_relay.assert_called_once_with(name,True)
            control.set_relay.reset_mock()
