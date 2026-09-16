#!/usr/bin/env python3
"""Prueba independiente de dos termocuplas en una Pi-Plates THERMOplate.

Configuracion usada por defecto en este proyecto:
    THERMOplate address 2, canales 5 y 8, termocuplas tipo K.

El programa solamente lee temperaturas; no acciona ningun rele.
Detengalo de forma segura con Ctrl+C.
"""

from __future__ import annotations

import argparse
import math
import time


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Muestra continuamente dos temperaturas de una THERMOplate."
    )
    parser.add_argument("--address", type=int, default=2, help="Address de la placa (0-7).")
    parser.add_argument("--canal-1", type=int, default=5, help="Canal de la termocupla 1 (1-8).")
    parser.add_argument("--canal-2", type=int, default=8, help="Canal de la termocupla 2 (1-8).")
    parser.add_argument(
        "--tipo", choices=("k", "j"), default="k", help="Tipo de termocupla: k o j."
    )
    parser.add_argument(
        "--intervalo", type=float, default=1.0, help="Segundos entre lecturas (minimo 1)."
    )
    return parser.parse_args()


def validar(config: argparse.Namespace) -> None:
    if not 0 <= config.address <= 7:
        raise SystemExit("ERROR: --address debe estar entre 0 y 7.")
    if config.canal_1 == config.canal_2:
        raise SystemExit("ERROR: seleccione dos canales diferentes.")
    for nombre, canal in (("--canal-1", config.canal_1), ("--canal-2", config.canal_2)):
        if not 1 <= canal <= 8:
            raise SystemExit(f"ERROR: {nombre} debe estar entre 1 y 8.")
    if config.intervalo < 1.0:
        raise SystemExit("ERROR: --intervalo debe ser de al menos 1 segundo.")


def leer_celsius(thermo, address: int, canal: int) -> float:
    valor = float(thermo.getTEMP(address, canal, "c"))
    if not math.isfinite(valor):
        raise ValueError("la placa devolvio un valor no numerico")
    return valor


def main() -> None:
    config = argumentos()
    validar(config)

    try:
        import piplates.THERMOplate as THERMO
    except (ImportError, ModuleNotFoundError) as exc:
        raise SystemExit(
            "ERROR: no se encontro la libreria Pi-Plates.\n"
            "Instalela en la Raspberry Pi con:\n"
            "  python3 -m pip install Pi-Plates"
        ) from exc

    try:
        identificacion = THERMO.getID(config.address)
        if "THERMO" not in str(identificacion).upper():
            raise RuntimeError(f"respuesta inesperada: {identificacion!r}")

        # Puerto Rico/EE. UU. usa una frecuencia electrica de 60 Hz.
        THERMO.setLINEFREQ(config.address, 60)
        THERMO.setTYPE(config.address, config.canal_1, config.tipo)
        THERMO.setTYPE(config.address, config.canal_2, config.tipo)
    except Exception as exc:
        raise SystemExit(
            f"ERROR: no se pudo configurar la THERMOplate address {config.address}: {exc}\n"
            "Revise los jumpers de address, el montaje de la placa y que SPI este habilitado."
        ) from exc

    print(f"Placa detectada: {identificacion}")
    print(
        f"Leyendo tipo {config.tipo.upper()} en canales "
        f"{config.canal_1} y {config.canal_2} cada {config.intervalo:g} s."
    )
    print("Presione Ctrl+C para terminar.\n")

    try:
        while True:
            hora = time.strftime("%Y-%m-%d %H:%M:%S")
            try:
                temp_1 = leer_celsius(THERMO, config.address, config.canal_1)
                temp_2 = leer_celsius(THERMO, config.address, config.canal_2)
                print(
                    f"{hora} | Canal {config.canal_1}: {temp_1:8.2f} °C | "
                    f"Canal {config.canal_2}: {temp_2:8.2f} °C",
                    flush=True,
                )
            except Exception as exc:
                print(f"{hora} | ERROR DE LECTURA: {exc}", flush=True)
            time.sleep(config.intervalo)
    except KeyboardInterrupt:
        print("\nLectura terminada por el usuario.")


if __name__ == "__main__":
    main()
