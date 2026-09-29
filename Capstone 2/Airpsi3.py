from __future__ import annotations
import time
import math

# Configuración de la placa y rangos del sensor
ADC_ADDRESS = 3  # Dirección de la placa ADC
RANGO_MAX = 232  # PSI a 20 mA: confirmar con la etiqueta del sensor.

def calcular_psi(current_mA: float) -> float:

    if not math.isfinite(current_mA):
        raise ValueError("Corriente no valida")
    return max(0.0, ((current_mA - 4.0) / 16.0) * RANGO_MAX)

def main() -> None:
    import piplates.ADCplate as ADC

    # Inicialización de la placa ADC
    ADC.initADC(ADC_ADDRESS)
    time.sleep(1)
    print(f"Placa ADC inicializada. ID: {ADC.getID(ADC_ADDRESS)}")

    print("Iniciando lectura continua...")
    while True:
        try:
            # 1. Obtener la lectura actual del canal "I3"=15 (0-15)
            current_mA = ADC.getADC(ADC_ADDRESS, 'I3')

             # 2. Convertir mA a PSI
            pressure_psi = calcular_psi(current_mA)

            # 2. Mostrar resultados
            print(f"I3: {current_mA:.3f} mA | Pressure: {pressure_psi:.2f} PSI")
            if not 4.0 <= current_mA <= 20.0:
                print("AVISO: senal fuera de 4-20 mA; presion no confiable.")
            
        except Exception as e:
            # Captura errores de hardware o comunicación con la placa
            print(f"Error de hardware/lectura: {e}")
            
        time.sleep(1)  # Espera 1 segundo antes de la siguiente lectura

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nMedicion terminada.")
