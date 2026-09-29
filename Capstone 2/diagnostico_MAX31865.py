"""Prueba directa SPI0/CE0: CS en GPIO8, pin fisico 24.

Ejecutar con leer_MAX31865.py detenido. No necesita un PT100 conectado
para comprobar la lectura/escritura del registro de configuracion.
Dependencia: spidev. No acciona las placas de reles.
"""
import time


def probar(spi):
    def leer(registro):
        # Direccion y respuesta en una transferencia: CE0 permanece activo.
        return spi.xfer2([registro & 0x7F, 0x00])[1]

    def escribir(valor):
        spi.xfer2([0x80, valor])

    original = leer(0x00)
    print(f"Configuracion inicial: 0x{original:02X}", flush=True)
    correcto = True
    try:
        for esperado in (0x00, 0x80, 0x00):
            escribir(esperado)
            time.sleep(0.02)
            recibido = leer(0x00)
            coincide = recibido == esperado
            correcto = correcto and coincide
            print(f"Escrito 0x{esperado:02X} | Leido 0x{recibido:02X} | "
                  f"{'OK' if coincide else 'FALLO'}", flush=True)
    finally:
        # Restaurar opciones persistentes, sin disparar conversion/diagnostico.
        escribir(original & 0xD1)
    if correcto:
        print("SPI OK: el registro responde. Si Blinka falla, revisar su manejo de CS.")
        print("Esta prueba no valida el PT100 ni su conexion.")
    else:
        print("SPI FALLO: no se pudo verificar la configuracion del modulo.")
        print("La prueba no distingue entre alimentacion, conexion, bus o modulo.")
    return correcto


if __name__ == "__main__":
    import spidev

    spi = spidev.SpiDev()
    try:
        spi.open(0, 0)
        spi.max_speed_hz = 100000
        spi.mode = 1
        spi.no_cs = False
        raise SystemExit(0 if probar(spi) else 1)
    finally:
        spi.close()
