"""Escanea I2C bus 1 en Raspberry Pi. MAX31865 y Pi-Plates usan SPI."""
import shutil
import subprocess

if __name__ == "__main__":
    if not shutil.which("i2cdetect"):
        raise SystemExit("Instala la herramienta: sudo apt install i2c-tools")
    print("Escaneo I2C bus 1. El MAX31865 no aparece porque usa SPI.", flush=True)
    try:
        raise SystemExit(subprocess.call(["i2cdetect", "1"]))
    except KeyboardInterrupt:
        print("\nEscaneo cancelado.")
