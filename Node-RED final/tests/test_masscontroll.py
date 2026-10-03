"""Pruebas aisladas del driver; no se incluye modo simulado en el producto."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from masscontroll import MassControl, percent_to_volts, leer_flujo
from errores import ControlError

class Driver:
    def __init__(self):
        self.volts = 1.0
        self.writes = []
    def getDAC(self, addr, channel):
        return self.volts
    def setDAC(self, addr, channel, volts):
        self.writes.append((addr, channel, volts))
        self.volts = volts
    def getADC(self, addr, channel):
        return 2.5

class MassTests(unittest.TestCase):
    def test_conversion_limits(self):
        self.assertAlmostEqual(percent_to_volts(81.9), 4.095)
        for invalid in [100, -1, True, None, float('nan'), float('inf')]:
            with self.assertRaises(ControlError): percent_to_volts(invalid)
    def test_state_does_not_write(self):
        m = MassControl(); m.driver = d = Driver()
        self.assertEqual(m.state()['command_percent'], 20)
        self.assertEqual(d.writes, [])
    def test_write_and_zero(self):
        m = MassControl(); m.driver = d = Driver()
        self.assertEqual(m.set_percent(50)['command_volts'], 2.5)
        self.assertEqual(m.set_percent(0)['command_volts'], 0)
        self.assertEqual(d.writes, [(4,0,2.5),(4,0,0)])
    def test_mismatch_is_error(self):
        m = MassControl(); m.driver = d = Driver()
        d.setDAC = lambda *args: None
        with self.assertRaises(ControlError) as ctx: m.set_percent(50)
        self.assertEqual(ctx.exception.code, 'MFC_WRITE')
    def test_read_configured_sccm(self):
        self.assertEqual(leer_flujo(Driver())['percent'],50)
        self.assertEqual(leer_flujo(Driver())['sccm'],2500)
        self.assertIsNotNone(leer_flujo(None)['error'])

    def test_sccm_limits_and_off(self):
        m=MassControl(); m.driver=d=Driver()
        self.assertEqual(m.set_sccm(10)['command_volts'],.01)
        self.assertEqual(m.set_sccm(4095)['command_volts'],4.095)
        self.assertEqual(m.set_sccm(0)['command_volts'],0)
        count=len(d.writes)
        for value in (9,4096,5000,5001,True,None,float('nan')):
            with self.assertRaises(ControlError): m.set_sccm(value)
        self.assertEqual(len(d.writes),count)

if __name__ == '__main__': unittest.main()
