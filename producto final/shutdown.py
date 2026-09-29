"""Shutdown normal 2026 separado del paro inmediato. Gas manual y enfriamiento."""
import math
import time
import threading
from errores import ControlError

# Orden visual del PDF; solenoide excluido por el usuario.
STEPS = [('gas', 'Cerrar inyeccion manualmente y confirmar', None),
         ('delay', 'Espera despues del cierre manual', 120)]
STEPS += [('relay', n, False) for n in ('Gate Valve A', 'Gate Valve B', 'Diffusion Pump A', 'Diffusion Pump B')]
STEPS += [('temperature', 'Enfriamiento de ambas bombas a 100 °F o menos', None)]
STEPS += [('relay', n, False) for n in ('Diffuse Valve A', 'Diffuse Valve B',
    'Mechanical Pump A', 'Mechanical Pump B', 'Air Compressor', 'Cool Trap A',
    'Cool Trap B', 'Booster Pump', 'Water Chiller')]


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


class Shutdown:
    def __init__(self, control, temperatures, pressures, emergency, startup):
        self.control, self.temperatures, self.pressures = control, temperatures, pressures
        self.emergency = emergency
        self.startup = startup
        self.status = 'idle'
        self.index = 0
        self.deadline = None
        self.message = 'Listo para iniciar'
        self.error = None
        self.readings = {}

    def state(self):
        with self.emergency.lock:
            if self.emergency.active:
                self.status = 'stopped'
                self.message = 'Interrumpido por paro de software'
            steps = STEPS
            kind, title, value = steps[min(self.index, len(STEPS)-1)]
            if kind == 'relay':
                title = f"{title} → {'ON' if value else 'OFF'}"
            condition = {'relay': 'Esperando confirmacion del estado en la placa.',
                         'delay': 'Completar 120 segundos de espera.',
                         'vacuum': 'Medium entre 1 × 10⁻³ y 3 × 10⁻² Torr (ambos limites incluidos).',
                         'temperature': 'Ambas bombas a 100 °F o menos (37.777… °C).',
                         'gas': 'Cerrar la inyeccion en el equipo y confirmar; no se envia consigna al Aera.'}[kind]
            remaining = max(0, math.ceil(self.deadline - time.monotonic())) if self.deadline is not None else None
            progress = []
            for i, (step_kind, name, on) in enumerate(steps):
                label = f"{name} → {'ON' if on else 'OFF'}" if step_kind == 'relay' else name
                phase = 'completado' if i < self.index or self.status == 'complete' else 'pendiente'
                if i == self.index and self.status not in ('idle', 'complete'):
                    phase = {'failed': 'error', 'stopped': 'interrumpido'}.get(self.status, 'actual')
                progress.append({'number': i + 1, 'title': label, 'state': phase})
            return {'title': title, 'condition': condition, 'remaining_seconds': remaining,
                    'readings': dict(self.readings), 'steps': progress,
                    'status': self.status, 'step': min(self.index + 1, len(STEPS)),
                    'total': len(STEPS), 'message': self.message, 'error': self.error,
                    'manual_locked': self.status != 'idle' and self.status != 'complete',
                    'can_start': self.status == 'idle' and self.startup.status in ('idle', 'complete'), 'can_confirm': self.status == 'awaiting_gas'}

    def manual(self, action):
        def guarded():
            if self.status not in ('idle', 'complete'):
                raise ControlError('SHUTDOWN_LOCKED', 'Shutdown: controles manuales bloqueados')
            return action()
        return self.emergency.command(guarded)

    def start(self, background=True):
        def begin():
            if self.status != 'idle':
                raise ControlError('SHUTDOWN_STATE', 'La secuencia ya fue iniciada')
            if self.startup.status not in ('idle', 'complete'):
                raise ControlError('SHUTDOWN_STATE', 'Termine el startup; emergencia disponible para interrumpir')
            self.status = 'awaiting_gas'
            self.background = background
            self.message = 'Cierre la inyeccion manualmente y confirme'
            return self.state()
        return self.emergency.command(begin)

    def confirm_gas(self):
        def confirm():
            if self.status != 'awaiting_gas':
                raise ControlError('SHUTDOWN_STATE', 'No corresponde confirmar el gas en este paso')
            self.status = 'running'
            self.index = 1
            self.deadline = time.monotonic() + 120
            self.message = 'Cierre manual confirmado; esperando 120 segundos'
            if self.background:
                threading.Thread(target=self._run, daemon=True).start()
            return self.state()
        return self.emergency.command(confirm)

    def _run(self):
        while True:
            self.tick()
            if self.state()['status'] != 'running':
                return
            time.sleep(.5)

    def tick(self):
        with self.emergency.lock:
            if self.emergency.active:
                self.state()
                return
            if self.status != 'running':
                return
            if self.index == len(STEPS):
                self.status = 'complete'
                self.message = 'Shutdown normal completado'
                return
            kind, name, value = STEPS[self.index]
            self.message = name
            try:
                if kind == 'relay':
                    self.emergency.command(lambda: self.control.set_relay(name, value))
                elif kind == 'delay':
                    if self.deadline is None:
                        self.deadline = time.monotonic() + value
                    remaining = self.deadline - time.monotonic()
                    if remaining > 0:
                        self.message = f'{name}: {math.ceil(remaining)} s restantes'
                        return
                else:
                    source = self.pressures if kind == 'vacuum' else self.temperatures
                    self.readings = {}
                    data = source.read()
                    timestamp = data.get('timestamp')
                    if not finite(timestamp) or not 0 <= time.time() - timestamp <= 15:
                        raise ValueError('Lectura vencida o sin fecha valida')
                    entries = ([data.get('vacuum', {}).get('Medium Vacuum')] if kind == 'vacuum'
                               else [data.get('temperatures', {}).get(n) for n in
                                     ('Diffusion Pump A', 'Diffusion Pump B')])
                    field = 'torr' if kind == 'vacuum' else 'celsius'
                    names = ['Medium'] if kind == 'vacuum' else ['Diffusion Pump A', 'Diffusion Pump B']
                    self.readings = {label: {'value': entry.get(field) if isinstance(entry, dict) and not entry.get('error') and finite(entry.get(field)) else None,
                                             'unit': 'Torr' if kind == 'vacuum' else '°C'}
                                     for label, entry in zip(names, entries)}
                    for entry in entries:
                        if not entry or entry.get('error') or not finite(entry.get(field)):
                            raise ValueError(f'Lectura invalida: {entry}')
                    low, high = (.001, .030) if kind == 'vacuum' else (float("-inf"), (100-32)*5/9)
                    self.error = None
                    if not all(low <= entry[field] <= high for entry in entries):
                        self.message += ': ' + ', '.join(str(entry[field]) for entry in entries)
                        return
                self.error = None
                self.index += 1
                self.readings = {}
                self.deadline = None
            except Exception as exc:
                self.error = str(exc)
                if kind == 'relay':
                    self.status = 'failed'
                    self.message = 'Orden sin confirmar: secuencia detenida; use Emergency Shutdown'
                else:
                    self.message = f'{name}: esperando lectura valida'
