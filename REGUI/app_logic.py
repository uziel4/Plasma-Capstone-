import math
import threading
import time
from collections import deque

from config import (
    DAQC2_ADDRESS,
    DAQC2_CHANNEL,
    MASS_FLOW_RELAY,
    RELAY_I2C_ADDRESS,
    RELAY_I2C_BUS,
    ROUGHING_RELAY,
    VACUUM_TOLERANCE,
)
from daqc2_reader import DAQC2Reader
from relay_controller import RelayController


class PlasmaController:
    def __init__(self):
        self.daq = DAQC2Reader(address=DAQC2_ADDRESS, channel=DAQC2_CHANNEL)
        self.relay = RelayController(bus_number=RELAY_I2C_BUS, address=RELAY_I2C_ADDRESS)

        self.lock = threading.RLock()
        self.stop_event = threading.Event()

        self.auto_active = False
        self.hv_active = False
        self.hold_mode = False
        self.roughing_active = False
        self.turbo_active = False
        self.mass_flow_active = False

        self.target_mtorr = 0.0
        self.hv_voltage = 0.0
        self.hv_voltage_applied = False
        self.hv_start_time = None
        self.hv_total_seconds = 30
        self.timer_seconds_remaining = 30
        self.timer_buzzer_fired = False

        self.current_voltage = 0.0
        self.current_torr = 1.0e-1
        self.initial_torr = 1.0e-1
        self.progress_start_torr = self.current_torr
        self.sensor_error = None
        self.status = "SYSTEM READY"

        self.last_relay_states = {}
        self.graph_start_timestamp = None
        self.last_sensor_timestamp = None
        self.points = deque(maxlen=240)

        self.worker = threading.Thread(target=self._run_sensor_loop, daemon=True)
        self.worker.start()

    def start_auto(self):
        with self.lock:
            if not self.has_valid_target(self.target_mtorr):
                self.auto_active = False
                self.hold_mode = False
                self.roughing_active = False
                self.mass_flow_active = False
                self.turbo_active = False
                self.status = "ENTER TARGET VACUUM"
                self._apply_relays_locked()
                return False

            self.auto_active = True
            self.hold_mode = False
            self.roughing_active = True
            self.mass_flow_active = False
            self.turbo_active = False
            self.progress_start_torr = max(self.current_torr, 1e-9)
            self.status = "AUTO PUMPDOWN ACTIVE"
            self._apply_relays_locked()

    def stop_auto(self):
        with self.lock:
            self.auto_active = False
            self.hold_mode = False
            self.roughing_active = False
            self.turbo_active = False
            self.mass_flow_active = False
            self.status = "SYSTEM STOPPED"
            self._apply_relays_locked()

    def reset_system(self):
        with self.lock:
            self.auto_active = False
            self.hv_active = False
            self.hold_mode = False
            self.roughing_active = False
            self.turbo_active = False
            self.mass_flow_active = False
            self.target_mtorr = 0.0
            self.hv_voltage = 0.0
            self.hv_voltage_applied = False
            self.hv_start_time = None
            self.hv_total_seconds = 30
            self.timer_seconds_remaining = 30
            self.timer_buzzer_fired = False
            self.relay.buzzer_off()
            self.graph_start_timestamp = None
            self.last_sensor_timestamp = None
            self.progress_start_torr = max(self.current_torr, 1e-9)
            self.points.clear()
            self.status = "SYSTEM RESET"
            self._apply_relays_locked()

    def set_target(self, target_mtorr):
        with self.lock:
            try:
                self.target_mtorr = max(float(target_mtorr), 0.0)
            except (TypeError, ValueError):
                self.target_mtorr = 0.0
            self.progress_start_torr = max(self.current_torr, 1e-9)
            if self.auto_active:
                self.hold_mode = False
                self._update_auto_logic_locked()

    def toggle_roughing(self):
        with self.lock:
            if self.auto_active:
                return
            self.roughing_active = not self.roughing_active
            self._apply_relays_locked()

    def toggle_mass_flow(self):
        with self.lock:
            if self.auto_active:
                return
            self.mass_flow_active = not self.mass_flow_active
            self._apply_relays_locked()

    def toggle_turbo(self):
        with self.lock:
            self.turbo_active = False
            self.status = "TURBOMOLECULAR PUMP UNAVAILABLE"

    def set_hv_voltage(self, voltage):
        with self.lock:
            try:
                value = float(voltage)
            except (TypeError, ValueError):
                return False
            if value < 0:
                return False
            self.hv_voltage = value
            self.hv_voltage_applied = True
            return True

    def reset_hv_voltage(self):
        with self.lock:
            self.hv_voltage = 0.0
            self.hv_voltage_applied = False

    def set_timer(self, value):
        with self.lock:
            seconds = self.parse_time(value)
            self.hv_total_seconds = seconds
            self.timer_buzzer_fired = False
            if not self.hv_active:
                self.timer_seconds_remaining = seconds

    def toggle_hv(self):
        with self.lock:
            if self.hv_active:
                self.hv_active = False
                self.hv_start_time = None
                self.timer_seconds_remaining = self.hv_total_seconds
                self.timer_buzzer_fired = False
                self.relay.buzzer_off()
            else:
                self.hv_active = True
                self.hv_start_time = time.monotonic()
                self.timer_seconds_remaining = self.hv_total_seconds
                self.timer_buzzer_fired = False
                self.relay.buzzer_off()

    def reset_hv_timer(self):
        with self.lock:
            self.hv_active = False
            self.hv_start_time = None
            self.hv_total_seconds = 30
            self.timer_seconds_remaining = 30
            self.timer_buzzer_fired = False
            self.relay.buzzer_off()

    def get_state(self):
        with self.lock:
            progress = self.target_progress_percent(self.current_torr, self.target_mtorr)
            progress_text = f"{progress:0.0f}% TO TARGET"
            if not self.has_valid_target(self.target_mtorr):
                progress_text = "0% - ENTER TARGET"
            elif self.hold_mode:
                progress_text = f"{progress:0.0f}% - HOLDING TARGET"

            return {
                "status": self.status,
                "mode": "AUTO" if self.auto_active else "MANUAL",
                "autoActive": self.auto_active,
                "holdMode": self.hold_mode,
                "roughingActive": self.roughing_active,
                "turboActive": self.turbo_active,
                "massFlowActive": self.mass_flow_active,
                "hvActive": self.hv_active,
                "hvVoltage": self.hv_voltage,
                "hvVoltageApplied": self.hv_voltage_applied,
                "timer": self.format_time(self.timer_seconds_remaining),
                "targetMtorr": self.target_mtorr,
                "voltage": self.current_voltage,
                "pressureTorr": self.current_torr,
                "pressureText": self.format_pressure(self.current_torr),
                "progress": progress,
                "progressText": progress_text,
                "sensorError": self.sensor_error,
                "relaySimulated": self.relay.simulated,
                "points": list(self.points),
            }

    def close(self):
        self.stop_event.set()
        with self.lock:
            self.roughing_active = False
            self.mass_flow_active = False
            self.turbo_active = False
            self.relay.buzzer_off()
            self._apply_relays_locked()
        self.relay.close()

    def _run_sensor_loop(self):
        while not self.stop_event.is_set():
            try:
                voltage, pressure = self.daq.read_pressure()
                self._accept_sensor_reading(voltage, max(pressure, 1e-9))
            except Exception as error:
                with self.lock:
                    self.sensor_error = str(error)
                    self.status = f"SENSOR ERROR: {error}"

            self._update_hv_timer()
            self.stop_event.wait(0.5)

    def _accept_sensor_reading(self, voltage, pressure):
        timestamp = time.monotonic()
        with self.lock:
            self.current_voltage = voltage
            self.current_torr = pressure
            self.sensor_error = None

            if not self.points:
                self.initial_torr = pressure
                self.progress_start_torr = pressure
                self.graph_start_timestamp = timestamp

            self._update_auto_logic_locked()
            self._append_graph_point_locked(timestamp)

    def _append_graph_point_locked(self, timestamp):
        if self.graph_start_timestamp is None:
            self.graph_start_timestamp = timestamp

        if timestamp == self.last_sensor_timestamp:
            return

        elapsed = timestamp - self.graph_start_timestamp
        self.last_sensor_timestamp = timestamp
        self.points.append({"time": elapsed, "pressure": max(self.current_torr, 1e-9)})

    def _update_auto_logic_locked(self):
        if not self.auto_active:
            return

        if not self.has_valid_target(self.target_mtorr):
            self.hold_mode = False
            self.roughing_active = False
            self.turbo_active = False
            self.mass_flow_active = False
            self.status = "ENTER TARGET VACUUM"
            self._apply_relays_locked()
            return

        target_torr = self.parse_target_torr(self.target_mtorr)
        lower_limit = target_torr * (1.0 - VACUUM_TOLERANCE)
        upper_limit = target_torr * (1.0 + VACUUM_TOLERANCE)

        previous = (
            self.roughing_active,
            self.turbo_active,
            self.mass_flow_active,
            self.hold_mode,
        )

        if not self.hold_mode:
            if self.current_torr <= target_torr:
                self.hold_mode = True
                self.roughing_active = True
                self.turbo_active = False
                self.mass_flow_active = True
                self.status = "TARGET REACHED - HOLD MODE"
            else:
                self.roughing_active = True
                self.turbo_active = False
                self.mass_flow_active = False
                self.status = "ROUGHING PUMP ACTIVE"
        else:
            self.turbo_active = False
            self.roughing_active = True
            if self.current_torr < lower_limit:
                self.mass_flow_active = True
                self.status = "MASS FLOW ACTIVE - REGULATING"
            elif self.current_torr > upper_limit:
                self.mass_flow_active = False
                self.status = "VACUUM LOSS - MASS FLOW OFF"
            else:
                self.mass_flow_active = True
                self.status = "HOLDING TARGET VACUUM"

        current = (
            self.roughing_active,
            self.turbo_active,
            self.mass_flow_active,
            self.hold_mode,
        )
        if current != previous:
            self._apply_relays_locked()

    def _update_hv_timer(self):
        with self.lock:
            if not self.hv_active or self.hv_start_time is None:
                return

            elapsed = int(time.monotonic() - self.hv_start_time)
            remaining = self.hv_total_seconds - elapsed
            self.timer_seconds_remaining = max(0, remaining)

            if remaining <= 0:
                if not self.timer_buzzer_fired:
                    self.timer_buzzer_fired = True
                    self.relay.buzz_timer_alarm()

    def _apply_relays_locked(self):
        desired_states = {
            ROUGHING_RELAY: self.roughing_active,
            MASS_FLOW_RELAY: self.mass_flow_active,
        }

        for relay_number, active in desired_states.items():
            if self.last_relay_states.get(relay_number) == active:
                continue
            self.relay.set_relay(relay_number, active)
            self.last_relay_states[relay_number] = active

    @staticmethod
    def has_valid_target(target_mtorr):
        try:
            return float(target_mtorr) > 0.0
        except (TypeError, ValueError):
            return False

    @staticmethod
    def parse_target_torr(target_mtorr):
        try:
            target_torr = float(target_mtorr) / 1000.0
        except (TypeError, ValueError):
            target_torr = 0.0
        return max(target_torr, 1.0e-6)

    def target_progress_percent(self, current_torr, target_mtorr):
        if not self.has_valid_target(target_mtorr):
            return 0.0

        target_torr = self.parse_target_torr(target_mtorr)
        start_torr = max(self.progress_start_torr, 1e-9)
        current_torr = max(current_torr, 1e-6)

        if current_torr <= target_torr:
            return 100.0

        if target_torr >= start_torr:
            return 100.0 if current_torr <= target_torr else 0.0

        start_log = math.log10(start_torr)
        current_log = math.log10(current_torr)
        target_log = math.log10(target_torr)
        progress = ((start_log - current_log) / (start_log - target_log)) * 100.0
        return max(0.0, min(100.0, progress))

    @staticmethod
    def parse_time(value):
        try:
            h, m, s = str(value).split(":")
            total = int(h) * 3600 + int(m) * 60 + int(s)
            return max(1, total)
        except Exception:
            return 30

    @staticmethod
    def format_time(seconds):
        seconds = max(0, int(seconds))
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    @staticmethod
    def format_pressure(value):
        if value <= 0:
            return "0 Torr"

        exponent = int(math.floor(math.log10(abs(value))))
        coefficient = value / (10 ** exponent)
        return f"{coefficient:0.3f} x 10^{exponent} Torr"
