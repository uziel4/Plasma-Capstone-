# ============================================================
# daqc2_reader.py
# Este archivo se encarga de leer el sensor 972B desde DAQC2.
#
# También incluye un modo simulado para poder probar el GUI
# en Mac/Windows sin Raspberry Pi ni DAQC2plate.
# ============================================================

import math
import random

from config import SIM_INITIAL_TORR


class DAQC2Reader:
    def __init__(self, address=0, channel=0, test_mode="AUTO"):
        # Dirección del DAQC2plate
        self.address = address

        # Canal analógico usado. Para A0 usamos channel 0.
        self.channel = channel

        # Guarda el modo de prueba
        self.test_mode = test_mode

        # Variable para saber si estamos usando simulación
        self.simulated = False

        # Presión simulada inicial
        self.sim_pressure = SIM_INITIAL_TORR

        # Intentamos cargar la librería real del DAQC2
        self.DAQC2 = None
        self._initialize_hardware()

    def _initialize_hardware(self):
        """
        Intenta importar la librería real de Pi-Plates.
        Si estás en Mac/Windows o no tienes piplates instalado,
        automáticamente usa simulación.
        """

        if self.test_mode is True:
            self.simulated = True
            return

        try:
            import piplates.DAQC2plate as DAQC2
            self.DAQC2 = DAQC2
            self.simulated = False

        except Exception:
            if self.test_mode == "AUTO":
                self.simulated = True
            else:
                raise

    def voltage_to_pressure_972b(self, voltage):
        """
        Fórmula del sensor 972B:

        P(Torr) = 10^(2V - 11)

        Esta fórmula convierte el voltaje leído por el DAQC2
        en presión real en Torr.
        """
        return 10 ** ((2 * voltage) - 11)

    def pressure_to_voltage_972b(self, pressure):
        """
        Fórmula inversa usada solamente en TEST MODE.

        Si:
        P = 10^(2V - 11)

        entonces:
        log10(P) = 2V - 11
        V = (log10(P) + 11) / 2
        """
        pressure = max(pressure, 1e-9)
        return (math.log10(pressure) + 11) / 2

    def read_voltage(self):
        """
        Lee voltaje real del DAQC2 o genera voltaje simulado.
        """

        if self.simulated:
            return self.pressure_to_voltage_972b(self.sim_pressure)

        voltage = self.DAQC2.getADC(self.address, self.channel)
        return float(voltage)

    def read_pressure(self):
        """
        Devuelve:
        voltage, pressure

        voltage  = lectura analógica
        pressure = presión calculada en Torr
        """

        voltage = self.read_voltage()
        pressure = self.voltage_to_pressure_972b(voltage)

        return voltage, pressure

    def update_simulation(self, roughing=False, mass_flow=False, hold=False, target_torr=1e-3):
        """
        Esta función solo afecta el TEST MODE.
        Simula cómo bajaría o subiría la presión dependiendo
        de los relays virtuales.
        """

        if not self.simulated:
            return

        # Si la bomba roughing está activa, la presión baja
        if roughing:
            self.sim_pressure *= random.uniform(0.955, 0.985)

        # Si el mass flow está activo, entra gas y la presión sube
        elif mass_flow:
            self.sim_pressure *= random.uniform(1.010, 1.035)

        # Si está en hold mode sin actuar, la presión se mueve poco
        elif hold:
            self.sim_pressure *= random.uniform(0.998, 1.004)

        # Si todo está apagado, la cámara puede perder vacío lentamente
        else:
            self.sim_pressure *= random.uniform(1.000, 1.002)

        # Límites seguros para que la simulación no explote
        self.sim_pressure = max(1e-7, min(SIM_INITIAL_TORR, self.sim_pressure))