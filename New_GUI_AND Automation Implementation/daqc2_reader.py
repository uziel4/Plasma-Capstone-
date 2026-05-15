import piplates.DAQC2plate as DAQC2


class DAQC2Reader:
    def __init__(self, address=0, channel=0):
        self.address = address
        self.channel = channel

    def read_voltage(self):
        voltage = DAQC2.getADC(self.address, self.channel)
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