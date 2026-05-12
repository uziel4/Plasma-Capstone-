import random
import math


class VacuumSimulator:
    def __init__(self):
        self.pressure_torr = 760.0
        self.time_seconds = 0

        # Presión mínima realista del sistema simulado
        self.base_pressure = 1e-6

        # Fuga / outgassing pequeño
        self.leak_rate = 2e-8

    def simulate_vacuum_process(self):
        self.time_seconds += 1

        p = self.pressure_torr

        # Diferentes zonas de bombeo
        if p > 100:
            pump_strength = 0.035
        elif p > 10:
            pump_strength = 0.028
        elif p > 1:
            pump_strength = 0.020
        elif p > 1e-2:
            pump_strength = 0.012
        elif p > 1e-4:
            pump_strength = 0.006
        else:
            pump_strength = 0.0025

        # La presión se acerca poco a poco al límite mínimo
        pressure_drop = (p - self.base_pressure) * pump_strength

        # Outgassing/fuga aumenta un poquito la presión
        outgassing = self.leak_rate * (1 + math.sin(self.time_seconds / 20))

        # Ruido proporcional al rango de presión
        noise_percent = random.uniform(-0.015, 0.015)
        noise = p * noise_percent

        # Nueva presión
        self.pressure_torr = p - pressure_drop + outgassing + noise

        # Evita valores imposibles
        if self.pressure_torr < self.base_pressure:
            self.pressure_torr = self.base_pressure + random.uniform(0, 2e-7)

        if self.pressure_torr > 760:
            self.pressure_torr = 760

        return self.pressure_torr