"""Servidor local del Vacuum Controller: python3 main.py."""
import argparse
import signal
import json
import webbrowser
import threading
import logging
from logging.handlers import RotatingFileHandler
from errores import ControlError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from manual_control import ManualControl
from temperaturas import Temperaturas
from presiones import Presiones
from masscontroll import MassControl
from emergency_shutdown import EmergencyShutdown
from startup import Startup
from shutdown import Shutdown
from alarma_room import RoomAlarm

ROOT = Path(__file__).resolve().parent


def handler_for(control, temperatures, pressures, mass=None, emergency=None, alarm=None):
    mass = mass or MassControl()
    emergency = emergency or EmergencyShutdown(control, mass)
    alarm = alarm or RoomAlarm(control, temperatures, emergency)
    startup = Startup(control, temperatures, pressures, emergency)
    shutdown = Shutdown(control, temperatures, pressures, emergency, startup)
    class Handler(BaseHTTPRequestHandler):
        def failure(self, status, exc):
            if not isinstance(exc, ControlError):
                exc = ControlError('INTERNAL', 'Error inesperado', repr(exc))
            logging.error('%s', exc, exc_info=True)
            self.reply(status, exc.payload())

        def reply(self, status, body, content_type='application/json'):
            data = json.dumps(body).encode() if content_type == 'application/json' else body
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == '/api/shutdown':
                self.reply(200, shutdown.state())
                return
            if self.path == '/api/startup':
                self.reply(200, startup.state())
                return
            if self.path == '/api/emergency':
                self.reply(200, emergency.state())
                return
            if self.path == '/api/mass-flow':
                try:
                    raise ControlError('INPUT', 'Manual Gas Flow Control no habilitado; proximamente para grupos futuros')
                except Exception as exc:
                    self.failure(503, exc)
                return
            if self.path == '/api/pressures':
                try:
                    self.reply(200, pressures.read())
                except Exception as exc:
                    self.failure(503, exc)
                return
            if self.path == '/api/temperatures':
                try:
                    self.reply(200, {**temperatures.read(), 'room_alarm': alarm.state()})
                except Exception as exc:
                    self.failure(503, exc)
                return
            if self.path == '/api/relays':
                try:
                    self.reply(200, control.manual_states(pressures.read(), temperatures.read()))
                except Exception as exc:
                    self.failure(503, exc)
                return
            files = {'/startup.js': 'startup.js', '/screen_fit.js': 'screen_fit.js', '/emergency.js': 'emergency.js', '/masscontroll.js': 'masscontroll.js', '/': 'vacuum_controller.html', '/vacuum_controller.html': 'vacuum_controller.html',
                     '/dashboard.html': 'dashboard.html', '/dashboard.js': 'dashboard.js', '/temperaturas.js': 'temperaturas.js', '/presiones.js': 'presiones.js', '/vacio.js': 'vacio.js', '/manual_control.js': 'manual_control.js'}
            if self.path not in files:
                self.failure(404, ControlError('HTTP_ROUTE', 'Ruta no encontrada', self.path))
                return
            content_type = 'application/javascript' if self.path.endswith('.js') else 'text/html; charset=utf-8'
            try:
                body = (ROOT / files[self.path]).read_bytes()
            except OSError as exc:
                self.failure(500, ControlError('GUI_FILE', 'No se pudo leer el archivo del GUI', repr(exc), archivo=files[self.path]))
                return
            self.reply(200, body, content_type)

        def do_POST(self):
            if self.path not in ('/api/relays', '/api/mass-flow', '/api/emergency', '/api/startup', '/api/startup/confirm-gas', '/api/shutdown', '/api/shutdown/confirm-gas'):
                self.failure(404, ControlError('HTTP_ROUTE', 'Ruta no encontrada', self.path))
                return
            # Solo peticiones JSON del GUI del mismo origen.
            if self.headers.get('Origin') not in (None, 'http://' + self.headers.get('Host', '')):
                self.failure(403, ControlError('HTTP_ORIGIN', 'Origen no permitido'))
                return
            if self.headers.get('Content-Type') != 'application/json':
                self.failure(415, ControlError('HTTP_TYPE', 'Formato no permitido'))
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 4096:
                    raise ValueError('Solicitud invalida')
                data = json.loads(self.rfile.read(length))
                if self.path == '/api/emergency':
                    if data != {}:
                        raise ValueError('Se requiere objeto vacio')
                    result = emergency.stop('Boton de emergencia')
                elif self.path in ('/api/shutdown', '/api/shutdown/confirm-gas'):
                    if data != {}:
                        raise ValueError('Se requiere objeto vacio')
                    result = shutdown.start() if self.path == '/api/shutdown' else shutdown.confirm_gas()
                elif self.path in ('/api/startup', '/api/startup/confirm-gas'):
                    if data != {}:
                        raise ValueError('Se requiere objeto vacio')
                    result = shutdown.manual(lambda: startup.start()) if self.path == '/api/startup' else shutdown.manual(lambda: startup.confirm_gas())
                elif self.path == '/api/mass-flow':
                    if not isinstance(data, dict) or set(data) not in ({'percent'}, {'sccm'}):
                        raise ValueError('Se requiere percent o sccm')
                    # Consigna manual deshabilitada; conservar MassControl para Emergency.
                    # Futuro: mass.set_sccm(data['sccm'])
                    def unavailable():
                        raise ControlError('INPUT', 'Manual Gas Flow Control no habilitado; proximamente para grupos futuros')
                    result = shutdown.manual(lambda: startup.manual(unavailable))
                else:
                    if not isinstance(data, dict) or set(data) != {'name', 'on'} or not isinstance(data['name'], str):
                        raise ValueError('Se requiere name y on')
                    result = shutdown.manual(lambda: startup.manual(lambda: control.set_manual_relay(data['name'], data['on'], pressures.read, temperatures.read)))

            except ControlError as exc:
                self.failure(400 if exc.code == 'INPUT' else 503, exc)
            except (ValueError, TypeError) as exc:
                self.failure(400, ControlError('INPUT', 'Solicitud invalida', repr(exc)))
            except Exception as exc:
                self.failure(503, exc)
            else:
                self.reply(200, result)
    return Handler


if __name__ == '__main__':
    from main_sim import run
    run()
