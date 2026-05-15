import smbus2
import time


class RelayController:
    """
    Controller for 8-channel relay module using PCF8574-style I2C logic.

    Relay logic:
    - 0 = relay ON
    - 1 = relay OFF

    Relay 1 uses bit 0.
    Relay 2 uses bit 1.
    """

    OUTPUT_PORT0 = 0x02
    OUTPUT_PORT1 = 0x03
    CONFIG_PORT0 = 0x06
    CONFIG_PORT1 = 0x07

    def __init__(self, bus_number=1, address=0x21):
        self.address = address
        self.bus = smbus2.SMBus(bus_number)

        self.port0_state = 0xFF
        self.port1_state = 0xFF

        self._configure_outputs()
        self.all_off()

    def _configure_outputs(self):
        self.bus.write_byte_data(self.address, self.CONFIG_PORT0, 0x00)
        self.bus.write_byte_data(self.address, self.CONFIG_PORT1, 0x00)
        time.sleep(0.1)

    def _write_ports(self):
        self.bus.write_byte_data(self.address, self.OUTPUT_PORT0, self.port0_state)
        self.bus.write_byte_data(self.address, self.OUTPUT_PORT1, self.port1_state)

    def relay_on(self, relay_number):
        if not 1 <= relay_number <= 8:
            return

        bit = relay_number - 1
        self.port0_state &= ~(1 << bit) & 0xFF
        self._write_ports()

    def relay_off(self, relay_number):
        if not 1 <= relay_number <= 8:
            return

        bit = relay_number - 1
        self.port0_state |= (1 << bit)
        self.port0_state &= 0xFF
        self._write_ports()

    def set_relay(self, relay_number, state):
        if state:
            self.relay_on(relay_number)
        else:
            self.relay_off(relay_number)

    def all_off(self):
        self.port0_state = 0xFF
        self.port1_state = 0xFF
        self._write_ports()

    def close(self):
        self.all_off()
        self.bus.close()