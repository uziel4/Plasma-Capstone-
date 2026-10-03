"""Ejecutar con npm start activo. Termina enclavando Emergency simulado."""
import json
import os
import urllib.request
import urllib.error

ports={1880:int(os.environ.get('SIM_VACUUM_PORT',1880)),1881:int(os.environ.get('SIM_DASHBOARD_PORT',1881))}

def request(port,path,data=None):
    req=urllib.request.Request(f'http://127.0.0.1:{ports.get(port,port)}{path}',data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=5) as res: return res.status,json.loads(res.read())
    except urllib.error.HTTPError as exc: return exc.code,json.loads(exc.read())

for port in (1880,1881):
    with urllib.request.urlopen(f'http://127.0.0.1:{ports.get(port,port)}/') as r:
        assert b'FlowFuse Dashboard' in r.read()
    assert request(port,'/api/temperatures')[0]==200
    assert request(port,'/api/pressures')[1]['simulation'] is True
assert request(1880,'/api/relays',{'name':'Diffusion Pump A','on':True})[0]==400
assert request(1880,'/api/simulation',{'overrides':{'medium_volts':0.6505149978},'faults':[]})[0]==200
assert request(1880,'/api/relays',{'name':'Diffusion Pump A','on':True})[0]==200
assert request(1881,'/api/relays')[1]['relays']['Diffusion Pump A']['on'] is True
assert request(1880,'/api/startup',{})[0]==200
assert request(1881,'/api/relays',{'name':'Buzzer','on':True})[0]!=200
assert request(1881,'/api/emergency',{})[1]['active'] is True
assert not any(e['on'] for e in request(1880,'/api/relays')[1]['relays'].values())
assert request(1880,'/api/relays',{'name':'Air Compressor','on':True})[0]!=200
assert request(1880,'/api/mass-flow',{'sccm':100})[0]!=200
print('PASS: dos Node-RED, API compartida, bloqueo difusion/startup, Emergency, mass deshabilitado')
