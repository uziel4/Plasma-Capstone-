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
    confirmed_state = "ON" if relay_is_on(name) else "OFF"
    print(
        f"ESTADO ACTUAL -> [Address {address} | Relé {relay}] "
        f"{name}: {confirmed_state}",
        flush=True,
    )


def relay_is_on(name: str) -> bool:
    address, relay = RELAYS[name]
    return bool(RELAY2.relaySTATE(address) & (1 << (relay - 1)))


def wait_seconds(seconds: int, reason: str) -> None:
    print(f"ESPERANDO {seconds} s: {reason}", flush=True)
    for remaining in range(seconds, 0, -1):
        print(f"\rTiempo restante: {remaining:04d} s", end="", flush=True)
        time.sleep(1)
    print("\rEspera completada.          ", flush=True)


def show_step(number: str, title: str, next_step: str) -> None:
    print(f"\n{'=' * 68}")
    print(f"PASO {number}: {title}")
    print(f"PRÓXIMO PASO: {next_step}")
    print(f"{'=' * 68}", flush=True)


def check_limit(
    description: str,
    condition_text: str,
    read_value,
    accepted,
    unit: str,
    retry_wait: int,
) -> float:
    print(f"ESTADO: VERIFICANDO {description}", flush=True)
    print("+----------------------------------------------------------+")
    print("| CONDICIÓN REQUERIDA PARA AVANZAR")
    print(f"| {condition_text}")
    print("+----------------------------------------------------------+", flush=True)
    for attempt in range(1, cfg.MAX_SENSOR_CHECKS + 1):
        value = read_value()
        print(
            f"VALOR SIMULADO: {description} = {value:.3e} {unit} "
            f"(lectura {attempt})",
            flush=True,
        )
        if accepted(value):
            print(
                f"RESULTADO: CUMPLE ({condition_text}) -> avanzando.",
                flush=True,
            )
            return value
        else:
            print(
                f"RESULTADO: NO CUMPLE ({condition_text}) -> permanecer aquí.",
                flush=True,
            )
            wait_seconds(retry_wait, description)
    raise ProcessFault(f"Tiempo máximo excedido: {description}")


def verify_plates() -> None:
    for address in (cfg.RELAY_PLATE_1_ADDRESS, cfg.RELAY_PLATE_2_ADDRESS):
        board_id = RELAY2.getID(address)
        condition = f"BOARD ID CONTAINS 'RELAYplate2' AT ADDRESS {address}"
        print(f"CONDICIÓN REQUERIDA: {condition}")
        if "RELAYplate2" in str(board_id):
            print(f"RESULTADO: CUMPLE - placa detectada ({board_id})")
        else:
            print(f"RESULTADO: NO CUMPLE - ID recibido: {board_id!r}")
            raise ProcessFault(f"RELAYplate2 no detectada en address {address}: {board_id!r}")


def all_relays_off() -> None:
    RELAY2.relayALL(cfg.RELAY_PLATE_1_ADDRESS, 0)
    RELAY2.relayALL(cfg.RELAY_PLATE_2_ADDRESS, 0)
    print("ESTADO DE SEGURIDAD: los 16 relés están OFF.", flush=True)


def ask_to_repeat() -> bool:
    answer = input(
        "\nEscriba SI para repetir la simulación o presione ENTER "
        "para terminar: "
    ).strip().lower()
    if answer in {"si", "sí"}:
        print("RESULTADO: se repetirá la simulación completa.", flush=True)
        return True
    else:
        print("RESULTADO: simulación finalizada; relés permanecen OFF.", flush=True)
        return False


def run_sequence() -> None:
    print("CONDICIÓN REQUERIDA: SIMULATE_SENSOR_DATA = True")
    if not cfg.SIMULATE_SENSOR_DATA:
        print("RESULTADO: NO CUMPLE - lectura real no implementada")
        raise ProcessFault(
            "Las lecturas reales aún no están implementadas. Use "
            "SIMULATE_SENSOR_DATA = True."
        )
    else:
        print("RESULTADO: CUMPLE - se usarán valores simulados")

    sensors = SimulatedSensors()
    print("\n=== STARTUP PROCESS 2.0 ===")
    print("SENSORES: MODO SIMULADO - NO SE RECOLECTAN DATOS DE ADC/THERMO")
    print("Water Level Solenoid: EXCLUIDO / NO SE ACCIONA")

    show_step("1", "Air Compressor y Cooling Traps ON", "validar presión de aire")
    set_relay("Air Compressor", True)
    set_relay("Cooling Trap A", True)
    set_relay("Cooling Trap B", True)
    air_condition = f"AIR PRESSURE >= {cfg.MIN_AIR_PRESSURE_PSI:.1f} PSI"
    air_pressure = sensors.read_air_pressure()
    print(f"CONDICIÓN REQUERIDA: {air_condition}")
    print(f"VALOR SIMULADO: AIR PRESSURE = {air_pressure:.1f} PSI")
    if air_pressure >= cfg.MIN_AIR_PRESSURE_PSI:
        print(f"RESULTADO: CUMPLE ({air_condition}) -> avanzando.")
    else:
        print(f"RESULTADO: NO CUMPLE ({air_condition}) -> FAULT.")
        raise ProcessFault(
            "Cooling System Failure: revisar compresor; no accionar válvulas "
            "neumáticas sin suficiente presión de aire"
        )

    show_step("2", "Water Chiller ON", "validar temperatura del tanque")
    print("Water Chiller: ON (control externo; sin relé asignado)")
    check_limit(
        "Water Tank Temperature",
        f"WATER TANK TEMPERATURE <= {cfg.MAX_WATER_TANK_TEMPERATURE_C:.1f} °C",
        sensors.read_water_tank_temperature,
        lambda value: value <= cfg.MAX_WATER_TANK_TEMPERATURE_C,
        "°C",
        cfg.WATER_TANK_RECHECK_SECONDS,
    )
    wait_seconds(cfg.BOOSTER_DELAY_SECONDS, "tiempo mínimo antes del booster")
    show_step("3", "Magnetic Booster Pump ON", "validar línea de agua")
    set_relay("Magnetic Booster Pump", True)
    check_limit(
        "Reactor Water Line Temperature",
        f"REACTOR WATER LINE TEMPERATURE <= "
        f"{cfg.MAX_REACTOR_WATER_TEMPERATURE_C:.1f} °C",
        sensors.read_reactor_water_temperature,
        lambda value: value <= cfg.MAX_REACTOR_WATER_TEMPERATURE_C,
        "°C",
        cfg.REACTOR_WATER_RECHECK_SECONDS,
    )

    show_step("4", "Diffuse Valves A & B OPEN", "abrir chamber valves")
    set_relay("Diffuse Valve A", True)
    set_relay("Diffuse Valve B", True)
    wait_seconds(cfg.VALVE_SEAT_WAIT_SECONDS, "asentar diffuse valves")
    show_step("5", "Chamber Valves A & B OPEN", "encender mechanical pumps")
    set_relay("Chamber Valve A", True)
    set_relay("Chamber Valve B", True)
    wait_seconds(cfg.VALVE_SEAT_WAIT_SECONDS, "asentar chamber valves")
    show_step("6", "Mechanical Pumps A & B ON", "validar temperatura y vacío")
    set_relay("Mechanical Pump A", True)
    set_relay("Mechanical Pump B", True)

    check_limit(
        "Mechanical Pump Temperature",
        f"MECHANICAL PUMP TEMPERATURE >= "
        f"{cfg.MIN_MECHANICAL_PUMP_TEMPERATURE_C:.2f} °C",
        sensors.read_mechanical_pump_temperature,
        lambda value: value >= cfg.MIN_MECHANICAL_PUMP_TEMPERATURE_C,
        "°C",
        cfg.MECHANICAL_PUMP_RECHECK_SECONDS,
    )
    check_limit(
        "Chamber Vacuum - roughing",
        f"CHAMBER VACUUM <= {cfg.CROSSOVER_VACUUM_TORR:.3e} TORR",
        sensors.read_chamber_pressure,
        lambda value: value <= cfg.CROSSOVER_VACUUM_TORR,
        "Torr",
        cfg.ROUGHING_PRESSURE_RECHECK_SECONDS,
    )

    show_step("7", "Diffusion Pumps A & B ON", "alcanzar temperatura de operación")
    set_relay("Diffusion Pump A", True)
    set_relay("Diffusion Pump B", True)
    diffusion_condition = (
        "DIFFUSION PUMP A TEMPERATURE >= "
        f"{cfg.MIN_DIFFUSION_PUMP_TEMPERATURE_C:.1f} °C AND "
        "DIFFUSION PUMP B TEMPERATURE >= "
        f"{cfg.MIN_DIFFUSION_PUMP_TEMPERATURE_C:.1f} °C"
    )
    print("ESTADO: CALENTANDO DIFFUSION PUMPS", flush=True)
    print("+----------------------------------------------------------+")
    print("| CONDICIÓN REQUERIDA PARA AVANZAR")
    print(f"| {diffusion_condition}")
    print("+----------------------------------------------------------+", flush=True)
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
            print(f"RESULTADO: CUMPLE ({diffusion_condition}) -> avanzando.")
            break
        else:
            print(
                f"RESULTADO: NO CUMPLE ({diffusion_condition}) -> "
                "continuar calentando."
            )
            wait_seconds(
                cfg.DIFFUSION_TEMPERATURE_RECHECK_SECONDS,
                "calentamiento diffusion pumps",
            )
    else:
        raise ProcessFault("Diffusion pumps no alcanzaron la temperatura requerida")

    check_limit(
        "Chamber Vacuum - comprobación final",
        f"CHAMBER VACUUM <= {cfg.CROSSOVER_VACUUM_TORR:.3e} TORR",
        lambda: sensors.read_chamber_pressure(diffusion=True),
        lambda value: value <= cfg.CROSSOVER_VACUUM_TORR,
        "Torr",
        cfg.FINAL_PRESSURE_RECHECK_SECONDS,
    )

    show_step("8", "Chamber Valves A & B CLOSE", "confirmar cierre")
    set_relay("Chamber Valve A", False)
    set_relay("Chamber Valve B", False)
    print("CONDICIÓN REQUERIDA: CHAMBER VALVE A = OFF AND B = OFF")
    if not relay_is_on("Chamber Valve A") and not relay_is_on("Chamber Valve B"):
        print("RESULTADO: CUMPLE - Chamber Valves A & B están cerradas.")
    else:
        print("RESULTADO: NO CUMPLE - revisar cierre de Chamber Valves A & B.")
        raise ProcessFault("Chamber valves no confirmaron estado cerrado")

    show_step("9", "Gate Valves A & B OPEN", "confirmar apertura")
    set_relay("Gate Valve A", True)
    set_relay("Gate Valve B", True)
    wait_seconds(cfg.VALVE_SEAT_WAIT_SECONDS, "confirmar apertura de gate valves")
    print("CONDICIÓN REQUERIDA: GATE VALVE A = ON AND B = ON")
    if relay_is_on("Gate Valve A") and relay_is_on("Gate Valve B"):
        print("RESULTADO: CUMPLE - Gate Valves A & B están abiertas.")
    else:
        print("RESULTADO: NO CUMPLE - ejecutando interlock de Gate Valves.")
        set_relay("Gate Valve A", False)
        set_relay("Gate Valve B", False)
        raise ProcessFault("Gate valve failed to open; revisar actuador neumático")

    show_step("10", "Gas y sistema de microondas", "estado operacional")
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
        repeat = True
        while repeat:
            all_relays_off()
            pause_for_operator("Sistema preparado para comenzar.")
            run_sequence()
            print("\nApagando todos los relés al terminar la simulación...")
            all_relays_off()
            repeat = ask_to_repeat()
    except KeyboardInterrupt:
        print("\nSecuencia interrumpida por el operador.", flush=True)
        all_relays_off()
    except ProcessFault as exc:
        print(f"\n⚠ FAULT: {exc}", flush=True)
        all_relays_off()
        raise SystemExit(1) from exc
    except Exception as exc:
        print(f"\nERROR DE HARDWARE: {exc}", flush=True)
        try:
            all_relays_off()
        except Exception:
            print("No fue posible confirmar el apagado de los relés.", flush=True)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
