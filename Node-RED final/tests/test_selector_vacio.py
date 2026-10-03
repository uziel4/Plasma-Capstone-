import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from selector_vacio import SelectorVacio, MEDIUM, HIGH
from errores import ControlError
from autovacio import accion_con_sensores


def packet(m, h, error=None):
    return {MEDIUM: {'torr': m, 'error': None}, HIGH: {'torr': h, 'error': error}}


class SelectorTests(unittest.TestCase):
    def test_high_without_medium_agreement(self):
        for m in (None, .001):
            s = SelectorVacio()
            self.assertEqual(s.seleccionar(packet(m, 1e-3), 1, 1)['sensor'], HIGH)

    def test_return_medium_when_high_above_range(self):
        s = SelectorVacio()
        s.seleccionar(packet(None, 1e-5), 1, 1)
        self.assertEqual(s.seleccionar(packet(.002, .002), 2, 2)['sensor'], MEDIUM)

    def test_high_failure_not_range_exit(self):
        s = SelectorVacio()
        s.seleccionar(packet(None, 1e-5), 1, 1)
        with self.assertRaises(ControlError):
            s.seleccionar(packet(None, None, {'code': 'VAC_READ'}), 2, 2)

    def test_return_uses_medium_even_with_high_saturated_or_failed(self):
        for high, error in [(1e-3, None), (1e-5, None), (None, {'code': 'VAC_READ'})]:
            s = SelectorVacio()
            s.seleccionar(packet(None, 1e-5), 1, 1)
            result = s.seleccionar(packet(.002, high, error), 2, 2)
            self.assertEqual(result, {'sensor': MEDIUM, 'torr': .002})
            self.assertEqual(s.seleccionar(packet(.002, 1e-5), 3, 3)['sensor'], MEDIUM)
            self.assertEqual(s.seleccionar(packet(.001, 1e-5), 4, 4)['sensor'], HIGH)

    def test_invalid_medium_cannot_force_return(self):
        for value in [True, float('nan'), 1001]:
            self.assertEqual(SelectorVacio().seleccionar(packet(value,1e-5),1,1)['sensor'], HIGH)
        data = packet(.02, 1e-5)
        data[MEDIUM]['error'] = {'code': 'VAC_READ'}
        self.assertEqual(SelectorVacio().seleccionar(data,1,1)['sensor'], HIGH)

    def test_exact_boundary_without_high(self):
        self.assertEqual(SelectorVacio().seleccionar(packet(.001,None),1,1)['sensor'], MEDIUM)

    def test_medium_before_high_available(self):
        self.assertEqual(SelectorVacio().seleccionar(packet(.03, None), 1, 1)['sensor'], MEDIUM)

    def test_invalid_packets_and_no_valid_sensor(self):
        for data, stamp, now in [(packet(None,None),1,1), (packet(None,1e-10),1,1),
                                 (packet(.02,None),1,5), (packet(.02,None),2,1),
                                 (packet(True,float('nan')),1,1)]:
            with self.assertRaises(ControlError): SelectorVacio().seleccionar(data,stamp,now)
        s=SelectorVacio(); s.seleccionar(packet(.03,None),1,1)
        with self.assertRaises(ControlError): s.seleccionar(packet(.03,None),1,1)

    def test_direction_uses_high(self):
        result=accion_con_sensores(SelectorVacio(),packet(.001,1e-5),1,1,2e-5,1e-6)
        self.assertEqual(result['accion'],'ABRIR_MAS')

if __name__ == '__main__': unittest.main()
