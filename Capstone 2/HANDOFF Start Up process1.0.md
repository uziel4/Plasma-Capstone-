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
| 3 | 0 | 2 | Water level solenoid | FUERA DE SERVICIO / OMITIDO |
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

El paso 3 está comentado en el programa. Actualmente no acciona el relé del
water level solenoid ni ejecuta la espera de llenado. Las líneas permanecen en
el archivo para poder reactivarlas retirando sus comentarios.

## Tiempos

- Antes de cada acción de la secuencia, el terminal identifica el equipo, el
  address, el relé y el estado solicitado. El relé no cambia hasta que el
  operador presiona `ENTER`.
- `WATER_FILL_WAIT_SECONDS`: espera después de encender el water level
  solenoid; actualmente 10 segundos.
- `CHILLER_WAIT_SECONDS`: espera después de encender el water chiller y antes
  del magnetic booster pump; actualmente 10 segundos.
- `PRESSURE_SIMULATION_SECONDS`: duración de la simulación de vacío;
  actualmente 15 segundos.
- `TEMPERATURE_SIMULATION_SECONDS`: duración de la simulación de temperatura;
  actualmente 15 segundos.
- Durante cada espera aparece una cuenta regresiva en el terminal.

Los objetivos simulados también se cambian al principio del archivo:

- `INITIAL_PRESSURE_TORR`: presión inicial de la simulación.
- `TARGET_VACUUM_TORR`: vacío único que debe alcanzar la simulación.
- `INITIAL_TEMPERATURE_F`: temperatura inicial simulada.
- `TARGET_TEMPERATURE_A_F`: temperatura objetivo de la diffusion pump A.
- `TARGET_TEMPERATURE_B_F`: temperatura objetivo de la diffusion pump B.

## Modo manual o automático

La variable al comienzo del programa controla el modo de operación:

```python
AUTOMATIC_MODE = False
```

- `False`: solicita `ENTER` antes de iniciar y antes de cada cambio de relé;
  al final permite repetir la secuencia.
- `True`: inicia y cambia todos los relés sin solicitar `ENTER`; al completar
  una ejecución restaura automáticamente el estado original y termina.

En ambos modos se mantienen las esperas, las cuentas regresivas y los pasos
simulados de presión y temperatura.

## Estado antes de comenzar

Al abrir el programa, primero se guarda el estado original y acto seguido se
apagan los 16 relés. El programa no solicita el `ENTER` de inicio hasta que las
dos Relay Plates han recibido la orden de apagado. Cada repetición vuelve a
apagar todos los relés antes de comenzar el primer paso.

## Pasos simulados

### Paso 11 — Presión

No lee la ADCplate. El terminal muestra en notación científica una presión
ficticia descendiendo desde `INITIAL_PRESSURE_TORR` hasta el vacío único
definido en `TARGET_VACUUM_TORR`. Con la configuración actual desciende desde
`7.600e+02 Torr` hasta `1.500e-02 Torr` durante 15 segundos.

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
[Address 0 | Relé 1] air_compressor: LISTO PARA CAMBIAR A ON / ENCENDIDO.
Presione ENTER:
[Address 0 | Relé 1] air_compressor: ON / ENCENDIDO
```

También aparecen el paso actual, las cuentas regresivas, los valores simulados,
los errores de comunicación y el aviso de finalización de la secuencia.

## Comportamiento al interrumpir

Si se presiona `Ctrl+C`, la secuencia se detiene, pero los relés conservan su
estado actual. El operador debe revisar el sistema antes de salir.

## Restauración al finalizar

Antes de iniciar, el programa lee y guarda el estado original de los 16 relés.
Cuando completa el paso 16, pregunta si el operador quiere repetir la secuencia:

- Escribir `SI` vuelve a ejecutar todos los pasos desde el comienzo.
- Presionar solamente `ENTER` restaura las dos Relay Plates exactamente a sus
  estados originales y finaliza el programa.

El estado inicial se guarda una sola vez, por lo que se conserva aunque la
secuencia se repita varias veces. La restauración final no ocurre si el programa
es interrumpido con `Ctrl+C`.

## Ejecución

```bash
python3 "Capstone 2/Start Up process1.0.py"
```
