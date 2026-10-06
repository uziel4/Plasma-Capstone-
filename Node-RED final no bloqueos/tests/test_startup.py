import sys
import time
import unittest
from pathlib import Path
from threading import RLock
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from startup import Startup, STEPS
from errores import ControlError

class Emergency:
    def __init__(self): self.lock=RLock(); self.active=False
    def command(self, action):
        with self.lock:
            if self.active: raise ControlError('STOP_LATCHED','Paro')
            return action()
class Control:
    def __init__(self): self.orders=[]; self.fail=False
    def set_relay(self,n,v):
        if self.fail: raise RuntimeError('Sin confirmacion')
        self.orders.append((n,v))
class Reader:
    def __init__(self,data): self.data=data
    def read(self): return self.data

class StartupTests(unittest.TestCase):
    def setUp(self):
        self.e=Emergency(); self.c=Control()
        self.p=Reader({'timestamp':time.time(),'vacuum':{'Medium Vacuum':{'torr':.01,'error':None}}})
        self.t=Reader({'timestamp':time.time(),'temperatures':{n:{'celsius':130,'error':None} for n in ('Diffusion Pump A','Diffusion Pump B')}})
        self.s=Startup(self.c,self.t,self.p,self.e)

    def test_complete_sequence_lock_and_manual_gas(self):
        self.s.start(background=False)
        with self.assertRaises(ControlError): self.s.manual(lambda: None)
        with self.assertRaises(ControlError): self.s.start(background=False)
        with self.assertRaises(ControlError): self.s.confirm_gas()
        with patch('startup.time.monotonic',return_value=0):
            self.s.tick(); self.s.tick()
            self.assertEqual(self.s.index,1)
        with patch('startup.time.monotonic',return_value=119): self.s.tick(); self.assertEqual(self.s.index,1)
        with patch('startup.time.monotonic',return_value=120): self.s.tick()
        while self.s.status=='running':
            if STEPS[self.s.index][0]=='delay' if self.s.index<len(STEPS) else False: self.s.deadline=0
            self.s.tick()
        self.assertEqual(self.s.status,'awaiting_gas')
        with self.assertRaises(ControlError): self.s.manual(lambda: None)
        self.assertEqual(self.c.orders,[(n,v) for k,n,v in STEPS if k=='relay'])
        self.s.confirm_gas()
        self.assertEqual(self.s.manual(lambda: 'allowed'),'allowed')

    def test_wait_invalid_stale_and_out_of_range(self):
        self.s.start(background=False); self.s.index=next(i for i,x in enumerate(STEPS) if x[0]=='vacuum')
        step=self.s.index
        for val in [None,True,.1,float('nan')]:
            self.p.data['vacuum']['Medium Vacuum']['torr']=val; self.s.tick(); self.assertEqual(self.s.index,step)
        self.p.data['vacuum']['Medium Vacuum']['torr']=.01
        self.p.data['timestamp']=0; self.s.tick(); self.assertEqual(self.s.index,step)

    def test_detailed_progress_and_readings(self):
        self.s.start(background=False)
        self.s.index=next(i for i,x in enumerate(STEPS) if x[0]=='temperature')
        self.t.data['temperatures']['Diffusion Pump B']['celsius']=100
        self.s.tick()
        state=self.s.state()
        self.assertEqual(state['readings']['Diffusion Pump A']['value'],130)
        self.assertEqual(state['readings']['Diffusion Pump B']['value'],100)
        self.assertEqual(state['steps'][self.s.index]['state'],'actual')
        self.assertEqual(state['steps'][0]['state'],'completado')
        self.assertIn('250',state['condition'])
        self.t.data['timestamp']=0
        self.s.tick()
        self.assertEqual(self.s.state()['readings'],{})
        self.assertIsNotNone(self.s.state()['error'])

    def test_both_temperatures_required(self):
        self.s.start(background=False); self.s.index=next(i for i,x in enumerate(STEPS) if x[0]=='temperature')
        step=self.s.index; self.t.data['temperatures']['Diffusion Pump B']['celsius']=100
        self.s.tick(); self.assertEqual(self.s.index,step)

    def test_emergency_prevents_future_orders_and_confirmation(self):
        self.s.start(background=False); self.e.active=True; self.s.tick()
        self.assertEqual(self.s.state()['status'],'stopped'); self.assertEqual(self.c.orders,[])
        with self.assertRaises(ControlError): self.s.confirm_gas()

    def test_uncertain_command_no_retry(self):
        self.c.fail=True; self.s.start(background=False); self.s.tick(); self.s.tick()
        self.assertEqual(self.s.status,'failed'); self.assertEqual(self.s.index,0)
        with self.assertRaises(ControlError): self.s.manual(lambda: None)

class EmergencyDuringStartupTests(unittest.TestCase):
    def test_real_stop_during_wait_and_gas_confirmation(self):
        from emergency_shutdown import EmergencyShutdown
        from types import SimpleNamespace
        for phase in ('running', 'awaiting_gas', 'failed'):
            calls=[]
            control=Control()
            control.driver=SimpleNamespace(relayOFF=lambda a,r: calls.append((a,r)), relaySTATE=lambda a:0)
            mass=SimpleNamespace(set_percent=lambda value: calls.append(('gas',value)))
            emergency=EmergencyShutdown(control,mass)
            startup=Startup(control,Reader({}),Reader({}),emergency)
            startup.status=phase
            result=emergency.stop('Paro durante startup')
            self.assertTrue(result['result']['confirmed'])
            self.assertEqual(len(calls),17)
            startup.tick()
            self.assertEqual(startup.state()['status'],'stopped')
            self.assertEqual(control.orders,[])
            with self.assertRaises(ControlError): startup.confirm_gas()

class StartupApiTests(unittest.TestCase):
    def test_routes_block_manual_and_allow_final_confirmation(self):
        import json
        import http.client
        import threading
        from http.server import ThreadingHTTPServer
        from main import handler_for
        e=Emergency(); c=Control()
        r=Reader({}); startup=Startup(c,r,r,e)
        class Mass:
            def set_percent(self,value): raise AssertionError('Manual DAC must be blocked')
        with patch('main.Startup',return_value=startup):
            server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(c,r,r,Mass(),e))
        worker=threading.Thread(target=server.serve_forever,daemon=True); worker.start()
        def request(path,body=None):
            client=http.client.HTTPConnection(*server.server_address)
            client.request('GET' if body is None else 'POST',path,
                           body=None if body is None else json.dumps(body),
                           headers={'Content-Type':'application/json'})
            response=client.getresponse(); result=(response.status,json.loads(response.read()))
            client.close(); return result
        try:
            self.assertTrue(request('/api/startup')[1]['can_start'])
            with patch.object(startup,'_run',return_value=None):
                self.assertEqual(request('/api/startup',{})[0],200)
            self.assertEqual(request('/api/relays',{'name':'Air Compressor','on':True})[1]['code'],'STARTUP_LOCKED')
            self.assertEqual(request('/api/mass-flow',{'percent':10})[1]['code'],'STARTUP_LOCKED')
            self.assertEqual(request('/api/startup/confirm-gas',{})[1]['code'],'STARTUP_STATE')
            startup.status='awaiting_gas'
            self.assertEqual(request('/api/startup/confirm-gas',{})[1]['status'],'complete')
            self.assertFalse(request('/api/startup')[1]['manual_locked'])
        finally:
            server.shutdown(); server.server_close(); worker.join()

if __name__=='__main__': unittest.main()
