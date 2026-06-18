# ============================================================
# relay_controller.py
# HL-54 Relay Board usando GPIO directo con gpiozero
#
# HL-54 NO usa I2C.
#
# GPIO 17 | Pin fisico 11 | IN1 | Mechanical Roughing Pump
# GPIO 22 | Pin fisico 15 | IN3 | Gas Mass Control Solenoid Valve
#
# ACTIVE HIGH:
# GPIO HIGH = Relay ON
# GPIO LOW  = Relay OFF
# ============================================================

from config import (
    TEST_MODE,
    RELAY_ACTIVE_LOW,
    ROUGHING_GPIO,
    MASS_FLOW_GPIO,
)


class RelayController:
    def __init__(self, bus_number=None, address=None, test_mode=None):
        # Se dejan para compatibilidad con gui.py
        self.bus_number = bus_number
        self.address = address

        self.test_mode = TEST_MODE if test_mode is None else test_mode
        self.active_low = RELAY_ACTIVE_LOW
        self.simulated = False

        # Relay logico usado por gui.py:
        # 1 = Roughing Pump
        # 2 = Mass Flow Solenoid
        self.relay_pins = {
            1: ROUGHING_GPIO,
            2: MASS_FLOW_GPIO,
        }

        self.relays = {}

        self._initialize_gpio()

    def _initialize_gpio(self):
        if self.test_mode is True:
            self.simulated = True
            print("RelayController en TEST MODE")
            return

        try:
            from gpiozero import OutputDevice

            for relay_number, gpio_pin in self.relay_pins.items():
                self.relays[relay_number] = OutputDevice(
                    pin=gpio_pin,
                    active_high=not self.active_low,
                    initial_value=False
                )

            self.simulated = False
            print("HL-54 GPIO inicializado correctamente con gpiozero")

        except Exception as error:
            if self.test_mode == "AUTO":
                self.simulated = True
                print(f"No se detecto GPIO real. Usando simulacion: {error}")
            else:
                raise

    def relay_on(self, relay_number):
        if relay_number not in self.relay_pins:
            print(f"Relay invalido: {relay_number}")
            return

        if self.simulated:
            print(f"[SIM] Relay {relay_number} GPIO {self.relay_pins[relay_number]} ON")
            return

        self.relays[relay_number].on()

    def relay_off(self, relay_number):
        if relay_number not in self.relay_pins:
            print(f"Relay invalido: {relay_number}")
            return

        if self.simulated:
            print(f"[SIM] Relay {relay_number} GPIO {self.relay_pins[relay_number]} OFF")
            return

        self.relays[relay_number].off()

    def set_relay(self, relay_number, state):
        if state:
            self.relay_on(relay_number)
        else:
            self.relay_off(relay_number)

    def all_off(self):
        for relay_number in self.relay_pins:
            self.relay_off(relay_number)

    def close(self):
        self.all_off()

        if not self.simulated:
            for relay in self.relays.values():
                relay.close()
