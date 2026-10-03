"""Backend exclusivamente simulado; reutiliza las reglas del producto."""
import json
import signal
from http.server import ThreadingHTTPServer
from main import handler_for
from emergency_shutdown import EmergencyShutdown
from planta import Planta
from manual_control import ManualControl
from temperaturas import Temperaturas
from presiones import Presiones
from masscontroll import MassControl
from alarma_room import RoomAlarm


def build():
    plant = Planta()
    control = ManualControl(plant)
    mass = MassControl()
    emergency = EmergencyShutdown(control,mass)
    temperatures = Temperaturas(plant)
    alarm = RoomAlarm(control,temperatures,emergency).start()
    base = handler_for(control,temperatures,Presiones(plant),mass,emergency,alarm)
    # La GUI y el panel de pruebas viven en Node-RED (build_dashboards.py); aquí solo la API.
    class Handler(base):
        def do_POST(self):
            if self.path != '/api/simulation': return super().do_POST()
            try:
                if self.headers.get('Origin') not in (None,'http://'+self.headers.get('Host','')):
                    raise ValueError('Origen no permitido')
                size = int(self.headers.get('Content-Length',0))
                if not 0 < size <= 4096: raise ValueError('Longitud invalida')
                result = plant.configure(json.loads(self.rfile.read(size)))
                self.reply(200,result)
            except Exception as exc: self.failure(400,exc)
    return Handler,emergency

def run():
    handler,emergency = build()
    class SimServer(ThreadingHTTPServer):
        request_queue_size = 64
    server = SimServer(('127.0.0.1',8001),handler)
    def stop(*args): raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,stop)
    print('Backend SIMULADO http://127.0.0.1:8001',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally:
        emergency.stop('Cierre de simulacion')
        server.server_close()

if __name__ == '__main__':
    run()
