"""Roughing Vacuum Gauges A/B (ADCplate 3, S4/S5): barras 0-10 V en la planta simulada."""
from planta import Planta
from presiones import Presiones

plant = Planta()
read = lambda: Presiones(plant).read()['rough']
r = read()
assert r['Rough Manifold A']['channel'] == 'S4' and r['Rough Manifold B']['channel'] == 'S5'
assert 9.5 < r['Rough Manifold A']['volts'] <= 10 and r['Rough Manifold A']['percent'] > 95  # 760 Torr, cerca de 10 V
plant.configure({'overrides': {'rough_a_volts': 2.5, 'rough_b_volts': 7.5}, 'faults': []})
r = read()
assert r['Rough Manifold A']['percent'] == 25 and r['Rough Manifold B']['percent'] == 75
plant.configure({'overrides': {'rough_a_volts': 11}, 'faults': ['rough_b_volts']})
r = read()
assert r['Rough Manifold A']['percent'] is None and r['Rough Manifold A']['error']['code'] == 'ROUGH_RANGE'
assert r['Rough Manifold B']['percent'] is None and r['Rough Manifold B']['error']
print('PASS: Rough A/B en S4/S5, 0-10 V a 0-100 %, fuera de rango y fallo de sensor')
