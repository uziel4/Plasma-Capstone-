#!/usr/bin/env python3
"""Secuencia inicial del sistema de plasma con dos RELAYplate2.

La presión y la temperatura se simulan en el terminal. Este programa todavía
no recibe datos de las placas ADC y THERMO.
"""

import time

try:
    import piplates.RELAYplate2 as RELAY2
except ImportError as exc:
    raise SystemExit(
        "No se encontró la librería Pi-Plates. Instálala con: "
        "python3 -m pip install Pi-Plates"
    ) from exc


# Configuración del proceso. Todos los tiempos están expresados en segundos.
AUTOMATIC_MODE = False
WATER_FILL_WAIT_SECONDS = 10
CHILLER_WAIT_SECONDS = 10
PRESSURE_SIMULATION_SECONDS = 15
TEMPERATURE_SIMULATION_SECONDS = 15

# Objetivos simulados. Sustituir por lecturas reales cuando se conecten sensores.
INITIAL_PRESSURE_TORR = 760.0
TARGET_VACUUM_TORR = 1.5e-2
INITIAL_TEMPERATURE_F = 75.0
TARGET_TEMPERATURE_A_F = 275.0
TARGET_TEMPERATURE_B_F = 272.0

# (address, relay). Cada salida puede cambiarse aquí si cambia el cableado.
RELAYS = {
    "air_compressor": (0, 1),
    "water_level_solenoid": (0, 2),
    "water_chiller": (0, 3),
    "magnetic_booster_pump": (0, 4),
    "cooling_trap_a": (0, 5),
    "cooling_trap_b": (0, 6),
    "diffuse_valve_a": (0, 7),
    "diffuse_valve_b": (0, 8),
    "chamber_valve_a": (1, 1),
    "chamber_valve_b": (1, 2),
    "mechanical_pump_a": (1, 3),
    "mechanical_pump_b": (1, 4),
    "diffusion_pump_a": (1, 5),
    "diffusion_pump_b": (1, 6),
    "gate_valve_a": (1, 7),
    "gate_valve_b": (1, 8),
}


def set_relay(name: str, on: bool) -> None:
    """Cambia un relé y muestra su estado en el terminal."""
    address, relay = RELAYS[name]
    target_state = "ON / ENCENDIDO" if on else "OFF / APAGADO"
    message = (
        f"[Address {address} | Relé {relay}] {name}: "
        f"LISTO PARA CAMBIAR A {target_state}."
    )
    if AUTOMATIC_MODE:
        print(f"\n{message} MODO AUTOMÁTICO.", flush=True)
    else:
        input(f"\n{message} Presione ENTER: ")

    if on:
        RELAY2.relayON(address, relay)
    else:
        RELAY2.relayOFF(address, relay)

    print(
        f"[Address {address} | Relé {relay}] {name}: {target_state}",
        flush=True,
    )


def wait_with_status(seconds: int, reason: str) -> None:
    """Espera mostrando el tiempo restante en el terminal."""
    print(f"\nESPERANDO: {reason}", flush=True)
    for remaining in range(seconds, 0, -1):
        minutes, secs = divmod(remaining, 60)
        print(
            f"\rTiempo restante: {minutes:02d}:{secs:02d}",
            end="",
            flush=True,
        )
        time.sleep(1)
    print("\rTiempo restante: 00:00 - COMPLETADO", flush=True)


def simulate_pressure() -> None:
    """Simula el descenso hasta el vacío definido en TARGET_VACUUM_TORR."""
    print("\n[SIMULACIÓN - SIN DATOS DEL ADC] Alcanzando vacío...", flush=True)
    for second in range(PRESSURE_SIMULATION_SECONDS + 1):
        progress = second / PRESSURE_SIMULATION_SECONDS
        pressure = INITIAL_PRESSURE_TORR * (
            TARGET_VACUUM_TORR / INITIAL_PRESSURE_TORR
        ) ** progress
        print(
            f"\rPresión simulada: {pressure:.3e} Torr "
            f"| {second:02d}/{PRESSURE_SIMULATION_SECONDS:02d} s",
            end="",
            flush=True,
        )
        if second < PRESSURE_SIMULATION_SECONDS:
            time.sleep(1)
    print(
        f"\nVacío simulado alcanzado: {TARGET_VACUUM_TORR:.3e} Torr.",
        flush=True,
    )


def simulate_temperature() -> None:
    """Simula en pantalla el calentamiento de ambas diffusion pumps."""
    print(
        "\n[SIMULACIÓN - SIN DATOS DEL THERMO] Calentando diffusion pumps...",
        flush=True,
    )
    for second in range(TEMPERATURE_SIMULATION_SECONDS + 1):
        progress = second / TEMPERATURE_SIMULATION_SECONDS
        temp_a = INITIAL_TEMPERATURE_F + (
            TARGET_TEMPERATURE_A_F - INITIAL_TEMPERATURE_F
        ) * progress
        temp_b = INITIAL_TEMPERATURE_F + (
            TARGET_TEMPERATURE_B_F - INITIAL_TEMPERATURE_F
        ) * progress
        print(
            f"\rTemp. A: {temp_a:6.1f} °F | Temp. B: {temp_b:6.1f} °F "
            f"| {second:02d}/{TEMPERATURE_SIMULATION_SECONDS:02d} s",
            end="",
            flush=True,
        )
        if second < TEMPERATURE_SIMULATION_SECONDS:
            time.sleep(1)
    print(
        f"\nTemperaturas simuladas alcanzadas: "
        f"A={TARGET_TEMPERATURE_A_F:.1f} °F, "
        f"B={TARGET_TEMPERATURE_B_F:.1f} °F.",
        flush=True,
    )


def verify_relay_plates() -> None:
    for address in (0, 1):
        board_id = RELAY2.getID(address)
        if "RELAYplate2" not in str(board_id):
            raise RuntimeError(
                f"No se encontró una RELAYplate2 en address {address}: "
                f"{board_id!r}"
            )
        print(f"Relay Plate address {address}: DETECTADA ({board_id})", flush=True)


def all_relays_off() -> None:
    for address in (0, 1):
        RELAY2.relayALL(address, 0)
    print("Todos los relés están OFF / APAGADOS.", flush=True)


def capture_relay_states() -> dict[int, int]:
    """Guarda la máscara inicial de los ocho relés de cada placa."""
    states = {address: RELAY2.relaySTATE(address) for address in (0, 1)}
    print("Estado original de los 16 relés guardado.", flush=True)
    return states


def restore_relay_states(states: dict[int, int]) -> None:
    """Devuelve ambas placas exactamente a su estado inicial."""
    print("\nRestaurando el estado original de los relés...", flush=True)
    for address in (0, 1):
        RELAY2.relayALL(address, states[address])
        print(
            f"Relay Plate address {address}: ESTADO ORIGINAL RESTAURADO "
            f"(máscara {states[address]:08b})",
            flush=True,
        )


def run_startup(original_states: dict[int, int]) -> bool:
    """Ejecuta un ciclo y devuelve True si el operador desea repetirlo."""
    print("\n=== START UP PROCESS 1.0 ===")
    print("Preparando inicio seguro: apagando los 16 relés...", flush=True)
    all_relays_off()
    if AUTOMATIC_MODE:
        print("MODO AUTOMÁTICO: iniciando la secuencia.", flush=True)
    else:
        input("Todos los relés están apagados. Presione ENTER para iniciar: ")

    print("\nPASO 2 - Air compressor")
    set_relay("air_compressor", True)

    print("\nPASO 3 - Water level solenoid")
    set_relay("water_level_solenoid", True)
    wait_with_status(WATER_FILL_WAIT_SECONDS, "llenado de agua")

    print("\nPASO 4 - Water chiller")
    set_relay("water_chiller", True)

    print("\nPASO 5 - Magnetic booster pump")
    wait_with_status(CHILLER_WAIT_SECONDS, "antes de encender el booster pump")
    set_relay("magnetic_booster_pump", True)

    print("\nPASO 6 - Cooling traps A & B")
    set_relay("cooling_trap_a", True)
    set_relay("cooling_trap_b", True)

    print("\nPASO 7 - Diffuse valves A & B")
    set_relay("diffuse_valve_a", True)
    set_relay("diffuse_valve_b", True)

    print("\nPASO 8 - Chamber valves A & B")
    set_relay("chamber_valve_a", True)
    set_relay("chamber_valve_b", True)

    print("\nPASO 9 - Mechanical pumps A & B")
    set_relay("mechanical_pump_a", True)
    set_relay("mechanical_pump_b", True)

    print("\nPASO 11 - Vacuum")
    simulate_pressure()

    print("\nPASO 12 - Diffusion pumps A & B")
    set_relay("diffusion_pump_a", True)
    set_relay("diffusion_pump_b", True)

    print("\nPASO 13 - Temperatura de diffusion pumps")
    simulate_temperature()

    print("\nPASO 14 - Chamber valves A & B")
    set_relay("chamber_valve_a", False)
    set_relay("chamber_valve_b", False)

    print("\nPASO 15 - Gate valves A & B")
    set_relay("gate_valve_a", True)
    set_relay("gate_valve_b", True)

    print("\nPASO 16 - Inyección de gas")
    print("Inyecte el gas deseado y regule la presión.", flush=True)
    print("\n=== START UP COMPLETADO ===", flush=True)

    if AUTOMATIC_MODE:
        print("MODO AUTOMÁTICO: restaurando el estado original.", flush=True)
        restore_relay_states(original_states)
        print("\n=== ESTADO ORIGINAL RESTAURADO ===", flush=True)
        return False

    answer = input(
        "Escriba SI para repetir la secuencia o presione ENTER para "
        "restaurar el estado original y finalizar: "
    ).strip().lower()
    if answer in {"si", "sí"}:
        print("\nLa secuencia se repetirá desde el comienzo.", flush=True)
        return True

    restore_relay_states(original_states)
    print("\n=== ESTADO ORIGINAL RESTAURADO ===", flush=True)
    return False


def main() -> None:
    try:
        verify_relay_plates()
        original_states = capture_relay_states()
        repeat = True
        while repeat:
            repeat = run_startup(original_states)
    except KeyboardInterrupt:
        print("\nSecuencia interrumpida por el operador.", flush=True)
        print(
            "Los relés conservan su estado actual; revise el sistema antes de salir.",
            flush=True,
        )
    except Exception as exc:
        print(f"\nERROR: {exc}", flush=True)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
