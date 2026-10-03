# Node-RED SIM — GUI original dentro de Node-RED, sin placas

Esta carpeta es la simulación solicitada el 3 de octubre de 2026. No importa drivers Pi-Plates ni controla hardware real. `producto final` conserva su ejecución real. No ejecutar su `main.py` para esta prueba.

## Arranque

Requisitos: Python 3 y Node.js compatible con la versión de Node-RED instalada, npm. Desde esta carpeta:

```bash
npm ci
npm start
```

- Vacuum Controller: http://127.0.0.1:1880/dashboard/main
- Dashboard: http://127.0.0.1:1881/dashboard/main
- Panel de simulación: http://127.0.0.1:1880/dashboard/sim o http://127.0.0.1:1881/dashboard/sim (enlace «Panel de pruebas» en el banner amarillo).
- Editores Node-RED: `/red` en cada puerto.
- API Python simulada: 127.0.0.1:8001.

Ctrl+C detiene los tres procesos. Emergency enclava el paro; reiniciar la simulación para volver a comenzar. No se guardan estados entre ejecuciones. Si un puerto está ocupado, cierre esa instancia antes de iniciar. Los enlaces son locales: este paquete no está configurado para acceso desde otro equipo.

## Estructura modular («header files»)

| Archivo | Función |
|---|---|
| main_sim.py | Servidor simulado y ensamblaje de módulos |
| planta.py | Estado en memoria y evolución didáctica de la planta |
| manual_control.py | Mapa, permisos, órdenes y confirmación de relés simulados |
| temperaturas.py | Siete canales simulados tipo K y sus errores |
| presiones.py | Lecturas simuladas de corriente/voltaje y paquetes API |
| temperatura_agua.py / vacio.py | Conversiones y validaciones locales |
| startup.py / shutdown.py | Secuencias locales, condiciones y bloqueos |
| emergency_shutdown.py | Paro enclavado de la planta simulada |
| errores.py / hardware_bus.py | Diagnósticos y exclusión mutua local |
| masscontroll.py | Respuesta simulada cero al paro; función futura |
| vacuum_controller.html / dashboard.html y sus .js | Fuente de la GUI; build_dashboards.py los incrusta en ui-template |
| server.js | Instancia Node-RED y alojamiento de cada pantalla |
| flows-vacuum.json / flows-dashboard.json | Flujo activo de cada instancia: ui-template de la pantalla, página sim y proxy /api/* → Python |
| build_dashboards.py | Regenera ambos flujos desde los HTML/JS. Sobrescribe lo editado en /red |
| flows.json | Plantilla del proxy API para el generador; no es el flujo activo |
| launch.js | Arranca los tres procesos y coordina su cierre |

La carpeta es autónoma. Cada instancia Node-RED contiene su pantalla original (HTML, CSS y JavaScript) en un nodo ui-template de FlowFuse Dashboard 2, más la página «Panel de simulación» en el mismo dashboard. No hay Express sirviendo HTML ni iframe; Python solo expone la API en 8001. Python sigue ejecutando simulación y secuencias, conservando los módulos solicitados. No carga archivos de `producto final` ni necesita esa carpeta para ejecutarse. Los módulos `manual_control.py`, `temperaturas.py`, `presiones.py`, `vacio.py`, `temperatura_agua.py`, `startup.py`, `shutdown.py`, `emergency_shutdown.py` y `errores.py` mantienen la organización del producto. Los módulos de adquisición usan exclusivamente `planta.py`, en memoria. `main.py` también permite arrancar solo el backend simulado; `npm start` arranca el conjunto completo. El destino Node-RED está fijo al puerto 8001.

Las dos instancias tienen directorios de usuario separados en `.runtime`. Cada instancia usa su propio archivo versionado: flows-vacuum.json o flows-dashboard.json. Para editar: abrir /red, doble clic en el ui-template («Vacuum Controller (HTML/CSS/JS)», «Reactor Dashboard (HTML/CSS/JS)» o «Panel de simulación») y Deploy; se guarda en flows-*.json. Alternativa: editar los HTML/JS fuente y ejecutar `python3 build_dashboards.py`, que reemplaza lo editado en /red.

## Qué se puede probar

Control de los 16 relés; restricción de difusión con Medium válido <0.030 Torr; startup, shutdown, confirmaciones manuales del gas; bloqueos y Emergency; temperaturas, presiones y gráficas en ambas interfaces. Las esperas de 120 segundos del procedimiento se conservan: no se aceleraron las reglas de seguridad para la demostración.

El modelo didáctico comienza a 760 Torr y 24 °C. Ambas mecánicas con Diffuse A/B y Chamber A/B abiertas hacen tender la presión a 0.01 Torr. Ambas bombas de difusión calientes (≥121.11 °C), Gate A/B abiertas y bombeo mecánico activo permiten tender a 5e-7 Torr. Una cámara aislada conserva su presión en este modelo ideal; una fuga inyectada la hace tender a 10 Torr. No son constantes físicas del reactor.

Cada difusión encendida tiende a 135 °C; apagada vuelve a 24 °C. El compresor lleva aire a 120 PSI; chiller lleva coolant a 58 PSI, agua a 45 PSI, coolant a 10 °C y Water a 18 °C. Cool traps encendidos con chiller tienden a 8 °C. Las bobinas externas pueden calentarse desde el panel para probar sus indicadores, sin inventarles relés.

High genera voltaje a partir de la presión del modelo usando la inversa de la fórmula nominal local, solo entre 3e-9 y 1e-3 Torr; fuera de ese intervalo entrega un estado inválido simulado. Medium conserva sus límites de conversión. Esto permite probar el cruce de rangos y los mensajes sin inventar lectura válida fuera del rango. Validar contra la propia fórmula prueba coherencia de software, no exactitud del sensor real.

El gas manual simulado puede abrirse/cerrarse desde el panel con `gas_open`; abierto, el objetivo del modelo en alto vacío sube a 2e-5 Torr. La confirmación de gas del procedimiento sigue siendo una acción independiente del operador. `coils_on` activa calentamiento externo simulado. No representan un mass flow ni AutoVacío implementados.

Manual Gas Flow Control, AutoVacío y Gas Mass Flow Meter conservan su exclusión y visual deshabilitado. Rough A/B ya se muestran (ver abajo). MassControl simulado solo atiende la orden cero interna de Emergency; no ejecuta un DAC. Room implementado (DS18B20, puerto 9).

## Permisos manuales del procedimiento de startup 2026

Igual que `producto final/manual_control.py` (misma lógica; solo cambia el constructor, que usa `Planta`):

- Siempre habilitados: Air Compressor, Water Chiller, Booster Pump, Cool Trap A/B, Mechanical Pump A/B. Temporal: Buzzer.
- Diffuse Valve A/B ON: Air Compressor, Water Chiller, Booster Pump y Cool Trap A/B encendidos.
- Chamber Valve A/B ON: lo anterior más Diffuse Valve A/B.
- Gate Valve A/B ON: pasos 2-7, Mechanical Pump A/B y Diffusion Pump A/B encendidos; Medium 0.001-0.030 Torr; ambas difusiones 250-300 °F; Chamber Valve A/B apagadas.
- Diffusion Pump A/B ON: Medium < 0.030 Torr. OFF siempre permitido en todos.

El aviso del botón dice qué falta. Para probarlo en el panel de simulación: aplicar `{"overrides":{"medium_volts":0.6505149978,"Diffusion Pump A":135,"Diffusion Pump B":135},"faults":[]}` (20 mTorr, 275 °F).

```bash
python3 -m unittest test_manual_conditions   # reglas, sin servidor
python3 test_manual_sequence.py     # con npm start recién iniciado: recorre el startup a mano por Node-RED
```

## Room (lab temp) y alarma High room temperature

Igual que el producto final (`alarma_room.py` y `temperaturas.py`): Room es un DS18B20 en THERMOplate address 2, puerto 9. En la simulación ronda 21–22 °C. Si pasa de 29 °C, la alarma **High room temperature** enciende el Buzzer y ambas pantallas la muestran. Se desactiva al bajar a 28 °C o menos (histéresis de 1 °C) y entonces apaga el Buzzer, si lo encendió la alarma.

Para probarla: en el panel de simulación, botón «Room 30 °C (alarma)», o JSON `{"overrides":{"Room":30},"faults":[]}`. «Fallo sensor Room» simula una lectura inválida: conserva el estado de la alarma y muestra el error. «Restaurar modelo automático» vuelve a ~21.5 °C.

```bash
python3 test_room_alarm.py   # sin servidor
```

## Roughing Vacuum Gauges A/B (Rough Manifold)

Igual que el producto final (`vacio_rough.py`): Rough A en ADCplate 3/S4 y Rough B en S5. Se muestran solo como barras de 0-10 V en el panel Vacuum Levels (0 V = 10⁻³ Torr, 10 V = 1000 Torr). La lectura reservada del caudal del Aera pasó de S4 a S6.

En la simulación, ambas barras siguen la presión del modelo con una escala logarítmica didáctica: a 760 Torr marcan unos 9.8 V. Botones del panel: «Rough A 2.5 V / B 7.5 V», «Rough A fuera de rango (11 V)» y «Fallo sensor Rough B». Campos JSON: `rough_a_volts` y `rough_b_volts`.

```bash
python3 test_rough.py   # sin servidor
```

## Señales y fallos

El panel reemplaza toda la configuración anterior en cada aplicación. «Restaurar» limpia overrides y fallos. Campos: `medium_volts`, `high_volts`, `water_ma`, `air_ma`, `coolant_ma`, `pressure_water_ma`, `rough_a_volts`, `rough_b_volts`, `Room` y nombres exactos de termocuplas, por ejemplo `Diffusion Pump A`.

```json
{"overrides":{"medium_volts":0.6505149978,"Diffusion Pump A":135,"Diffusion Pump B":135},"faults":[]}
```

Ejemplo de sensor fallido: `{"overrides":{},"faults":["medium_volts"]}`. `relays` simula fallos de lectura/escritura de ambas placas: puede impedir confirmar el paro simulado. Restaurar comunicación no elimina el enclavamiento de Emergency.

Las conversiones Medium/High, RTD y presión se reutilizan. Los valores fuera de rango producen errores en lugar de mediciones normales. Los indicadores «SIMULACIÓN» identifican las pantallas.

## Prueba manual completa

1. Abrir las dos pantallas y el panel de pruebas.
2. Intentar difusión a presión ambiente: permanece bloqueada.
3. Fijar Medium 0.020 Torr: habilita difusión manual; comprobar que estado se refleja en Dashboard.
4. Reiniciar para probar startup desde estado inicial. Iniciarlo, esperar sus dos pausas de 120 s y evolución de sensores; confirmar gas al final.
5. Iniciar shutdown, confirmar gas cerrado y esperar los 120 s y enfriamiento de ambas bombas.
6. En otra ejecución iniciar startup y pulsar Emergency: salidas OFF y nuevas órdenes bloqueadas.
7. Provocar fallos de sensor/relés y revisar errores, condiciones de espera y falta de confirmación.

La simulación no valida el reactor físico. La migración de producción a Node-RED queda separada de este laboratorio.

Referencias de configuración: https://nodered.org/docs/user-guide/runtime/embedding y https://nodered.org/docs/user-guide/runtime/configuration

## Verificación realizada

3 de octubre de 2026, en puertos 2880/2881 (1880/1881 los ocupa el túnel SSH). Chromium headless cargó las tres páginas sin errores de consola. Se vieron los relés, temperaturas, presiones, vacío y el diagrama. Un clic real en Air Compressor (2880) se reflejó en 2881. Un clic real en «Medium 0.020 Torr» del panel respondió desde Python. Pasaron:

```bash
node test_nodered.cjs      # termina con Emergency enclavado; reiniciar después
python3 test_modules.py
python3 test_plant.py
```

No se recorrieron por la interfaz las esperas completas de 120 s del startup/shutdown.

## Alcance confirmado y pruebas del modelo

El usuario confirmó: solo el alcance actual, con todos sus procesos simulados. Las funciones futuras continúan deshabilitadas; Room se añadió el 3 de octubre de 2026. No se añadieron base de datos, mass flow operativo, AutoVacío ni Rough A/B.

`python3 test_modules.py` verifica startup y shutdown completos adelantando únicamente sus deadlines dentro de la prueba. `python3 test_plant.py` verifica evolución de bombeo y válvulas, calentamiento/enfriamiento, presión High dinámica, gas manual, fuga y fallo de lectura. Ambas pasaron. La aplicación mantiene los tiempos originales de espera. Los coeficientes térmicos y neumáticos son didácticos, no identificación física del reactor.

## Actualizar la copia que ya está en el Pi

1. Detener `npm start` en el Pi con Ctrl+C.
2. Copiar esta versión actualizada de `node red sim` al escritorio del Pi, conservando los archivos JSON de flujos y package-lock.json. Excluir node_modules, .runtime y __pycache__.
3. En SSH ejecutar:

```bash
cd "$HOME/Desktop/node red sim"
npm ci
npm start
```

4. Mantener el túnel SSH de puertos 1880/1881 y abrir las direcciones habituales. `/` redirige ahora a `/dashboard/main`, que carga FlowFuse Dashboard.
5. Editores de nodos: `http://127.0.0.1:1880/red` y `http://127.0.0.1:1881/red`. No se necesita importar los flujos manualmente.

Las pantallas son el mismo HTML/CSS/JS de antes dentro de ui-template; su CSS va limitado a la pantalla para no alterar Dashboard 2. Emergency está presente en ambas. Los permisos se validan en Python.

Documentación del componente: https://dashboard.flowfuse.com/getting-started.html
