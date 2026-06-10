# ============================================================
# relay_controller.py
# Controlador para HL-54 Relay Board usando GPIO directo.
#
# Este board NO usa I2C.
#
# Asignación actual:
# Relay lógico 1 = GPIO 17 = Pin físico 11 = Mechanical Roughing Pump
# Relay lógico 2 = GPIO 22 = Pin físico 15 = Gas Mass Control Solenoid Valve
#
# Muchos relay boards trabajan ACTIVE LOW:
# GPIO LOW  = Relay ON
# GPIO HIGH = Relay OFF
# ============================================================

import time

from config import (
    RELAY_ACTIVE_LOW,
    ROUGHING_GPIO,
    MASS_FLOW_GPIO,
)


class RelayController:
    def __init__(self, bus_number=None, address=None):
        # Se dejan estos parámetros para mantener compatibilidad con gui.py.
        # El HL-54 no usa bus_number ni address.
        self.bus_number = bus_number
        self.address = address

        self.active_low = RELAY_ACTIVE_LOW

        # Mapeo lógico usado por gui.py
        self.relay_pins = {
            1: ROUGHING_GPIO,
            2: MASS_FLOW_GPIO,
        }

        self.GPIO = None
        self.simulated = False
        self.relay_states = {
            1: False,
            2: False,
        }

        self._initialize_gpio()

    def _initialize_gpio(self):
        try:
            import RPi.GPIO as GPIO

            self.GPIO = GPIO
            self.GPIO.setwarnings(False)
            self.GPIO.setmode(self.GPIO.BCM)

            for pin in self.relay_pins.values():
                self.GPIO.setup(pin, self.GPIO.OUT)
                self.GPIO.output(pin, self._off_state())

            time.sleep(0.1)
            self.simulated = False

        except Exception as error:
            self.GPIO = None
            self.simulated = True
            print(f"WARNING: GPIO not available. RelayController in simulation mode. {error}")

    def _on_state(self):
        if self.active_low:
            return 0
        return 1

    def _off_state(self):
        if self.active_low:
            return 1
        return 0

    def relay_on(self, relay_number):
        if relay_number not in self.relay_pins:
            print(f"WARNING: Relay {relay_number} is not assigned.")
            return

        pin = self.relay_pins[relay_number]
        self.relay_states[relay_number] = True

        if self.simulated:
            print(f"SIMULATION: Relay {relay_number} ON | GPIO {pin}")
            return

        self.GPIO.output(pin, self._on_state())

    def relay_off(self, relay_number):
        if relay_number not in self.relay_pins:
            print(f"WARNING: Relay {relay_number} is not assigned.")
            return

        pin = self.relay_pins[relay_number]
        self.relay_states[relay_number] = False

        if self.simulated:
            print(f"SIMULATION: Relay {relay_number} OFF | GPIO {pin}")
            return

        self.GPIO.output(pin, self._off_state())

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

        if not self.simulated and self.GPIO is not None:
            self.GPIO.cleanup()