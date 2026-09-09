#Shutdown Process para el reactor de plasma basado
#en el diseño shutdown que proveyó Rey Mendez

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
    """Falla que detiene la secuencia."""


class SimulatedShutdownSensors:
    def __init__(self) -> None:
        self.diffusion_a_c = cfg.SIM_SHUTDOWN_INITIAL_DIFFUSION_TEMP_C
        self.diffusion_b_c = cfg.SIM_SHUTDOWN_INITIAL_DIFFUSION_TEMP_C

    def read_cooling_diffusion_temperatures(self) -> tuple[float, float]:
        self.diffusion_a_c = max(
            20.0, self.diffusion_a_c - cfg.SIM_DIFFUSION_PUMP_COOLING_STEP_C
        )
        self.diffusion_b_c = max(
            20.0, self.diffusion_b_c - cfg.SIM_DIFFUSION_PUMP_COOLING_STEP_C
        )
        return self.diffusion_a_c, self.diffusion_b_c


def pause_for_operator(message: str) -> None:
    if cfg.AUTOMATIC_MODE:
        print(f"{message} [AUTOMÁTICO]", flush=True)
    else:
        input(f"{message} Presione ENTER: ")


def set_relay(name: str, on: bool) -> None:
    address, relay = RELAYS[name]
    state = "ON" if on else "OFF"

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


def show_step(number: str, title: str) -> None:
    print(f"\n{'=' * 68}")
    print(f"PASO {number}: {title}")
    print(f"{'=' * 68}", flush=True)


def run_shutdown_sequence() -> None:
    sensors = SimulatedShutdownSensors()
    print("\n=== SHUTDOWN PROCESS ===")

    show_step("5", "Close injection valve and wait 2 minutes")
    pause_for_operator("Cierre la Injection Valve manualmente.")
    wait_seconds(cfg.INJECTION_VALVE_WAIT_SECONDS, "espera de estabilización de gas")

    show_step("6", "Switch to OFF position the gate valves A & B")
    set_relay("Gate Valve A", False)
    set_relay("Gate Valve B", False)

    show_step("7", "Switch to OFF position the diffusion pumps A & B")
    set_relay("Diffusion Pump A", False)
    set_relay("Diffusion Pump B", False)

    show_step("12", "Wait until the diffusion pumps reach <= 100 °F (37.78 °C)")
    cooling_condition = f"TEMP A <= {cfg.MAX_SAFE_DIFFUSION_TEMP_C:.2f} °C AND TEMP B <= {cfg.MAX_SAFE_DIFFUSION_TEMP_C:.2f} °C"

    for attempt in range(1, cfg.MAX_SENSOR_CHECKS + 1):
        temp_a, temp_b = sensors.read_cooling_diffusion_temperatures()
        print(f"Diffusion temps: A={temp_a:.2f} °C, B={temp_b:.2f} °C", flush=True)

        if (temp_a <= cfg.MAX_SAFE_DIFFUSION_TEMP_C and temp_b <= cfg.MAX_SAFE_DIFFUSION_TEMP_C):
            print(f"RESULTADO: CUMPLE ({cooling_condition}) -> avanzando.")
            break
        else:
            print("RESULTADO: NO CUMPLE -> continuar enfriando.")
            wait_seconds(cfg.DIFFUSION_COOLDOWN_RECHECK_SECONDS, "enfriamiento de bombas")
    else:
        raise ProcessFault("Excedido el tiempo máximo de espera para enfriamiento.")

    show_step("9", "Switch to OFF position the diffuse valves A & B")
    set_relay("Diffuse Valve A", False)
    set_relay("Diffuse Valve B", False)

    show_step("8", "Switch to OFF position the mechanical pumps A & B")
    set_relay("Mechanical Pump A", False)
    set_relay("Mechanical Pump B", False)

    show_step("10", "Switch to OFF position the air compressor")
    set_relay("Air Compressor", False)

    show_step("13", "Switch to OFF position the cooling traps A & B")
    set_relay("Cooling Trap A", False)
    set_relay("Cooling Trap B", False)

    show_step("14", "Switch to OFF position the magnetic booster pump")
    set_relay("Magnetic Booster Pump", False)

    show_step("15", "Turn OFF position the water chiller")
    pause_for_operator("Apague el Water Chiller manualmente (control externo).")

    show_step("16", "Switch to OFF position the water level solenoid")
    print("Water Level Solenoid: EXCLUIDO POR REQUISITO DEL PROYECTO -> Saltando paso.")

    print("\n=== SECUENCIA DE APAGADO COMPLETADA CON ÉXITO ===", flush=True)


def main() -> None:
    try:
        pause_for_operator("Sistema preparado para iniciar secuencia de apagado.")
        run_shutdown_sequence()
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

