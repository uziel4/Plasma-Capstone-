import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from emergency_shutdown import EmergencyShutdown
from errores import ControlError

class StopTests(unittest.TestCase):
    def make(self, fail=False):
        self.calls=[]
        def off(a,r):
            self.calls.append((a,r))
            if fail and (a,r)==(0,1): raise RuntimeError('fallo')
        def zero(v):
            self.calls.append(('mass',v))
            if fail: raise RuntimeError('sin DAC')
        return EmergencyShutdown(SimpleNamespace(driver=SimpleNamespace(relayOFF=off,relaySTATE=lambda a:0)),SimpleNamespace(set_percent=zero))
    def test_all_off_latched(self):
        e=self.make();result=e.stop('test')
        self.assertTrue(result['result']['confirmed'])
        self.assertEqual(len(self.calls),17)
        self.assertEqual(self.calls[0],('mass',0))
        with self.assertRaises(ControlError): e.command(lambda: self.fail('Reactivacion'))
    def test_failure_continues_and_retry(self):
        e=self.make(True);r=e.stop('test')
        self.assertFalse(r['result']['confirmed'])
        self.assertEqual(len(self.calls),17)
        e.stop('retry');self.assertEqual(len(self.calls),34)

if __name__=='__main__': unittest.main()
