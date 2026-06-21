import json
import signal
import time

import paho.mqtt.client as mqtt

from app_logic import PlasmaController

BROKER_HOST = "localhost"
BROKER_PORT = 1883
CMD_TOPIC = "plasma/cmd"
STATE_TOPIC = "plasma/state"
STATE_INTERVAL_SECONDS = 0.5

controller = PlasmaController()
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
running = True


def publish_state():
    state = controller.get_state()
    client.publish(STATE_TOPIC, json.dumps(state), retain=True)


def handle_command(payload):
    action = payload.get("action")
    value = payload.get("value")

    if action == "auto_start":
        controller.start_auto()
    elif action == "auto_stop":
        controller.stop_auto()
    elif action == "reset":
        controller.reset_system()
    elif action == "toggle_roughing":
        controller.toggle_roughing()
    elif action == "toggle_turbo":
        controller.toggle_turbo()
    elif action == "toggle_mass_flow":
        controller.toggle_mass_flow()
    elif action == "toggle_hv":
        controller.toggle_hv()
    elif action == "reset_hv_timer":
        controller.reset_hv_timer()
    elif action == "reset_hv_voltage":
        controller.reset_hv_voltage()
    elif action == "set_target":
        controller.set_target(value)
    elif action == "set_hv_voltage":
        controller.set_hv_voltage(value)
    elif action == "set_timer":
        controller.set_timer(value)
    else:
        print(f"Unknown command: {payload}")

    publish_state()


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected to MQTT broker: {reason_code}")
    client.subscribe(CMD_TOPIC)
    publish_state()


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        handle_command(payload)
    except Exception as error:
        print(f"MQTT command error: {error}")


def shutdown(*_):
    global running
    running = False


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER_HOST, BROKER_PORT, 60)
client.loop_start()

print("Plasma MQTT controller running")
print(f"Commands: {CMD_TOPIC}")
print(f"State:    {STATE_TOPIC}")

try:
    while running:
        publish_state()
        time.sleep(STATE_INTERVAL_SECONDS)
finally:
    print("Shutting down plasma controller...")
    controller.close()
    client.loop_stop()
    client.disconnect()
