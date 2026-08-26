# ============================================================
# test_hl54_relays.py
# Prueba rápida del HL-54:
# 1) Prende GPIO 17 / IN1 por 2 segundos
# 2) Prende GPIO 22 / IN3 por 2 segundos
# 3) Apaga todo
# ============================================================

import time
from relay_controller import RelayController

relay = RelayController(test_mode=False)

try:
    print("Prendiendo IN1 / GPIO 17 / Roughing Pump")
    relay.set_relay(1, True)
    time.sleep(2)
    relay.set_relay(1, False)

    print("Prendiendo IN3 / GPIO 22 / Mass Flow Solenoid")
    relay.set_relay(2, True)
    time.sleep(2)
    relay.set_relay(2, False)

    print("Apagando todo")
    relay.all_off()

finally:
    relay.close()
