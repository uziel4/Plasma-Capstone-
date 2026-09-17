
from __future__ import annotations
import piplates.ADCplate as ADC
import time


ADC_ADDRESS = 0  # Dirección de la placa ADC 

# Define el rango de tu sensor aquí:
RANGO_MIN = 0    # PSI a 4mA
RANGO_MAX = 100  # PSI a 20mA

def calcular_psi(current_mA):
     
    current_mA = ADC.getADC(ADC_ADDRESS, 'I0')
    if not (4 <= current_mA <= 20):
        raise ValueError("La señal debe estar en el rango estándar de 4 a 20 mA.")
        # Aplicar la fórmula de interpolación lineal
        psi = RANGO_MIN + ((current_mA - 4) / 16)*(RANGO_MAX - RANGO_MIN)
        return psi
        
ADC.initADC(ADC_ADDRESS)
print(ADC.getID(ADC_ADDRESS))

while True:
        #convert mA to PSI
        presure_psi = calcular_psi(current_mA)
        print(f"I0: {current_mA:.2f} mA | Pressure: {presure_psi:.2f} PSI")
        time.sleep(1)  # Espera 1 segundo antes de la siguiente lectura


def main() -> None:
    try:
        pressure = calcular_psi(current_mA)
        main()
    except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
