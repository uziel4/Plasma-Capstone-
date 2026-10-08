import sys
import unittest
from pathlib import Path
from threading import RLock
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from manual_control import ManualControl, INITIAL_MANUAL_ALLOWED, RELAYS, RELAY_ADDRESSES


class FakeBoard:
    def __init__(self):
        self.masks = {a: 0 for a in RELAY_ADDRESSES}
    def relaySTATE(self, address):
        return self.masks[address]
    def relayON(self, address, relay):
        self.masks[address] |= 1 << (relay - 1)
    def relayOFF(self, address, relay):
        self.masks[address] &= ~(1 << (relay - 1))


class NoBlockTests(unittest.TestCase):
    def control(self):
        control = ManualControl.__new__(ManualControl)
        control.driver, control.lock = FakeBoard(), RLock()
        return control

    def test_relay_addresses_match_unique_outputs(self):
        self.assertEqual(set(RELAYS.values()), {(a, r) for a in (0, 1) for r in range(1, 9)})

    def test_board_addresses(self):
        from manual_control import THERMO_ADDRESS, ADC_ADDRESS
        from masscontroll import DAC_ADDRESS
        self.assertEqual((RELAY_ADDRESSES, THERMO_ADDRESS, ADC_ADDRESS, DAC_ADDRESS), ((0, 1), 2, 3, 4))

    def test_all_relays_allowed(self):
        self.assertEqual(INITIAL_MANUAL_ALLOWED, set(RELAYS))
        states = self.control().manual_states()['relays']
        self.assertTrue(all(s['manual_allowed'] for s in states.values()))

    def test_any_relay_turns_on_without_prerequisites(self):
        control = self.control()
        read = Mock(return_value=None)
        for name in RELAYS:
            result = control.set_manual_relay(name, True, read, read)
            self.assertTrue(result['relays'][name]['on'])
        for name in RELAYS:
            self.assertFalse(control.set_manual_relay(name, False)['relays'][name]['on'])


if __name__ == '__main__':
    unittest.main()
