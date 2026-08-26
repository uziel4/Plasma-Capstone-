#!/usr/bin/env python3
"""Detecta placas Pi-Plates y dispositivos I2C sin activar salidas."""

from __future__ import annotations

import argparse
import importlib
import os
from typing import Any


PIPLATE_MODULES = (
    "DAQC2plate",
    "DAQCplate",
    "RELAYplate2",
    "RELAYplate",
    "THERMOplate",
    "TINKERplate",
    "MOTORplate",
    "ADCplate",
    "CURRENTplate",
)


def _safe_call(module: Any, function_name: str, address: int) -> Any:
    function = getattr(module, function_name, None)
    if not callable(function):
        return None
    try:
        return function(address)
    except Exception:
        return None


def scan_piplates() -> int:
    """Busca direcciones lógicas Pi-Plates de 0 a 7."""
    modules = []
    for name in PIPLATE_MODULES:
        try:
            modules.append(importlib.import_module(f"piplates.{name}"))
        except (ImportError, ModuleNotFoundError):
            continue

    if not modules:
        print("No se encontró el paquete Pi-Plates.")
        print("Instálalo en la Raspberry Pi con: python3 -m pip install Pi-Plates")
        return 1

    found: dict[int, dict[str, Any]] = {}
    for address in range(8):
        for module in modules:
            reported_address = _safe_call(module, "getADDR", address)
            if reported_address != address:
                continue

            plate_id = _safe_call(module, "getID", address)
            found[address] = {
                "id": plate_id if plate_id is not None else "Pi-Plate (modelo desconocido)",
                "hw": _safe_call(module, "getHWrev", address),
                "fw": _safe_call(module, "getFWrev", address),
            }
            break

    print("\nDirecciones lógicas del stack Pi-Plates (jumpers 0-7)")
    print("----------------------------------------------------")
    if not found:
        print("No se detectaron placas.")
        return 2

    for address, info in found.items():
        details = []
        if info["hw"] is not None:
            details.append(f"HW {info['hw']}")
        if info["fw"] is not None:
            details.append(f"FW {info['fw']}")
        suffix = f" ({', '.join(details)})" if details else ""
        print(f"Dirección {address}: {info['id']}{suffix}")
    return 0


def scan_i2c(bus_number: int) -> int:
    """Busca direcciones físicas I2C; no escribe registros de configuración."""
    try:
        import smbus2
    except ImportError:
        print("No se encontró smbus2. Instálalo con: python3 -m pip install smbus2")
        return 1

    device = f"/dev/i2c-{bus_number}"
    if not os.path.exists(device):
        print(f"No existe {device}. Verifica que I2C esté habilitado.")
        return 1

    detected = []
    try:
        with smbus2.SMBus(bus_number) as bus:
            for address in range(0x03, 0x78):
                try:
                    bus.write_quick(address)
                except OSError:
                    continue
                detected.append(address)
    except PermissionError:
        print(f"Sin permiso para abrir {device}; prueba ejecutándolo con sudo.")
        return 1

    print(f"\nDirecciones físicas en I2C bus {bus_number}")
    print("----------------------------------")
    if detected:
        print("  ".join(f"0x{address:02X}" for address in detected))
    else:
        print("No se detectaron dispositivos I2C.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detecta placas del stack Pi-Plates y dispositivos I2C."
    )
    parser.add_argument(
        "--i2c",
        action="store_true",
        help="también escanea las direcciones físicas del bus I2C",
    )
    parser.add_argument("--bus", type=int, default=1, help="bus I2C (predeterminado: 1)")
    args = parser.parse_args()

    result = scan_piplates()
    if args.i2c:
        i2c_result = scan_i2c(args.bus)
        if result == 0:
            result = i2c_result
    return result


if __name__ == "__main__":
    raise SystemExit(main())
