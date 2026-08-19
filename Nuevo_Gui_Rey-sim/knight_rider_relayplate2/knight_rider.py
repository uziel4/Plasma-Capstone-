#!/usr/bin/env python3
"""Efecto Knight Rider para una Pi-Plates RELAYplate2."""

import argparse
import time

try:
    import piplates.RELAYplate2 as RELAY2
except ImportError as exc:
    raise SystemExit(
        "No se encontro la libreria piplates. Instalala con: "
        "python3 -m pip install piplates"
    ) from exc


FIRST_RELAY = 1
LAST_RELAY = 7


def knight_rider(address: int, delay: float, cycles: int) -> None:
    """Recorre K1..K7..K1; cycles=0 mantiene el efecto indefinidamente."""
    board_id = RELAY2.getID(address)
    if "RELAYplate2" not in str(board_id):
        raise RuntimeError(
            f"No se encontro una RELAYplate2 en la direccion {address}: {board_id!r}"
        )

    # No repetir K1/K7 al cambiar de direccion produce un movimiento uniforme.
    sequence = list(range(FIRST_RELAY, LAST_RELAY + 1)) + list(
        range(LAST_RELAY - 1, FIRST_RELAY, -1)
    )

    RELAY2.relayALL(address, 0)
    completed = 0

    try:
        while cycles == 0 or completed < cycles:
            for relay in sequence:
                RELAY2.relayON(address, relay)
                print(f"\rRelay K{relay} encendido", end="", flush=True)
                time.sleep(delay)
                RELAY2.relayOFF(address, relay)
            completed += 1
    finally:
        # Siempre dejar todos los contactos abiertos al salir o si ocurre un error.
        RELAY2.relayALL(address, 0)
        print("\nTodos los relays quedaron apagados.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Barrido Knight Rider en los 7 relays de una RELAYplate2."
    )
    parser.add_argument(
        "--address",
        type=int,
        default=0,
        choices=range(8),
        metavar="0-7",
        help="direccion configurada con los jumpers (default: 0)",
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
        f"RELAYplate2 address={args.address}, delay={args.delay}s. "
        "Presiona Ctrl+C para detener."
    )
    try:
        knight_rider(args.address, args.delay, args.cycles)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        raise SystemExit(f"Error comunicando con la RELAYplate2: {exc}") from exc


if __name__ == "__main__":
    main()
