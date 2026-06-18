import math
import time

from config import SIM_INITIAL_TORR, TEST_MODE


class DAQC2Reader:
    def __init__(self, address=0, channel=0, test_mode=None):
        self.address = address
        self.channel = channel
        self.test_mode = TEST_MODE if test_mode is None else test_mode
        self.simulated = False
        self._sim_start = time.monotonic()

        if self.test_mode is True:
            self.simulated = True
            return

        try:
            import piplates.DAQCplate as DAQC2
            self._daqc2 = DAQC2
        except Exception:
            if self.test_mode == "AUTO":
                self.simulated = True
            else:
                raise

    def read_voltage(self):
        if self.simulated:
            return self._read_simulated_voltage()

        voltage = self._daqc2.getADC(self.address, self.channel)
        return float(voltage)

    def voltage_to_pressure_972b(self, voltage):
        """
        972B pressure conversion:
        P(Torr) = 10^(2V - 11)
        """
        return 10 ** ((2 * voltage) - 11)

    def read_pressure(self):
        voltage = self.read_voltage()
        pressure = self.voltage_to_pressure_972b(voltage)
        return voltage, pressure

    def _read_simulated_voltage(self):
        elapsed = time.monotonic() - self._sim_start
        pressure = max(1e-5, SIM_INITIAL_TORR * math.exp(-elapsed / 38.0))
        return (math.log10(pressure) + 11) / 2
