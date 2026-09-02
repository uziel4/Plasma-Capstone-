# Handoff — Start Up process 1.0

## Hardware utilizado

- Raspberry Pi 5
- RELAYplate2 address 0: relés 1–8
- RELAYplate2 address 1: relés 1–8
- THERMOplate address 2: reservada; todavía no se leen datos
- ADCplate address 3: reservada; todavía no se leen datos

## Asignación de los relés

| Paso | Address | Relé | Equipo | Acción |
|---:|---:|---:|---|---|
| 2 | 0 | 1 | Air compressor | ON |
| 3 | 0 | 2 | Water level solenoid | ON |
| 4 | 0 | 3 | Water chiller | ON |
| 5 | 0 | 4 | Magnetic booster pump | ON |
| 6 | 0 | 5 | Cooling trap A | ON |
| 6 | 0 | 6 | Cooling trap B | ON |
| 7 | 0 | 7 | Diffuse valve A | ON |
| 7 | 0 | 8 | Diffuse valve B | ON |
| 8 | 1 | 1 | Chamber valve A | ON |
| 8 | 1 | 2 | Chamber valve B | ON |
| 9 | 1 | 3 | Mechanical pump A | ON |
| 9 | 1 | 4 | Mechanical pump B | ON |
| 12 | 1 | 5 | Diffusion pump A | ON |
| 12 | 1 | 6 | Diffusion pump B | ON |
| 14 | 1 | 1 | Chamber valve A | OFF |
| 14 | 1 | 2 | Chamber valve B | OFF |
| 15 | 1 | 7 | Gate valve A | ON |
| 15 | 1 | 8 | Gate valve B | ON |

Esta asignación debe compararse con el cableado físico antes de ejecutar el
programa en el sistema real.

## Tiempos

- Después de encender el water level solenoid: espera real de 120 segundos.
- Después de encender el water chiller y antes del magnetic booster pump:
  espera real de 120 segundos.
- Durante cada espera aparece una cuenta regresiva en el terminal.
- `WAIT_TWO_MINUTES` permite cambiar las esperas reales.
- `SIMULATION_SECONDS` permite cambiar la duración visual de las simulaciones.

## Pasos simulados

### Paso 11 — Presión

No lee la ADCplate. El terminal muestra una presión ficticia descendiendo desde
760,000 milliTorr hasta 15 milliTorr durante 15 segundos. Al terminar informa
que alcanzó de forma simulada el rango solicitado de 30–1 milliTorr.

### Paso 13 — Temperaturas

No lee la THERMOplate. El terminal muestra temperaturas ficticias para las
diffusion pumps A y B, desde 75 °F hasta 275 °F y 272 °F respectivamente,
durante 15 segundos. Al terminar informa que alcanzaron de forma simulada el
rango de 250–300 °F.

Los valores simulados no confirman las condiciones físicas del sistema y no
deben tratarse como medidas de seguridad.

## Paso manual

El paso 16 solamente muestra en el terminal: “Inyecte el gas deseado y regule
la presión”. No tiene un relé asignado porque los 16 relés ya están asignados.

## Información mostrada en el terminal

Por cada acción real aparece una línea con este formato:

```text
[Address 0 | Relé 1] air_compressor: ON / ENCENDIDO
```

También aparecen el paso actual, las cuentas regresivas, los valores simulados,
los errores de comunicación y el aviso de finalización de la secuencia.

## Comportamiento al interrumpir

Si se presiona `Ctrl+C`, la secuencia se detiene, pero los relés conservan su
estado actual. El operador debe revisar el sistema antes de salir.

## Ejecución

```bash
python3 "Capstone 2/Start Up process1.0.py"
```
