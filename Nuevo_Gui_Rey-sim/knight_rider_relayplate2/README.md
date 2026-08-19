# Knight Rider para RELAYplate2

Este programa crea un barrido continuo en los siete relés de una Pi-Plates
RELAYplate2:

```text
K1 -> K2 -> K3 -> K4 -> K5 -> K6 -> K7 -> K6 -> ... -> K2 -> K1
```

## Preparación en la Raspberry Pi

Instala la librería de Pi-Plates si todavía no está disponible:

```bash
python3 -m pip install piplates
```

Con la RELAYplate2 instalada y configurada con la dirección 0, ejecuta:

```bash
cd Nuevo_Gui_Rey-sim/knight_rider_relayplate2
python3 knight_rider.py
```

Detén el efecto con `Ctrl+C`. El programa apaga todos los relés antes de salir.

## Opciones

```bash
# Barrido más rápido
python3 knight_rider.py --delay 0.10

# Ejecutar solamente cinco ciclos
python3 knight_rider.py --cycles 5

# Usar una placa cuyos jumpers indiquen la dirección 2
python3 knight_rider.py --address 2
```

Usa `python3 knight_rider.py --help` para ver todas las opciones.

> **Seguridad:** corta la alimentación antes de conectar cargas. La placa puede
> manejar voltajes peligrosos; no trabajes con terminales energizados o cables
> expuestos.
