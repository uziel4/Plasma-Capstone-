# ============================================================
# relay_controller.py
# Controla el módulo de 8 relays por I2C.
#
# También tiene TEST MODE para correr en Mac/Windows sin relays.
#
# Lógica usada por el módulo:
# 0 = relay ON
# 1 = relay OFF
#
# Relay 1 usa bit 0.
# Relay 2 usa bit 1.
# ============================================================

import time


class RelayController:
    OUTPUT_PORT0 = 0x02
    OUTPUT_PORT1 = 0x03
    CONFIG_PORT0 = 0x06
    CONFIG_PORT1 = 0x07

    def __init__(self, bus_number=1, address=0x21, test_mode="AUTO"):
        # Bus I2C usado por Raspberry Pi
        self.bus_number = bus_number

        # Dirección I2C del relay module
        self.address = address

        # Modo de prueba
        self.test_mode = test_mode

        # Estado interno de los puertos.
        # 0xFF significa todos apagados porque la lógica es active-low.
        self.port0_state = 0xFF
        self.port1_state = 0xFF

        # Variable para saber si estamos simulando
        self.simulated = False

        # Bus real
        self.bus = None

        self._initialize_hardware()

    def _initialize_hardware(self):
        """
        Intenta abrir el bus I2C real.
        Si no existe, usa simulación en modo AUTO.
        """

        if self.test_mode is True:
            self.simulated = True
            return

        try:
            import smbus2
            self.bus = smbus2.SMBus(self.bus_number)

            # Configura ambos puertos como salidas
            self.bus.write_byte_data(self.address, self.CONFIG_PORT0, 0x00)
            self.bus.write_byte_data(self.address, self.CONFIG_PORT1, 0x00)
            time.sleep(0.1)

            self.simulated = False
            self.all_off()

        except Exception:
            if self.test_mode == "AUTO":
                self.simulated = True
            else:
                raise

    def _write_ports(self):
        """
        Escribe el estado actual al módulo real.
        En TEST MODE no hace nada físico.
        """

        if self.simulated:
            return

        self.bus.write_byte_data(self.address, self.OUTPUT_PORT0, self.port0_state)
        self.bus.write_byte_data(self.address, self.OUTPUT_PORT1, self.port1_state)

    def relay_on(self, relay_number):
        """
        Enciende un relay específico.
        relay_number debe ser 1 a 8.
        """

        if not 1 <= relay_number <= 8:
            return

        bit = relay_number - 1

        # Active-low:
        # Para encender se escribe 0 en el bit correspondiente
        self.port0_state &= ~(1 << bit) & 0xFF

        self._write_ports()

    def relay_off(self, relay_number):
        """
        Apaga un relay específico.
        relay_number debe ser 1 a 8.
        """

        if not 1 <= relay_number <= 8:
            return

        bit = relay_number - 1

        # Active-low:
        # Para apagar se escribe 1 en el bit correspondiente
        self.port0_state |= (1 << bit)
        self.port0_state &= 0xFF

        self._write_ports()

    def set_relay(self, relay_number, state):
        """
        state = True  -> relay ON
        state = False -> relay OFF
        """

        if state:
            self.relay_on(relay_number)
        else:
            self.relay_off(relay_number)

    def all_off(self):
        """
        Apaga todos los relays.
        Se llama cuando se abre o se cierra el GUI.
        """

        self.port0_state = 0xFF
        self.port1_state = 0xFF
        self._write_ports()

    def close(self):
        """
        Apaga relays y cierra el bus I2C.
        """

        self.all_off()

        if self.bus is not None and not self.simulated:
            self.bus.close()