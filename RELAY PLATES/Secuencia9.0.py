#!/usr/bin/env python3
"""Efecto Knight Rider en la Pi-Plates RELAYplate2 con address 0."""

import argparse
import time

try:
    import piplates.RELAYplate2 as RELAY2
except ImportError as exc:
    raise SystemExit(
        "No se encontro la libreria Pi-Plates. Instalala con: "
        "python3 -m pip install Pi-Plates"
    ) from exc


PLATE_ADDRESS = 0
FIRST_RELAY = 1
LAST_RELAY = 8


def knight_rider(delay: float, cycles: int) -> None:
    """Recorre K1..K8..K1; cycles=0 mantiene el efecto continuamente."""
    board_id = RELAY2.getID(PLATE_ADDRESS)
    if "RELAYplate2" not in str(board_id):
        raise RuntimeError(
            "No se encontro una RELAYplate2 en la direccion "
            f"{PLATE_ADDRESS}: {board_id!r}"
        )

    sequence = list(range(FIRST_RELAY, LAST_RELAY + 1)) + list(
        range(LAST_RELAY - 1, FIRST_RELAY, -1)
    )

    RELAY2.relayALL(PLATE_ADDRESS, 0)
    completed = 0

    try:
        while cycles == 0 or completed < cycles:
            for relay in sequence:
                RELAY2.relayON(PLATE_ADDRESS, relay)
                print(f"\rRelay K{relay} encendido", end="", flush=True)
                time.sleep(delay)
                RELAY2.relayOFF(PLATE_ADDRESS, relay)
            completed += 1
    finally:
        # Siempre deja todos los contactos abiertos al terminar.
        RELAY2.relayALL(PLATE_ADDRESS, 0)
        print("\nTodos los relays quedaron apagados.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Knight Rider en los 8 relays de la placa address 0."
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.20,
        help="segundos que permanece encendido cada relay (default: 0.20)",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=0,
        help="cantidad de ciclos; 0 significa continuo (default: 0)",
    )
    args = parser.parse_args()

    if args.delay <= 0:
        parser.error("--delay debe ser mayor que 0")
    if args.cycles < 0:
        parser.error("--cycles no puede ser negativo")
    return args


def main() -> None:
    args = parse_args()
    print(
        f"RELAYplate2 address={PLATE_ADDRESS}, delay={args.delay}s. "
        "Presiona Ctrl+C para detener."
    )
    try:
        knight_rider(args.delay, args.cycles)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        raise SystemExit(f"Error comunicando con la RELAYplate2: {exc}") from exc


if __name__ == "__main__":
    main()
