"""Lee temperatura RTD por SPI. Configurar los parametros segun el cableado.

Dependencia: adafruit-circuitpython-max31865 (con Adafruit Blinka).
SPI: CLK=GPIO11, SDI=GPIO10, SDO=GPIO9. CS debe ser un GPIO libre.
SEN-30201-PT100: RTD nominal 100 ohmios, referencia 400 ohmios.
Conectar los puentes FRC/RTD segun las paginas 3-4 del datasheet SEN-30201.
Referencia: https://docs.circuitpython.org/projects/max31865/en/latest/api.html
"""
import argparse
import math
import time


def describir_fallas(fallas):
    # Orden de sensor.fault en la biblioteca Adafruit. Son causas posibles.
    mensajes = (
        "HIGHTHRESH: resistencia demasiado alta. Posible sensor desconectado; revise los 4 tornillos y la continuidad del PT100.",
        "LOWTHRESH: resistencia demasiado baja. Busque cables en corto o pares del PT100 mal conectados.",
        "REFINLOW: falla del circuito de referencia. Revise FRC+, cables sueltos y continuidad del sensor.",
        "REFINHIGH: falla del circuito de referencia. Revise FRC-, RTD- y posibles cortos a GND.",
        "RTDINLOW: falla en la entrada RTD. Revise RTD+, RTD- y cables tocando GND.",
        "OVUV: voltaje fuera de rango en las entradas. Revise VIN=3.3 V, GND comun y que los cables del PT100 no toquen alimentacion externa.",
    )
    if all(fallas):
        return ["TODAS LAS FALLAS ACTIVAS: posible lectura SPI incorrecta. Revise primero VIN/GND, CS=GPIO8 (pin 24), SDI=pin 19, SDO=pin 21 y SCLK=pin 23. No confirma que el sensor este danado."]
    return [mensaje for mensaje, activa in zip(mensajes, fallas) if activa]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rtd", type=int, choices=(100, 1000), default=100,
                        help="Resistencia nominal del RTD; predeterminado PT100.")
    parser.add_argument("--cables", type=int, choices=(2, 3, 4), default=4,
                        help="Numero de cables del RTD; predeterminado: 4.")
    parser.add_argument("--cs", type=int, choices=range(28), default=8,
                        help="GPIO BCM de CS; predeterminado GPIO8 (pin fisico 24).")
    parser.add_argument("--rref", type=float, default=400.0,
                        help="Referencia en ohmios; SEN-30201-PT100: 400.")
    args = parser.parse_args()
    if not math.isfinite(args.rref) or args.rref <= 0:
        parser.error("--rref debe ser positiva y finita.")
    if args.cs in (9, 10, 11):
        parser.error("CS no puede compartir los pines de datos/reloj SPI.")

    import board
    import digitalio
    import adafruit_max31865

    with board.SPI() as spi, digitalio.DigitalInOut(getattr(board, f"D{args.cs}")) as cs:
        sensor = adafruit_max31865.MAX31865(
            spi, cs, rtd_nominal=args.rtd, ref_resistor=args.rref,
            wires=args.cables, filter_frequency=60,
        )
        print("Lectura RTD en grados Celsius. Ctrl+C para terminar.")
        print(f"PT{args.rtd} | {args.cables} cables | CS GPIO{args.cs} | Rref {args.rref:g} ohm")
        while True:
            temperatura = sensor.temperature
            fallas = sensor.fault
            if any(fallas) or not math.isfinite(temperatura):
                print("\nERROR RTD - posibles causas (apague antes de mover cables):", flush=True)
                for mensaje in describir_fallas(fallas):
                    print(f"  - {mensaje}", flush=True)
                if not math.isfinite(temperatura):
                    print("  - Temperatura no valida: revise PT100, Rref y conexion del sensor.", flush=True)
                sensor.clear_faults()
            else:
                print(f"Temperatura: {temperatura:.2f} °C", flush=True)
            time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nLectura terminada.")
