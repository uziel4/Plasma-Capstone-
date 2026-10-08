import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vacio_rough import ROUGH_SENSORES, voltaje_a_porcentaje, leer_rough
from errores import ControlError
import masscontroll


class FakeADC:
    def __init__(self, values):
        self.values, self.calls = values, []

    def getADC(self, address, channel):
        self.calls.append((address, channel))
        value = self.values[channel]
        if isinstance(value, Exception):
            raise value
        return value


class RoughTests(unittest.TestCase):
    def test_channels_s4_s5_and_mass_flow_moved(self):
        self.assertEqual(ROUGH_SENSORES, {'Rough Manifold A': 'S4', 'Rough Manifold B': 'S5'})
        self.assertEqual(masscontroll.ADC_CHANNEL, 'S6')

    def test_percent_scale(self):
        for volts, percent in ((0, 0), (5, 50), (10, 100), (2.5, 25), (-0.03, 0), (10.04, 100)):
            self.assertAlmostEqual(voltaje_a_porcentaje(volts), percent)
        for bad in (-0.2, 10.2, float('nan'), None, True):
            with self.assertRaises(ControlError):
                voltaje_a_porcentaje(bad)

    def test_read(self):
        driver = FakeADC({'S4': 7.5, 'S5': 11.0})
        readings = leer_rough(driver)
        self.assertEqual(readings['Rough Manifold A'], {'volts': 7.5, 'percent': 75.0, 'channel': 'S4', 'error': None})
        b = readings['Rough Manifold B']
        self.assertIsNone(b['percent'])
        self.assertEqual(b['volts'], 11.0)
        self.assertEqual(b['error']['code'], 'ROUGH_RANGE')
        self.assertEqual(driver.calls, [(3, 'S4'), (3, 'S5')])

    def test_read_failures(self):
        readings = leer_rough(FakeADC({'S4': RuntimeError('SPI'), 'S5': 3.0}))
        self.assertEqual(readings['Rough Manifold A']['error']['code'], 'ROUGH_READ')
        self.assertEqual(readings['Rough Manifold B']['percent'], 30.0)
        missing = leer_rough(None, 'sin placa')
        self.assertTrue(all(e['error']['code'] == 'ROUGH_READ' for e in missing.values()))


if __name__ == '__main__':
    unittest.main()
