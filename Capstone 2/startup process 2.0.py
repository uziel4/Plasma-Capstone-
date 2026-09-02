#!/usr/bin/env python3
"""Secuencia de startup 2.0 basada en el flowchart V2.

El Water Level Solenoid está intencionalmente excluido. Las lecturas se simulan
mientras SIMULATE_SENSOR_DATA sea True en startup_process_2_config.py.
"""

import time

import startup_process_2_config as cfg

try:
    import piplates.RELAYplate2 as RELAY2
except ImportError as exc:
    raise SystemExit(
        "No se encontró Pi-Plates. Instale con: python3 -m pip install Pi-Plates"
    ) from exc


RELAYS = {
    "Air Compressor": cfg.AIR_COMPRESSOR_RELAY,
    "Magnetic Booster Pump": cfg.MAGNETIC_BOOSTER_PUMP_RELAY,
    "Cooling Trap A": cfg.COOLING_TRAP_A_RELAY,
    "Cooling Trap B": cfg.COOLING_TRAP_B_RELAY,
    "Diffuse Valve A": cfg.DIFFUSE_VALVE_A_RELAY,
    "Diffuse Valve B": cfg.DIFFUSE_VALVE_B_RELAY,
    "Chamber Valve A": cfg.CHAMBER_VALVE_A_RELAY,
    "Chamber Valve B": cfg.CHAMBER_VALVE_B_RELAY,
    "Mechanical Pump A": cfg.MECHANICAL_PUMP_A_RELAY,
    "Mechanical Pump B": cfg.MECHANICAL_PUMP_B_RELAY,
    "Diffusion Pump A": cfg.DIFFUSION_PUMP_A_RELAY,
    "Diffusion Pump B": cfg.DIFFUSION_PUMP_B_RELAY,
    "Gate Valve A": cfg.GATE_VALVE_A_RELAY,
    "Gate Valve B": cfg.GATE_VALVE_B_RELAY,
    "Microwave Cooling": cfg.MICROWAVE_COOLING_RELAY,
}


class ProcessFault(RuntimeError):
    """Falla de interlock que detiene la secuencia."""


class SimulatedSensors:
    def __init__(self) -> None:
        self.air_psi = cfg.SIM_INITIAL_AIR_PRESSURE_PSI
        self.water_tank_c = cfg.SIM_INITIAL_WATER_TANK_TEMPERATURE_C
        self.reactor_water_c = cfg.SIM_INITIAL_REACTOR_WATER_TEMPERATURE_C
        self.mechanical_pump_c = cfg.SIM_INITIAL_MECHANICAL_PUMP_TEMPERATURE_C
        self.chamber_torr = cfg.SIM_INITIAL_CHAMBER_PRESSURE_TORR
        self.diffusion_a_c = cfg.SIM_INITIAL_DIFFUSION_PUMP_A_TEMPERATURE_C
        self.diffusion_b_c = cfg.SIM_INITIAL_DIFFUSION_PUMP_B_TEMPERATURE_C

    def read_air_pressure(self) -> float:
        self.air_psi += cfg.SIM_AIR_PRESSURE_STEP_PSI
        return self.air_psi

    def read_water_tank_temperature(self) -> float:
        self.water_tank_c = max(
            cfg.MAX_WATER_TANK_TEMPERATURE_C,
            self.water_tank_c - cfg.SIM_WATER_TANK_COOLING_STEP_C,
        )
        return self.water_tank_c

    def read_reactor_water_temperature(self) -> float:
        self.reactor_water_c = max(
            cfg.MAX_REACTOR_WATER_TEMPERATURE_C,
            self.reactor_water_c - cfg.SIM_REACTOR_WATER_COOLING_STEP_C,
        )
        return self.reactor_water_c

    def read_mechanical_pump_temperature(self) -> float:
        self.mechanical_pump_c += cfg.SIM_MECHANICAL_PUMP_HEATING_STEP_C
        return self.mechanical_pump_c

    def read_chamber_pressure(self, diffusion: bool = False) -> float:
        factor = (
            cfg.SIM_DIFFUSION_PRESSURE_FACTOR
            if diffusion
            else cfg.SIM_ROUGHING_PRESSURE_FACTOR
        )
        self.chamber_torr = max(cfg.CROSSOVER_VACUUM_TORR, self.chamber_torr * factor)
        return self.chamber_torr

    def read_diffusion_temperatures(self) -> tuple[float, float]:
        self.diffusion_a_c += cfg.SIM_DIFFUSION_PUMP_HEATING_STEP_C
        self.diffusion_b_c += cfg.SIM_DIFFUSION_PUMP_HEATING_STEP_C
        return self.diffusion_a_c, self.diffusion_b_c


def pause_for_operator(message: str) -> None:
    if cfg.AUTOMATIC_MODE:
        print(f"{message} [AUTOMÁTICO]", flush=True)
    else:
        input(f"{message} Presione ENTER: ")


def set_relay(name: str, on: bool) -> None:
    address, relay = RELAYS[name]
    state = "ON" if on else "OFF"
    pause_for_operator(
        f"[Address {address} | Relé {relay}] {name}: listo para {state}."
    )
    if on:
        RELAY2.relayON(address, relay)
    else:
        RELAY2.relayOFF(address, relay)
    print(f"[Address {address} | Relé {relay}] {name}: {state}", flush=True)


def relay_is_on(name: str) -> bool:
    address, relay = RELAYS[name]
    return bool(RELAY2.relaySTATE(address) & (1 << (relay - 1)))


def wait_seconds(seconds: int, reason: str) -> None:
    print(f"ESPERANDO {seconds} s: {reason}", flush=True)
    for remaining in range(seconds, 0, -1):
        print(f"\rTiempo restante: {remaining:04d} s", end="", flush=True)
        time.sleep(1)
    print("\rEspera completada.          ", flush=True)


def check_limit(
    description: str,
    read_value,
    accepted,
    unit: str,
    retry_wait: int,
) -> float:
    for attempt in range(1, cfg.MAX_SENSOR_CHECKS + 1):
        value = read_value()
        print(f"{description}: {value:.3e} {unit} (lectura {attempt})", flush=True)
        if accepted(value):
            print("Condición: SÍ", flush=True)
            return value
        else:
            print("Condición: NO - continuar esperando/verificando.", flush=True)
            wait_seconds(retry_wait, description)
    raise ProcessFault(f"Tiempo máximo excedido: {description}")


def verify_plates() -> None:
    for address in (cfg.RELAY_PLATE_1_ADDRESS, cfg.RELAY_PLATE_2_ADDRESS):
        board_id = RELAY2.getID(address)
        if "RELAYplate2" in str(board_id):
            print(f"Relay Plate address {address}: DETECTADA ({board_id})")
        else:
            raise ProcessFault(f"RELAYplate2 no detectada en address {address}: {board_id!r}")


def all_relays_off() -> None:
    RELAY2.relayALL(cfg.RELAY_PLATE_1_ADDRESS, 0)
    RELAY2.relayALL(cfg.RELAY_PLATE_2_ADDRESS, 0)
    print("Estado inicial: los 16 relés están OFF.", flush=True)


def run_sequence() -> None:
    if not cfg.SIMULATE_SENSOR_DATA:
        raise ProcessFault(
            "Las lecturas reales aún no están implementadas. Use "
            "SIMULATE_SENSOR_DATA = True."
        )

    sensors = SimulatedSensors()
    print("\n=== STARTUP PROCESS 2.0 ===")
    print("Water Level Solenoid: EXCLUIDO / NO SE ACCIONA")

    set_relay("Air Compressor", True)
    set_relay("Cooling Trap A", True)
    set_relay("Cooling Trap B", True)
    check_limit(
        "Air Pressure",
        sensors.read_air_pressure,
        lambda value: value >= cfg.MIN_AIR_PRESSURE_PSI,
        "psi",
        cfg.AIR_PRESSURE_RECHECK_SECONDS,
    )

    print("Water Chiller: ON (control externo; sin relé asignado)")
    check_limit(
        "Water Tank Temperature",
        sensors.read_water_tank_temperature,
        lambda value: value <= cfg.MAX_WATER_TANK_TEMPERATURE_C,
        "°C",
        cfg.WATER_TANK_RECHECK_SECONDS,
    )
    wait_seconds(cfg.BOOSTER_DELAY_SECONDS, "tiempo mínimo antes del booster")
    set_relay("Magnetic Booster Pump", True)
    check_limit(
        "Reactor Water Line Temperature",
        sensors.read_reactor_water_temperature,
        lambda value: value <= cfg.MAX_REACTOR_WATER_TEMPERATURE_C,
        "°C",
        cfg.REACTOR_WATER_RECHECK_SECONDS,
    )

    set_relay("Diffuse Valve A", True)
    set_relay("Diffuse Valve B", True)
    wait_seconds(cfg.VALVE_SEAT_WAIT_SECONDS, "asentar diffuse valves")
    set_relay("Chamber Valve A", True)
    set_relay("Chamber Valve B", True)
    wait_seconds(cfg.VALVE_SEAT_WAIT_SECONDS, "asentar chamber valves")
    set_relay("Mechanical Pump A", True)
    set_relay("Mechanical Pump B", True)

    check_limit(
        "Mechanical Pump Temperature",
        sensors.read_mechanical_pump_temperature,
        lambda value: value >= cfg.MIN_MECHANICAL_PUMP_TEMPERATURE_C,
        "°C",
        cfg.MECHANICAL_PUMP_RECHECK_SECONDS,
    )
    check_limit(
        "Chamber Vacuum - roughing",
        sensors.read_chamber_pressure,
        lambda value: value <= cfg.CROSSOVER_VACUUM_TORR,
        "Torr",
        cfg.ROUGHING_PRESSURE_RECHECK_SECONDS,
    )

    set_relay("Diffusion Pump A", True)
    set_relay("Diffusion Pump B", True)
    for attempt in range(1, cfg.MAX_SENSOR_CHECKS + 1):
        temp_a, temp_b = sensors.read_diffusion_temperatures()
        print(
            f"Diffusion temperatures: A={temp_a:.1f} °C, B={temp_b:.1f} °C",
            flush=True,
        )
        if (
            temp_a >= cfg.MIN_DIFFUSION_PUMP_TEMPERATURE_C
            and temp_b >= cfg.MIN_DIFFUSION_PUMP_TEMPERATURE_C
        ):
            print("Condición de temperatura: SÍ")
            break
        else:
            print("Condición de temperatura: NO - continuar calentando.")
            wait_seconds(
                cfg.DIFFUSION_TEMPERATURE_RECHECK_SECONDS,
                "calentamiento diffusion pumps",
            )
    else:
        raise ProcessFault("Diffusion pumps no alcanzaron la temperatura requerida")

    check_limit(
        "Chamber Vacuum - comprobación final",
        lambda: sensors.read_chamber_pressure(diffusion=True),
        lambda value: value <= cfg.CROSSOVER_VACUUM_TORR,
        "Torr",
        cfg.FINAL_PRESSURE_RECHECK_SECONDS,
    )

    set_relay("Chamber Valve A", False)
    set_relay("Chamber Valve B", False)
    if not relay_is_on("Chamber Valve A") and not relay_is_on("Chamber Valve B"):
        print("Chamber Valves A & B cerradas: SÍ")
    else:
        raise ProcessFault("Chamber valves no confirmaron estado cerrado")

    set_relay("Gate Valve A", True)
    set_relay("Gate Valve B", True)
    wait_seconds(cfg.VALVE_SEAT_WAIT_SECONDS, "confirmar apertura de gate valves")
    if relay_is_on("Gate Valve A") and relay_is_on("Gate Valve B"):
        print("Gate Valves A & B abiertas: SÍ")
    else:
        set_relay("Gate Valve A", False)
        set_relay("Gate Valve B", False)
        raise ProcessFault("Gate valve failed to open; revisar actuador neumático")

    pause_for_operator("Inyecte el gas de proceso y regule la presión.")
    set_relay("Microwave Cooling", True)
    pause_for_operator(
        f"Encienda Power Supply y ajuste aproximadamente {cfg.POWER_SUPPLY_CURRENT_AMPS:.0f} A."
    )
    pause_for_operator("Encienda Microwave Source.")
    pause_for_operator("Espere la luz verde READY y presione ON.")
    pause_for_operator(
        f"Ajuste Microwave Power a {cfg.MICROWAVE_POWER_LEVEL_PERCENT:.1f} %."
    )
    print("\n=== SEQUENCE COMPLETE - SYSTEM OPERATIONAL ===", flush=True)


def main() -> None:
    try:
        verify_plates()
        all_relays_off()
        pause_for_operator("Sistema preparado para comenzar.")
        run_sequence()
    except KeyboardInterrupt:
        print("\nSecuencia interrumpida por el operador.", flush=True)
    except ProcessFault as exc:
        print(f"\n⚠ FAULT: {exc}", flush=True)
        raise SystemExit(1) from exc
    except Exception as exc:
        print(f"\nERROR DE HARDWARE: {exc}", flush=True)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
