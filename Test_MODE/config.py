# ============================================================
# config.py
# Archivo central de configuración del sistema.
# Aquí ajustas el título, tamaño de ventana, colores,
# modo de prueba, DAQC2plate, relays y lógica de control.
# ============================================================

# Título principal que aparece en la parte superior del GUI
APP_TITLE = "PUPR PLASMA MOBILE REACTOR VACUUM CONTROLLER VER. 2.0"

# Tamaño de la ventana principal
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 950

# ============================================================
# TEST MODE
# ============================================================
# "AUTO"  = intenta usar hardware real; si falla, usa simulación
# True    = fuerza simulación siempre, ideal para Mac/Windows
# False   = fuerza hardware real, ideal para Raspberry Pi
#
# Para ver el GUI en tu Mac:
# TEST_MODE = True
#
# Para Raspberry Pi:
# TEST_MODE = "AUTO" o False
# ============================================================
TEST_MODE = "AUTO"

# ============================================================
# DAQC2plate
# ============================================================
# address = dirección del DAQC2plate
# channel = canal analógico usado
#
# En tu caso el sensor 972B está conectado a A0.
# A0 normalmente corresponde a channel 0.
# ============================================================
DAQC2_ADDRESS = 0
DAQC2_CHANNEL = 0

# ============================================================
# 8 Relay Module I2C
# ============================================================
# Estos valores vienen del código tipo Knight Rider.
# El módulo usa bus I2C 1 y dirección 0x21.
# ============================================================
RELAY_I2C_BUS = 1
RELAY_I2C_ADDRESS = 0x21

# ============================================================
# Relay assignment
# ============================================================
# Relay 1 = Roughing Pump
# Relay 2 = Mass Flow Controller / Mass Flow Valve
#
# Si después cableas la bomba en otro relay, cambias esto.
# Ejemplo: si la bomba está en Relay 3:
# ROUGHING_RELAY = 3
# ============================================================
ROUGHING_RELAY = 1
MASS_FLOW_RELAY = 2

# ============================================================
# Control tuning
# ============================================================
# Tolerancia alrededor del target.
# 0.05 = 5%
#
# Ejemplo:
# Si el target es 1.000 mTorr = 1e-3 Torr,
# el sistema acepta un margen de ±5%.
# ============================================================
VACUUM_TOLERANCE = 0.05

# ============================================================
# Seguridad visual / simulación
# ============================================================
# Presión inicial usada cuando estás en TEST MODE.
# Se usa para simular la cámara antes de bombear.
# ============================================================
SIM_INITIAL_TORR = 1.450e-1

# ============================================================
# Colores del GUI
# ============================================================
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