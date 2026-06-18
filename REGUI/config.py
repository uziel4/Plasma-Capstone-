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

RELAY_ACTIVE_LOW = False

# GPIO 17 | Pin físico 11 | IN1 | Mechanical Roughing Pump
ROUGHING_GPIO = 5

# GPIO 27 | Pin físico 15 | IN3 | Gas Mass Control Solenoid Valve
MASS_FLOW_GPIO = 6

# Relays lógicos usados por gui.py
ROUGHING_RELAY = 1
MASS_FLOW_RELAY = 2

# Control tuning
VACUUM_TOLERANCE = 0.05

# Simulación
SIM_INITIAL_TORR = 1.450e-1

# Colores GUI
COLORS = {
    "background": "#070a12",
    "panel": "#101722",
    "panel_light": "#151f2e",
    "panel_soft": "#1b2a3d",

    "button": "#2563eb",
    "button_hover": "#3b82f6",
    "button_active": "#dc2626",

    "white": "#f8fafc",
    "muted": "#a7b4c7",
    "input": "#dbeafe",
    "black": "#020617",

    "red": "#ef4444",
    "red_dark": "#991b1b",
    "green": "#22c55e",
    "green_dark": "#166534",
    "yellow": "#f59e0b",
    "gray": "#6b7280",

    "accent": "#38bdf8",
    "grid": "#2d3a4f",
    "graph_line": "#2dd4bf",
    "graph_marker": "#f8fafc",
}
