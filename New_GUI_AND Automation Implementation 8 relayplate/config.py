APP_TITLE = "PUPR PLASMA MOBILE REACTOR VACUUM CONTROLLER VER. 2.0"

WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 950

# DAQC2plate configuration
DAQC2_ADDRESS = 0
DAQC2_CHANNEL = 0

# 8 Relay Module I2C configuration
RELAY_I2C_BUS = 1
RELAY_I2C_ADDRESS = 0x21

# Relay assignment
ROUGHING_RELAY = 1       # Relay 1
MASS_FLOW_RELAY = 2      # Relay 2

# Control tuning
VACUUM_TOLERANCE = 0.05  # 5% tolerance around target

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