"""Backend Python del producto final (Pi-Plates). Con Node-RED: npm start (lanza main.py --port 8000 --no-browser)."""
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--no-browser', action='store_true', help='No abrir el navegador; la GUI la sirve Node-RED')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('--port debe estar entre 1 y 65535')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    try:
        (ROOT / 'logs').mkdir(exist_ok=True)
        handler = RotatingFileHandler(ROOT / 'logs/control.log', maxBytes=1000000, backupCount=3)
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        logging.getLogger().addHandler(handler)
    except OSError as exc:
        logging.warning('No se puede guardar logs/control.log: %r. Diagnosticos disponibles en terminal.', exc)
    try:
        control = ManualControl()
        mass = MassControl()
        emergency = EmergencyShutdown(control, mass)
        try:
            temperatures = Temperaturas()
            alarm = RoomAlarm(control, temperatures, emergency)
            server = ThreadingHTTPServer(('127.0.0.1', args.port), handler_for(control, temperatures, Presiones(), mass, emergency, alarm))
        except OSError as exc:
            raise ControlError('SERVER_BIND', 'No se pudo abrir el servidor', repr(exc), puerto=args.port) from exc
    except Exception as exc:
        error = exc if isinstance(exc, ControlError) else ControlError('INTERNAL', 'Fallo de arranque', repr(exc))
        if 'emergency' in locals():
            emergency.stop('Fallo de arranque del servidor')
        logging.exception('%s', error)
        raise SystemExit(1)
    alarm.start()  # Revisa Room cada 2 s aunque no haya un GUI abierto
    url = f"http://127.0.0.1:{args.port}"
    print(f"{url} | Control de reles conectado", flush=True)
    def abrir_gui():
        try:
            if not webbrowser.open(url):
                raise RuntimeError('El navegador no acepto la apertura')
        except Exception as exc:
            logging.error('%s', ControlError('BROWSER', 'El servidor funciona, pero no se pudo abrir el navegador', repr(exc), url=url))
    if not args.no_browser:
        threading.Thread(target=abrir_gui, daemon=True).start()
    def terminate(signum, frame):
        raise SystemExit(128 + signum)
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, terminate)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        # Evitar que una segunda señal interrumpa el intento de apagado.
        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            signal.signal(sig, signal.SIG_IGN)
        try:
            emergency.stop('Cierre de main.py')
        finally:
            server.server_close()
