"""Alarma High room temperature: Room (DS18B20, THERMOplate 2 / puerto 9) mayor de 29 °C."""
import logging
import math
import threading
import time
from temperaturas import ROOM_SENSOR

ROOM_ALARM_C = 29.0  # El laboratorio ronda 21-22 °C; la alarma se activa con Room > 29 °C
ROOM_CLEAR_C = 28.0  # Histeresis: la alarma se desactiva al bajar a <= 28 °C
CHECK_SECONDS = 2


class RoomAlarm:
    """Enciende el Buzzer cuando Room > 29 °C y lo apaga al bajar a <= 28 °C,
    solo si lo encendio la alarma. Entre 28 y 29 °C conserva el estado. Un OFF manual del Buzzer lo silencia. Con el
    paro activo no se acciona el Buzzer; el aviso sigue visible en ambos GUI."""

    def __init__(self, control, temperatures, emergency):
        self.control, self.temperatures, self.emergency = control, temperatures, emergency
        self.lock = threading.Lock()
        self.active = False
        self.buzzer_by_alarm = False
        self.celsius = None
        self.error = None

    def state(self):
        with self.lock:
            return {'name': 'High room temperature', 'active': self.active, 'celsius': self.celsius,
                    'limit_c': ROOM_ALARM_C, 'clear_c': ROOM_CLEAR_C, 'buzzer': self.buzzer_by_alarm, 'error': self.error}

    def _buzzer(self, on):
        self.emergency.command(lambda: self.control.set_relay('Buzzer', on))

    def check(self):
        entry = (self.temperatures.read().get('temperatures') or {}).get(ROOM_SENSOR[0]) or {}
        value = entry.get('celsius')
        valid = not entry.get('error') and type(value) in (int, float) and math.isfinite(value)
        with self.lock:
            self.celsius = value if valid else None
            if not valid:
                # Sin lectura no se decide: se conserva el estado y se informa.
                self.error = (entry.get('error') or {}).get('error') or 'Room sin lectura valida'
                return
            high = value > ROOM_ALARM_C or (self.active and value > ROOM_CLEAR_C)
            if high and not self.active:
                logging.warning('ALARMA High room temperature: Room %.2f °C > %.0f °C', value, ROOM_ALARM_C)
            elif not high and self.active:
                logging.info('Alarma High room temperature normalizada: Room %.2f °C', value)
            self.active = high
            self.error = None
            try:
                if high and not self.buzzer_by_alarm:
                    self._buzzer(True)
                    self.buzzer_by_alarm = True
                elif not high and self.buzzer_by_alarm:
                    self._buzzer(False)
                    self.buzzer_by_alarm = False
            except Exception as exc:
                self.error = f'Buzzer no accionado: {exc}'

    def run(self):
        while True:
            try:
                self.check()
            except Exception as exc:
                with self.lock:
                    self.error = f'Fallo al revisar Room: {exc!r}'
            time.sleep(CHECK_SECONDS)

    def start(self):
        threading.Thread(target=self.run, daemon=True, name='room-alarm').start()
        return self
