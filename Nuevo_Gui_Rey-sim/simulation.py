import random
import math


class ReactorSimulation:
    def __init__(self):
        self.initial_chamber_torr = 1.450e-1
        self.initial_roughing_torr = 1.450e-1

        self.chamber_torr = self.initial_chamber_torr
        self.roughing_torr = self.initial_roughing_torr

        self.temperature = 21.5
        self.pressure_mbar = 1008.0
        self.humidity = 45.0

    def reset(self):
        self.chamber_torr = self.initial_chamber_torr
        self.roughing_torr = self.initial_roughing_torr

    def parse_target_mtorr(self, target_mtorr):
        try:
            target_torr = float(target_mtorr) / 1000.0
        except Exception:
            target_torr = 1.0e-3

        return max(target_torr, 1e-6)

    def target_reached(self, target_mtorr):
        target_torr = self.parse_target_mtorr(target_mtorr)
        return self.chamber_torr <= target_torr

    def update(self, roughing=False, turbo=False, hold=False, target_mtorr="1.000"):
        target_torr = self.parse_target_mtorr(target_mtorr)

        if hold:
            if roughing or turbo:
                factor = 0.972

                if turbo:
                    factor = 0.945

                noise = random.uniform(0.992, 1.008)

                self.chamber_torr = max(
                    target_torr * 0.82,
                    self.chamber_torr * factor * noise
                )

                self.roughing_torr = self.chamber_torr * random.uniform(0.97, 1.03)

            else:
                drift = random.uniform(0.998, 1.006)

                self.chamber_torr = min(
                    self.initial_chamber_torr,
                    max(target_torr * 0.92, self.chamber_torr * drift)
                )

                self.roughing_torr = self.chamber_torr * random.uniform(0.97, 1.03)

        elif roughing or turbo:
            factor = 0.948

            if roughing and turbo:
                factor = 0.895
            elif turbo:
                factor = 0.915

            noise = random.uniform(0.975, 1.012)

            self.chamber_torr = max(
                1e-6,
                self.chamber_torr * factor * noise
            )

            self.roughing_torr = max(
                1e-6,
                self.roughing_torr * 0.935 * noise
            )

        else:
            self.chamber_torr = min(
                self.initial_chamber_torr,
                self.chamber_torr * random.uniform(1.000, 1.002)
            )

            self.roughing_torr = min(
                self.initial_roughing_torr,
                self.roughing_torr * random.uniform(1.000, 1.002)
            )

        self.temperature = 21.5 + random.uniform(-0.15, 0.15)
        self.pressure_mbar = 1008.0 + random.uniform(-1.2, 1.2)
        self.humidity = 45.0 + random.uniform(-1.2, 1.2)

    def target_progress_percent(self, target_mtorr):
        target_torr = self.parse_target_mtorr(target_mtorr)

        start_torr = self.initial_chamber_torr
        current_torr = max(self.chamber_torr, 1e-6)

        if current_torr <= target_torr:
            return 100.0

        if target_torr >= start_torr:
            return 100.0 if current_torr <= target_torr else 0.0

        start_log = math.log10(start_torr)
        current_log = math.log10(current_torr)
        target_log = math.log10(target_torr)

        progress = ((start_log - current_log) / (start_log - target_log)) * 100.0

        return max(0.0, min(100.0, progress))

    def chamber_mtorr(self):
        return self.chamber_torr * 1000.0

    def torr_from_mbar(self):
        return self.pressure_mbar * 0.750062