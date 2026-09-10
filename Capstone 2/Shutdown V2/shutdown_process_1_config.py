
# Modos de operación
AUTOMATIC_MODE = False


#Espera el proceso en segundos
MAX_SENSOR_CHECKS = 900

# --- VARIABLES PARA SECUENCIA DE SHUTDOWN ---

# Tiempos de espera
INJECTION_VALVE_WAIT_SECONDS = 10 #120 seconds
DIFFUSION_COOLDOWN_RECHECK_SECONDS = 5

# Límites de seguridad para apagado
MAX_SAFE_DIFFUSION_TEMP_C = 37.78  # Equivalente a 100 °F

# Variables para simulación de enfriamiento de bombas
SIM_SHUTDOWN_INITIAL_DIFFUSION_TEMP_C = 200.0
SIM_DIFFUSION_PUMP_COOLING_STEP_C = 15.0