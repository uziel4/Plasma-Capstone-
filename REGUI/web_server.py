import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from config import APP_TITLE
from app_logic import PlasmaController


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"


class VacuumRequestHandler(BaseHTTPRequestHandler):
    controller = None

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/state":
            self.send_json(self.controller.get_state())
            return

        if parsed.path in ("", "/"):
            self.send_static(WEB_ROOT / "index.html")
            return

        requested = (WEB_ROOT / parsed.path.lstrip("/")).resolve()
        if WEB_ROOT not in requested.parents and requested != WEB_ROOT:
            self.send_error(403)
            return

        if requested.is_file():
            self.send_static(requested)
            return

        self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        data = self.read_json()

        routes = {
            "/api/auto/start": lambda: self.controller.start_auto(),
            "/api/auto/stop": lambda: self.controller.stop_auto(),
            "/api/reset": lambda: self.controller.reset_system(),
            "/api/manual/roughing": lambda: self.controller.toggle_roughing(),
            "/api/manual/turbo": lambda: self.controller.toggle_turbo(),
            "/api/manual/mass-flow": lambda: self.controller.toggle_mass_flow(),
            "/api/hv/toggle": lambda: self.controller.toggle_hv(),
            "/api/hv/reset-timer": lambda: self.controller.reset_hv_timer(),
            "/api/hv/reset-voltage": lambda: self.controller.reset_hv_voltage(),
            "/api/target": lambda: self.controller.set_target(data.get("targetMtorr")),
            "/api/hv/voltage": lambda: self.controller.set_hv_voltage(data.get("voltage")),
            "/api/hv/timer": lambda: self.controller.set_timer(data.get("timer")),
        }

        action = routes.get(parsed.path)
        if action is None:
            self.send_error(404)
            return

        result = action()
        self.send_json({"ok": result is not False, "state": self.controller.get_state()})

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_static(self, path):
        body = path.read_bytes()
        content_type, _ = mimetypes.guess_type(str(path))
        self.send_response(200)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print("%s - %s" % (self.address_string(), format % args))


def run(host="0.0.0.0", port=8000):
    controller = PlasmaController()
    VacuumRequestHandler.controller = controller
    server = ThreadingHTTPServer((host, port), VacuumRequestHandler)

    print(f"{APP_TITLE}")
    print(f"Open http://localhost:{port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        controller.close()
        server.server_close()


if __name__ == "__main__":
    run()
