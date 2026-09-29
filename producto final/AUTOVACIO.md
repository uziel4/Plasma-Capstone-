# AutoVacio: alcance y dudas pendientes

AutoVacio es una funcion independiente del [startup 2026](STARTUP_2026.md).
El startup termina con regulacion **manual** del gas; no activa AutoVacio.

## Lo definido

AutoVacio seleccionara la lectura segun el rango de vacio: Medium (Terranova 906A, ADC3/S0) en rango medio y High (GP270, ADC3/S1) en alto vacio. El selector por rango esta implementado sin exigir concordancia entre sensores; ver SELECCION_VACIO.md para rangos y limites. Solo se podran usar lecturas validas.

Las bombas mecanicas A/B permanecen encendidas durante AutoVacio, incluso al
alcanzar el objetivo. Menor presion significa mas vacio.

| Lectura respecto al objetivo y tolerancia | Ajuste |
|---|---|
| Presion menor | Aumentar gas para subir la presion |
| Presion mayor | Reducir gas para bajar la presion |
| Dentro de la tolerancia | Mantener consigna |

El porcentaje de caudal no representa la apertura mecanica de la valvula.

## Lo implementado

- `autovacio.py` calcula ABRIR_MAS, CERRAR_MAS o MANTENER. No envia ordenes ni arranca bombas.
- ON automatico permanece deshabilitado; falta el ciclo de regulacion.
- `masscontroll.py` y `masscontroll.js` ya permiten mando manual y lectura del Aera.
- Medium es Terranova 906A en ADC3/S0; High es GP270 en ADC3/S1. Se conservan las formulas confirmadas, documentadas en CONFIGURACION.md.
- Rough A/B pertenecen a otro grupo: en blanco, sin lecturas ni barras de progreso activas.
- Los objetivos del GUI no accionan hardware. El campo automatico SCCM sigue pendiente de la escala.

| Funcion | Conexion |
|---|---|
| Mechanical Pump A | RELAYplate2 address 1, rele 2 |
| Mechanical Pump B | RELAYplate2 address 1, rele 3 |
| Consigna Aera | DAQC2 address 4, DAC0 → pin 6 |
| Caudal Aera | Pin 2 → ADCplate address 3, S4 |

Main Valve es la valvula interna del Aera. ON aplica la consigna seleccionada;
OFF manda cero. No se usa un rele adicional ni apertura total forzada.
El mando directo llega a 81.9% por el limite de 4.095 V del DAC.

## Dudas de AutoVacio

- Seleccion definida: High valido entre 3e-9 y 0.001 Torr; Medium valido > 1 × 10⁻³ Torr tiene prioridad para regresar. El regreso usa Medium valido > 1 × 10⁻³ Torr; ver SELECCION_VACIO.md.
- Tolerancia alrededor del objetivo y tiempo para considerar estable la lectura.
- Magnitud e intervalo de los ajustes; limites del caudal y significado del flujo deseado (inicial o maximo).
- Condiciones para entrar al modo automatico, caudal durante evacuacion y controles manuales que se bloquearan.
- Estado del caudal y bombas al salir a manual.
- Respuesta ante perdida de sensor, comunicacion o caudal insuficiente. La espera indefinida acordada para startup no define por si sola estas respuestas de regulacion.

## Dudas del equipo de mass flow

1. Modelo completo/MULTI, gas seleccionado y fondo de escala activo para convertir porcentaje a SCCM.
2. Configuracion normal del pin 1 y variante normalmente abierta/cerrada; debe seguir la consigna del pin 6.
El usuario confirma conservar el limite de consigna de 81.9% (4.095 V). No queda pendiente adaptar la salida a 100%.

La fuente ±15 V la prepara el equipo del usuario. Las conexiones de señal ya
estan asignadas; faltan la comprobacion de retornos y pruebas fisicas de consigna,
caudal y cierre con cero. Estas pruebas no son una duda sobre control manual o automatico.

## Errores y apagado

- AUTO_CONFIG: el modo automatico no esta integrado o faltan sus parametros. No se resuelve solo cambiando una bandera.
- AUTO_VALUE: presion, objetivo o tolerancia no numericos, no finitos o fuera del rango admitido.
- El paro de software manda cero al Aera y OFF a los 16 reles; bloquea nuevas ordenes hasta reiniciar. Tambien se ejecuta al cerrar main.py, no al cerrar una pestaña.
- No cubre perdida de alimentacion ni SIGKILL ni confirma cierre mecanico. Falta validar fisicamente la respuesta y la secuencia de enfriamiento.

Detalles: [EMERGENCY_SHUTDOWN.md](EMERGENCY_SHUTDOWN.md),
[CONEXIONES.md](CONEXIONES.md) y [PENDIENTES.md](PENDIENTES.md).

## Conversion Medium actualizada al manual

Se aplica `P(Torr)=10^(2V - 3)` en S0. Los estados LO/OFF/HI no se interpretan como presion valida. Detalles, ejemplos y limites del cambio Medium/High en [SELECCION_VACIO.md](SELECCION_VACIO.md). La formula esta implementada y probada en software; el selector por rango esta implementado; el regreso usa Medium valido > 1 × 10⁻³ Torr, sin esperar un valor superior al rango de High. Falta validacion fisica. AutoVacio no se habilita con este cambio.
