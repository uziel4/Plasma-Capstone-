"""Ejecutar con npm start recien iniciado. Recorre a mano el startup 2026 por Node-RED
y comprueba los permisos de Diffuse, Chamber y Gate Valves. No usa Emergency."""
import json
import os
import time
import urllib.request
import urllib.error

VACUUM = int(os.environ.get('SIM_VACUUM_PORT', 1880))
DASHBOARD = int(os.environ.get('SIM_DASHBOARD_PORT', 1881))
MEDIUM_20_MTORR = 0.6505149978


def request(port, path, data=None):
    req = urllib.request.Request(f'http://127.0.0.1:{port}{path}', data=None if data is None else json.dumps(data).encode(),
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            return res.status, json.loads(res.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def relay(name, on, expect=200, reason=None):
    status, body = request(VACUUM, '/api/relays', {'name': name, 'on': on})
    assert status == expect, (name, on, status, body)
    if reason:
        assert reason in json.dumps(body, ensure_ascii=False), (name, reason, body)


def simulate(overrides):
    assert request(DASHBOARD, '/api/simulation', {'overrides': overrides, 'faults': []})[0] == 200
    time.sleep(1.2)  # Las lecturas se guardan 1 s en cache


def reason(name):
    return request(DASHBOARD, '/api/relays')[1]['relays'][name]['manual_reason']


assert not any(r['on'] for r in request(VACUUM, '/api/relays')[1]['relays'].values()), 'Reiniciar npm start antes de la prueba'
simulate({})
relay('Diffuse Valve A', True, 400, 'falta encender Air Compressor')
for name in ('Air Compressor', 'Water Chiller', 'Booster Pump', 'Cool Trap A'):
    relay(name, True)
relay('Diffuse Valve A', True, 400, 'Cool Trap B')
relay('Cool Trap B', True)
relay('Chamber Valve A', True, 400, 'Diffuse Valve A, Diffuse Valve B')
relay('Diffuse Valve A', True)
relay('Diffuse Valve B', True)
relay('Chamber Valve A', True)
relay('Chamber Valve B', True)
relay('Mechanical Pump A', True)
relay('Mechanical Pump B', True)
relay('Gate Valve A', True, 400, 'falta encender Diffusion Pump A')
assert 'falta apagar Chamber Valve A' in reason('Gate Valve A')
simulate({'medium_volts': MEDIUM_20_MTORR})
relay('Diffusion Pump A', True)
relay('Diffusion Pump B', True)
simulate({'medium_volts': MEDIUM_20_MTORR, 'Diffusion Pump A': 110, 'Diffusion Pump B': 110})
relay('Chamber Valve A', False)  # OFF siempre permitido
relay('Chamber Valve B', False)
relay('Gate Valve A', True, 400, '250 y 300')
simulate({'medium_volts': MEDIUM_20_MTORR, 'Diffusion Pump A': 135, 'Diffusion Pump B': 160})
relay('Gate Valve A', True, 400, '250 y 300')
simulate({'medium_volts': 0.9, 'Diffusion Pump A': 135, 'Diffusion Pump B': 135})
relay('Gate Valve A', True, 400, 'Medium debe estar entre 0.001 y 0.030')
simulate({'medium_volts': MEDIUM_20_MTORR, 'Diffusion Pump A': 135, 'Diffusion Pump B': 135})
assert reason('Gate Valve A') == 'Control manual disponible'
relay('Gate Valve A', True)
relay('Gate Valve B', True)
relay('Diffuse Valve A', False)  # OFF siempre permitido
assert request(DASHBOARD, '/api/relays')[1]['relays']['Gate Valve B']['on'] is True
simulate({})
print('PASS: startup manual por Node-RED; Diffuse, Chamber y Gate Valves bloquean ON hasta cumplir los pasos previos')
