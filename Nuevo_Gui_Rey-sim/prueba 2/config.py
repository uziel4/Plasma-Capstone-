# ============================================================
# config.py
# Configuración para HL-54 Relay Board usando GPIO directo
# ============================================================

APP_TITLE = "PUPR PLASMA MOBILE REACTOR VACUUM CONTROLLER VER. 2.0"

# Ventana GUI
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768

# Modo de prueba
# "AUTO" = intenta hardware real, si falla usa simulación
# True = simulación
# False = hardware real obligatorio
TEST_MODE = False
# DAQC2plate
DAQC2_ADDRESS = 0
DAQC2_CHANNEL = 0

# Estos se dejan para que gui.py no falle aunque HL-54 NO usa I2C
RELAY_I2C_BUS = 1
RELAY_I2C_ADDRESS = 0x21

# ============================================================
# HL-54 GPIO RELAYS
# ============================================================

RELAY_ACTIVE_LOW = True

# GPIO 17 | Pin físico 11 | IN1 | Mechanical Roughing Pump
ROUGHING_GPIO = 17

# GPIO 27 | Pin físico 15 | IN3 | Gas Mass Control Solenoid Valve
MASS_FLOW_GPIO = 27

# Relays lógicos usados por gui.py
ROUGHING_RELAY = 1
MASS_FLOW_RELAY = 2

# Control tuning
VACUUM_TOLERANCE = 0.05

# Simulación
SIM_INITIAL_TORR = 1.450e-1

# Colores GUI
COLORS = {
    "background": "#050814",
    "panel": "#0b1220",
    "panel_light": "#111827",
    "panel_soft": "#162033",

    "button": "#1d4ed8",
    "button_hover": "#2563eb",
    "button_active": "#dc2626",

    "white": "#f8fafc",
    "muted": "#94a3b8",
    "input": "#e0f2fe",
    "black": "#020617",

    "red": "#ef4444",
    "green": "#22c55e",
    "yellow": "#facc15",
    "gray": "#64748b",

    "grid": "#334155",
    "graph_line": "#38bdf8",
    "graph_marker": "#f8fafc",
}
