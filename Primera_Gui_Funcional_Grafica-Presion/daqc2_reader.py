import piplates.DAQC2plate as DAQC2


class DAQC2Reader:
    def __init__(self, address=0, channel=0):
        self.address = address
        self.channel = channel

    def read_voltage(self):
        voltage = DAQC2.getADC(self.address, self.channel)
        return voltage