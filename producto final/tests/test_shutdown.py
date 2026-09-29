import unittest
import time
from unittest.mock import patch
from test_startup import Control, Emergency, Reader
from startup import Startup
from shutdown import Shutdown, STEPS
from errores import ControlError

class ShutdownTests(unittest.TestCase):
    def setUp(self):
        self.c=Control(); self.e=Emergency()
        self.t=Reader({'timestamp':time.time(),'temperatures':{n:{'celsius':30,'error':None} for n in ('Diffusion Pump A','Diffusion Pump B')}})
        self.up=Startup(self.c,self.t,Reader({}),self.e)
        self.s=Shutdown(self.c,self.t,Reader({}),self.e,self.up)
    def test_manual_first_delay_and_order(self):
        self.s.start(background=False); self.s.tick()
        self.assertEqual(self.c.orders,[])
        with self.assertRaises(ControlError): self.s.manual(lambda: None)
        with patch('shutdown.time.monotonic',return_value=0): self.s.confirm_gas()
        with patch('shutdown.time.monotonic',return_value=119): self.s.tick(); self.assertEqual(self.c.orders,[])
        with patch('shutdown.time.monotonic',return_value=120):
            while self.s.status=='running': self.s.tick()
        self.assertEqual(self.c.orders,[(n,v) for k,n,v in STEPS if k=='relay'])
        self.assertEqual(self.s.state()['status'],'complete')
        self.assertFalse(self.s.state()['manual_locked'])
    def test_both_cool_and_current(self):
        self.s.start(background=False); self.s.confirm_gas()
        self.s.index=next(i for i,x in enumerate(STEPS) if x[0]=='temperature'); idx=self.s.index
        b=self.t.data['temperatures']['Diffusion Pump B']
        for value in [38,100,None,True,float('nan')]:
            b['celsius']=value; self.s.tick(); self.assertEqual(self.s.index,idx)
        b['celsius']=(100-32)*5/9; self.t.data['timestamp']=0
        self.s.tick(); self.assertEqual(self.s.index,idx)
        self.t.data['timestamp']=time.time(); self.s.tick(); self.assertEqual(self.s.index,idx+1)
    def test_emergency_and_uncertain_command(self):
        self.s.start(background=False); self.e.active=True
        with self.assertRaises(ControlError): self.s.confirm_gas()
        self.s.tick(); self.assertEqual(self.s.state()['status'],'stopped')
        self.assertEqual(self.c.orders,[])
    def test_interlock_startup_and_duplicates(self):
        self.up.start(background=False)
        with self.assertRaises(ControlError): self.s.start(background=False)
        self.up.status='complete'; self.s.start(background=False)
        with self.assertRaises(ControlError): self.s.start(background=False)
        with self.assertRaises(ControlError): self.s.manual(lambda:self.up.start(background=False))
        self.s.confirm_gas()
        with self.assertRaises(ControlError): self.s.confirm_gas()
    def test_no_retry_relay_failure(self):
        self.s.start(background=False); self.s.confirm_gas(); self.s.index=2
        self.c.fail=True; self.s.tick(); self.s.tick()
        self.assertEqual(self.s.status,'failed')
        self.assertTrue(self.s.state()['manual_locked'])

if __name__=='__main__': unittest.main()
