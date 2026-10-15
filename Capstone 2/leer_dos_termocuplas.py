#!/usr/bin/env python3
"""Prueba independiente de las 8 termocuplas de la THERMOplate.

Usa la misma configuracion que "Node-RED final no bloqueos/temperaturas.py":
    THERMOplate address 2, frecuencia de linea 60 Hz.
    Canales 1-8: termocuplas tipo K (ver tabla TERMOCUPLAS).

Muestra las lecturas en el terminal. Por defecto lee las 8 termocuplas.
Para leer solo algunas:
    python3 leer_dos_termocuplas.py --canales 4 5

El programa solamente lee temperaturas; no acciona ningun rele.
Detenga el backend de Node-RED (main.py) antes de usarlo, para que los dos
programas no usen la placa al mismo tiempo (si no, sale "GPIO busy").
Detengalo de forma segura con Ctrl+C.
"""

from __future__ import annotations

import argparse
import time

# Igual que en Node-RED final no bloqueos/temperaturas.py (canal 8 no se usa alli)
THERMO_ADDRESS = 2
LINE_FREQUENCY = 60
# Equipo: (canal, tipo)
TERMOCUPLAS = {
    'Coolant': (1, 'k'),
    'Cool Trap A': (2, 'k'),
    'Cool Trap B': (3, 'k'),
    'Diffusion Pump A': (4, 'k'),
    'Diffusion Pump B': (5, 'k'),
    'Field Magnet A': (6, 'k'),
    'Field Magnet B': (7, 'k'),
    'Canal 8': (8, 'k'),
}


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Muestra continuamente las 8 termocuplas de la THERMOplate (config. Node-RED)."
    )
    parser.add_argument(
        "--canales", type=int, nargs="+", default=None,
        help="Canales a leer (1-8). Por defecto: todos.",
    )
    parser.add_argument(
        "--intervalo", type=float, default=1.0, help="Segundos entre lecturas (minimo 1)."
    )
    return parser.parse_args()


def sensores_seleccionados(canales: list[int] | None) -> list[tuple[str, int, str]]:
    todos = [(name, channel, kind) for name, (channel, kind) in TERMOCUPLAS.items()]
    if canales is None:
        return todos
    validos = {channel for _, channel, _ in todos}
    invalidos = sorted(set(canales) - validos)
    if invalidos:
        raise SystemExit(
            f"ERROR: canales no validos: {invalidos}. Validos: {sorted(validos)}."
        )
    return [s for s in todos if s[1] in set(canales)]


def leer_celsius(thermo, canal: int) -> str:
    """Devuelve la lectura tal como la da la placa, o '--' si no respondio."""
    try:
        return f"{float(thermo.getTEMP(THERMO_ADDRESS, canal, 'c')):7.2f} °C"
    except Exception:
        return "     --"


def main() -> None:
    config = argumentos()
    if config.intervalo < 1.0:
        raise SystemExit("ERROR: --intervalo debe ser de al menos 1 segundo.")
    sensores = sensores_seleccionados(config.canales)

    try:
        import piplates.THERMOplate as THERMO
    except (ImportError, ModuleNotFoundError) as exc:
        raise SystemExit(
            "ERROR: no se encontro la libreria Pi-Plates.\n"
            "Instalela en la Raspberry Pi con:\n"
            "  python3 -m pip install Pi-Plates"
        ) from exc

    # Puerto Rico/EE. UU. usa una frecuencia electrica de 60 Hz.
    # Se configuran las 8, aunque solo se lean algunas.
    try:
        THERMO.setLINEFREQ(THERMO_ADDRESS, LINE_FREQUENCY)
    except Exception:
        pass
    for name, (channel, kind) in TERMOCUPLAS.items():
        try:
            THERMO.setTYPE(THERMO_ADDRESS, channel, kind)
        except Exception:
            pass

    print(f"THERMOplate address {THERMO_ADDRESS}")
    for name, channel, kind in sensores:
        print(f"  Canal {channel}: {name} ({kind.upper()})")
    print(f"Leyendo cada {config.intervalo:g} s. Presione Ctrl+C para terminar.\n")

    try:
        while True:
            hora = time.strftime("%Y-%m-%d %H:%M:%S")
            print(hora, flush=True)
            for name, channel, kind in sensores:
                print(f"  Canal {channel} {name:<17}: {leer_celsius(THERMO, channel)}", flush=True)
            print(flush=True)
            time.sleep(config.intervalo)
    except KeyboardInterrupt:
        print("\nLectura terminada por el usuario.")


if __name__ == "__main__":
    main()
