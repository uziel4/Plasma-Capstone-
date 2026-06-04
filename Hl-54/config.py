APP_TITLE = "PUPR PLASMA MOBILE REACTOR VACUUM CONTROLLER VER. 2.0"

# DAQC2plate configuration
DAQC2_ADDRESS = 0
DAQC2_CHANNEL = 0

# ============================================================
# HL-54 RELAY BOARD GPIO CONFIGURATION
# ============================================================
# Este relay board NO es I2C.
# Se controla directamente por GPIO desde la Raspberry Pi.
#
# Conexiones según tu tabla:
# K1 / X1 = GPIO 17 = Pin físico 11 = Mechanical Roughing Pump
# K3 / X3 = GPIO 22 = Pin físico 15 = Gas Mass Control Solenoid Valve
#
# Por ahora SOLO se usarán:
# - Roughing Pump
# - Gas Mass Control
# ============================================================

RELAY_ACTIVE_LOW = True

ROUGHING_GPIO = 17
MASS_FLOW_GPIO = 22

# Estas variables se dejan para que gui.py no se rompa.
# Ya no se usan para I2C.
RELAY_I2C_BUS = None
RELAY_I2C_ADDRESS = None

# Relay lógico usado por el GUI
ROUGHING_RELAY = 1
MASS_FLOW_RELAY = 2

# Control tuning
VACUUM_TOLERANCE = 0.05

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