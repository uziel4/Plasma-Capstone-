import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vacio import terranova906a_a_torr, leer_vacios, gp270_a_torr
from errores import ControlError

class VacuumTests(unittest.TestCase):
    def test_manual_examples(self):
        for volts, torr in [(.5,.01),(1,.1),(1.5,1),(2,10),(2.5,100)]:
            self.assertAlmostEqual(terranova906a_a_torr(volts),torr)

    def test_invalid_or_status(self):
        for volts in [None, True, float('nan'), float('inf'), -1, 0, 3, 4]:
            with self.assertRaises(ControlError): terranova906a_a_torr(volts)

    def test_both_channels_read_every_cycle_regardless_of_pressure(self):
        class ADC:
            def __init__(self): self.calls = []; self.medium = 1.0
            def getADC(self, address, channel):
                self.calls.append((address, channel))
                return self.medium if channel == 'S0' else -2.5
        adc = ADC()
        for medium in [1.0, .5, 0.0]:
            adc.medium = medium
            values = leer_vacios(adc)
            self.assertAlmostEqual(values['High Vacuum']['torr'], 5e-6)
            self.assertEqual(values['High Vacuum']['volts'], -2.5)
            self.assertEqual(adc.calls[-2:], [(3, 'S0'), (3, 'S1')])

    def test_adc_route_and_channel_isolation(self):
        class ADC:
            def getADC(self, address, channel):
                assert address == 3
                return 1 if channel == 'S0' else -10
        values=leer_vacios(ADC())
        self.assertAlmostEqual(values['Medium Vacuum']['torr'],.1)
        self.assertIsNone(values['High Vacuum']['torr'])
        self.assertEqual(values['High Vacuum']['error']['code'],'VAC_GP270_STATE')
        self.assertAlmostEqual(gp270_a_torr(-2.5),5e-6)

if __name__ == '__main__': unittest.main()
