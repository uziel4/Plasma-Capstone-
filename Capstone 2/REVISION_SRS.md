# Comparación del SRS con el alcance actual

Revisión: 1 de octubre de 2026. Documento comparado: **SRS oficial.pdf**, 49 páginas de contenido. Las páginas indicadas son las del archivo PDF, contando la portada como página 1.

Profesor, revisamos el SRS contra el código actual de `producto final`. La idea general de monitoreo y control de vacío coincide, pero el documento todavía incluye funciones que retiramos del alcance y diagramas de procedimientos anteriores. No basta con quitar el apéndice de base de datos.

Esta revisión compara funciones y código; no certifica el funcionamiento físico, la calibración ni la seguridad del reactor. Se revisaron también visualmente el diagrama de casos de uso y los diagramas de startup/shutdown. El PDF original no se modificó.

## Alcance que vamos a entregar

- Dos interfaces: Vacuum Controller para controles y lecturas; Dashboard para visualizar el sistema. La arquitectura prevista usa dos servidores Node-RED distintos, uno por interfaz; el código revisado todavía sirve ambas desde Python. Ver el apartado de Node-RED al final.
- Control de 16 relés, incluida la salida Buzzer, con consulta del estado registrado por la placa.
- Termocuplas K, temperatura Water por transmisor RTD, presiones Air/Coolant/Water y vacío Medium/High.
- Gráficas independientes de Medium y High con hasta 60 muestras temporales en memoria del navegador. No son históricos guardados.
- Startup y shutdown normal con pasos, condiciones, lecturas, esperas y confirmación manual del gas.
- Bloqueo de mandos manuales durante las secuencias; Emergency disponible.
- Paro de software enclavado, errores de lectura/comunicación y logs técnicos.
- Encendido manual de Diffusion Pump A/B condicionado a Medium válido y reciente menor de 0.030 Torr.

**Fuera del alcance de esta entrega:** base de datos, archivo histórico de mediciones, consulta/exportación de sesiones, regulación AutoVacío, control y medición operativos de mass flow, y Rough Manifold A/B. Manual Gas Flow Control, Automatic Vacuum, Vacuum Levels y Gas Mass Flow Meter conservan su diseño, deshabilitados y anunciados para grupos futuros. Tener sus módulos o pruebas en el repositorio no significa que las funciones estén habilitadas.

Startup automático y AutoVacío son distintos: el primero sí ejecuta una secuencia; el segundo sería la regulación continua de presión por gas y queda fuera del alcance.

## Matriz de requisitos funcionales

| SRS | Situación actual | Ajuste necesario |
|---|---|---|
| FR1, p.30: inicialización de todos los componentes | Parcial: `main.py` verifica relés antes de servir; ADC y THERMO manejan inicialización/errores al adquirir datos. Un fallo inicial de relés puede impedir abrir el servidor. | No prometer que cualquier fallo inicial aparecerá en el GUI. Distinguir errores de arranque en terminal y errores operativos en pantalla. |
| FR2, p.30: adquirir presión y temperatura por ADCplate | Implementado con dos placas de adquisición: ADCplate y THERMOplate. | Nombrar ambas; termocuplas por THERMO, RTD con transmisor por ADC I0. Room: DS18B20 en THERMOplate 2, puerto 9. |
| FR3, p.30: convertir señales | Implementado en `presiones.py`, `temperatura_agua.py`, `vacio.py`; THERMO entrega °C. | Conservar, identificando escalas y validación física pendiente. |
| FR4, p.30: monitoreo en tiempo real | Hay actualización periódica de los dos GUI. | Usar “monitoreo periódico”; no atribuir una garantía temporal de tiempo real duro. |
| FR5, p.30: detección de alarmas por umbrales | Parcial: validaciones de señal y condiciones específicas de secuencias/control manual. | No afirmar que hay un sistema general de límites operativos configurables por variable. |
| FR6, p.30: alarmas visuales | Hay errores y avisos visibles. Buzzer tiene control manual, sin disparo automático definido. | Diferenciar diagnóstico de fallos, condiciones de espera y alarmas operativas. No declarar alarma sonora automática implementada. |
| FR7, p.31: registrar todas las variables con fecha | Fuera de alcance. `logs/control.log` registra diagnósticos; no almacena todas las mediciones. | Retirar FR7 de requisitos de esta entrega o marcarlo explícitamente como futuro. No presentar los logs como cumplimiento de FR7. |
| FR8, p.31: interacción supervisada | Implementada para funciones activas. | Excluir paneles futuros y agregar confirmaciones manuales de gas. |
| FR9, p.31: activación de equipos por relés | Implementada para equipos asignados y secuencias. | Sustituir “cualquier equipo” por el mapa aprobado; aclarar que el estado de relé no confirma posición de válvula o giro de bomba. |
| FR10, p.31: detectar fallos de sensores/comunicación | Parcial: errores de comunicación, tipo/rango y datos vencidos en controles concretos. | No prometer detectar todo sensor desconectado: una señal errónea pero plausible puede pasar la validación. |

## Secciones que deben cambiar

| Ubicación | Qué debe corregirse |
|---|---|
| Abstract, pp.5-6; Scope, p.8 | Retirar registro histórico como función entregada. Precisar monitoreo y control del subsistema de vacío, no automatización completa de plasma. |
| 2.1.2, pp.18-20 | Sustituir “prototipo visual sin hardware”, diseño blanco/negro y eventos simulados por la arquitectura actual HTML/JS + Python con hardware real. Reemplazar capturas antiguas. Las gráficas activas son Medium/High, no dos gráficas de secciones A/B. No se identificó un indicador operativo de uptime como el prometido. |
| 2.1.3, p.21 | Eliminar “Data Storage and Memory (Database)” del alcance activo. El apartado promete almacenamiento en tiempo real, mientras el apéndice G dice que sería a petición: ambas versiones se retiran. |
| 2.3, pp.22-23 | Eliminar acceso rápido a históricos y tareas del usuario basadas en consultar registros experimentales. |
| 2.5.2 y 3.1.2, pp.26 y 28 | El documento fija Raspberry Pi 5; el equipo indicado en la conversación es Raspberry Pi 4 de 4 GB. Alinear la plataforma objetivo y dejar compatibilidad/validación real como verificación pendiente. Incluir THERMOplate. |
| 2.5.3 y 3.1.3, pp.27 y 29 | Quitar base de datos/históricos de dependencias. Conservar Python, Pi-Plates, navegador y logs técnicos. |
| 3.1.4, p.29 | Cambiar “I2C para ADC” por SPI de Pi-Plates, según `hardware_bus.py` y los drivers usados. No listar I2C/USB como integración de sensores implementada sin un dispositivo concreto. La sección 3.8.3 ya habla de SPI: resolver esa contradicción. |
| 3.3, p.31 | No cumple la promesa de máximo 1 segundo. Sensores esperan 1.5 s después de terminar cada consulta; relés se consultan cada 2 s y las peticiones tienen latencia/timeouts adicionales. Definir un objetivo de aceptación medible en el Pi; no sustituirlo por otra garantía sin medir. |
| 3.4, p.31 | ADC reemplaza adquisición analógica previa, pero no toda presencia de DAQC2: Emergency aún intenta escribir cero en su DAC. Documentar esta dependencia residual. |
| 3.5.1, p.32 | Sustituir “detectar cualquier fallo sin caer” por fallos concretos manejados; hay fallos de arranque que detienen el proceso. |
| 3.5.5, p.32 | No hay usuarios, login ni roles. Se sirve en localhost y se validan solicitudes, pero eso no equivale a autenticación de operadores. No afirmar control de acceso implementado. |
| 3.6, pp.33-34 | Diferenciar apagado normal con enfriamiento y paro inmediato de software. No prometer apagado físico completo garantizado, ni protección ante corte eléctrico/SIGKILL. |
| 3.7, p.34 | No hay pantalla para configurar límites de alarmas. Los parámetros existentes se definen en código. Reformular o dejar la configuración de alarmas como futura, según alcance acordado. |
| 3.8, pp.34-36 | Separar pruebas aisladas de software de pruebas con placas/sensores. Las pruebas con dobles de hardware no son un modo de simulación del producto. Evitar “garantiza” antes de validación física. |
| Apéndice A, pp.37-38 | Retirar Log Data, View Historical Data y Configure Alarm Thresholds de los casos de uso activos. Añadir casos explícitos de startup, confirmación manual de gas, shutdown normal y Emergency. |
| Apéndices B/C, pp.38-40 | Actualizar mapas a RELAYplate2 1/2, THERMO 2, ADC 3 y DAQC2 4 como dependencia residual de Emergency. Separar arquitectura activa de expansión futura; no inferir alimentación física comprobada desde el software. |
| Apéndice G, pp.48-49 | Sacar el modelo de base de datos del alcance entregable. Si se conserva, titularlo como propuesta futura no implementada. |

## Los diagramas de startup y shutdown necesitan reemplazarse

### Startup: apéndice E, pp.42-44

El dibujo todavía contiene Water Level Solenoid, comprobaciones de aire de 100 PSI y agua de 10 °C, temperatura de bombas mecánicas, difusión a 177 °C/350 °F, esperas de 5 segundos/5 minutos y controles de plasma/microondas. No corresponde a la secuencia vigente en `startup.py`.

La secuencia programada actualmente es:

1. Air Compressor ON y espera de 120 s.
2. Water Chiller ON y espera de 120 s.
3. Booster Pump, Cool Trap A/B, Diffuse Valve A/B, Chamber Valve A/B y Mechanical Pump A/B ON, por pasos.
4. Esperar Medium entre **0.001 y 0.030 Torr**, según la condición de startup existente.
5. Diffusion Pump A/B ON.
6. Esperar ambas temperaturas entre **250 y 300 °F** (aproximadamente 121.11-148.89 °C).
7. Chamber Valve A/B OFF y Gate Valve A/B ON.
8. Esperar confirmación de que el gas se ajustó manualmente; no mandar una consigna de mass flow.

No confundir esa condición del startup con el permiso del botón manual de difusión: este último exige **P < 0.030 Torr**, estrictamente, y dato de hasta 3 segundos de antigüedad. El SRS debe explicar ambas reglas tal como están, o resolver su diferencia con el responsable del procedimiento, sin cambiarla silenciosamente.

El RTD Water es monitor del agua del reactor, no una condición de temperatura del startup vigente. Rough A/B (S4/S5, barras 0-10 V) no participan del startup. Los relés locales son 1-8 por placa; corregir diagramas que asignan “switches 10-15” como si fueran números locales.

### Shutdown: apéndice F, pp.46-47

Conservar cierre de gas **manual con confirmación**, espera de 120 s, Gate Valve A/B OFF, Diffusion Pump A/B OFF, espera de **ambas bombas <=100 °F** (37.777… °C), Diffuse Valve A/B OFF, Mechanical Pump A/B OFF, Air Compressor OFF, Cool Trap A/B OFF, Booster Pump OFF y Water Chiller OFF.

Eliminar Water Level Solenoid. Agregar Booster Pump donde falta. Corregir asignaciones de relés. La comprobación del software es el registro de salida de la placa; el diagrama no debe llamarla confirmación mecánica de posición sin sensores de realimentación.

El diagrama propone reintentar cierre ante fallo; el programa detiene la secuencia ante una orden no confirmada y no reenvía automáticamente una orden incierta. Las condiciones de lectura pendientes esperan; no todas las clases de fallo se tratan igual.

## Hallazgo de implementación que no se resuelve editando el SRS

Aunque mass flow está fuera del alcance operativo, `emergency_shutdown.py` todavía llama `mass.set_percent(0)` en el paro y al cerrar `main.py`. Sin DAQC2 puede reportar error de mass flow y `confirmed: false`, aunque los relés sí se apaguen. El bucle continúa intentando apagar las demás salidas.

Por tanto, hoy no sería exacto afirmar “el producto no usa DAQC2 en ninguna circunstancia”. Esta revisión no modifica ese comportamiento: hay que decidir por separado si se conserva como acción residual de apagado o se retira de la configuración sin mass flow. Tampoco debe confundirse el paro inmediato con enfriamiento normal de bombas de difusión.

## Redacción sugerida para el alcance del SRS

> This release provides local monitoring and supervisory control of the reactor vacuum subsystem using Python and browser-based interfaces on a Raspberry Pi. It includes periodic pressure and temperature acquisition, relay control, independent Medium and High vacuum trend displays, guided startup and normal shutdown sequences, manual gas-operation confirmations, diagnostic messages, and a latched software emergency shutdown. Database storage, historical measurement retrieval, automatic vacuum regulation through gas flow, mass-flow control and measurement, and Rough Manifold A/B operation are excluded from this release. Their interface sections may remain visible as disabled placeholders for future student groups. Diagnostic logs and temporary chart samples are not an experimental database. Hardware validation remains required.

## Requisitos concretos que conviene incorporar

Estas propuestas describen el alcance actual; no son evidencia de validación física:

| ID propuesto | Requisito verificable |
|---|---|
| FR11 | Ejecutar startup por pasos, mostrando paso actual, condición pendiente, lecturas y tiempo restante cuando corresponda. |
| FR12 | Ejecutar shutdown normal con confirmación manual de gas y espera de enfriamiento de ambas bombas antes de apagar las mecánicas. |
| FR13 | Bloquear mandos manuales durante secuencias y mantener disponible Emergency. |
| FR14 | Rechazar ON manual de difusión si Medium no es válido, reciente y menor de 0.030 Torr; permitir OFF sujeto a bloqueos generales. |
| FR15 | Leer y graficar Medium/High independientemente; no sustituir errores por presión cero. La línea punteada es una referencia sin dato válido. |
| FR16 | Mostrar las tres secciones futuras (Vacuum Levels ya muestra Rough A/B) con su diseño y aviso de no habilitado, sin permitir operación ni lectura periódica del mass flow. |
| FR17 | Enviar apagado de software al cerrar el servidor normalmente o mediante señales manejadas; distinguirlo de cerrar una pestaña, pérdida de energía o terminación forzada. |

## Qué sigue siendo pendiente y no debe declararse terminado

- Validación física de señales, fórmulas, equipos y respuesta a órdenes.
- Validación física del DS18B20 de Room (puerto 9) y de la alarma High room temperature.
- Límites de otras alarmas operativas, si se mantienen como requisito.
- Medición de rendimiento, continuidad y visualización en la pantalla real del Pi.
- Decisión sobre la dependencia residual DAQC2 en Emergency al excluir mass flow.
- Los indicadores Field Coil A/B son tendencia de temperatura, no confirmación eléctrica de encendido.

La base de datos, AutoVacío y mass flow no deben aparecer aquí como obligaciones pendientes del grupo actual: quedaron fuera del alcance por indicación del usuario.

## Evidencia de código revisada

- [Servidor y API](main.py): rutas, localhost, logs y rechazo de órdenes de mass flow.
- [Relés y permisos](manual_control.py): addresses 1/2, Buzzer, condición manual de difusión y requisitos previos de Diffuse Valve A/B, Chamber Valve A/B y Gate Valve A/B.
- [Startup](startup.py), [shutdown](shutdown.py), [Emergency](emergency_shutdown.py): secuencias y límites reales.
- [Presiones](presiones.py), [termocuplas](temperaturas.py), [RTD Water](temperatura_agua.py), [vacío](vacio.py).
- [Vacuum Controller](vacuum_controller.html), [gráficas](vacio.js), [Dashboard](dashboard.js).
- [AutoVacío reservado](autovacio.py): reglas presentes, sin ciclo actuador conectado.

**Conclusión:** el SRS puede alinearse con el producto, pero todavía no coincide por completo. Deben corregirse el alcance, FR7, las promesas de alarmas/rendimiento, la descripción del GUI y los apéndices de procedimientos y base de datos antes de presentarlo como especificación vigente.

## Especificación técnica completa para incorporar al SRS

Este anexo complementa la matriz anterior. Incorporar adquisición y fórmulas en **3.1–3.2**, tiempos en **3.3**, restricciones y errores en **3.5–3.6**, comprobaciones en **3.8** y mapas en **apéndices B/C**. Actualizar también requisitos, diagramas y referencias internas. Las fórmulas describen el código revisado; los ejemplos son resultados matemáticos, no mediciones ni pruebas físicas realizadas.

### Mapa completo de entradas y unidades

| Variable | Placa/address | Canal | Adquisición | Unidad presentada |
|---|---|---|---|---|
| Coolant temperatura | THERMO/2 | 1 | Termocupla K | °C |
| Cool Trap A / B | THERMO/2 | 2 / 3 | Termocupla K | °C |
| Diffusion Pump A / B | THERMO/2 | 4 / 5 | Termocupla K | °C |
| Field Magnet A / B | THERMO/2 | 6 / 7 | Termocupla K | °C |
| Water temperatura | ADC/3 | I0 | Transmisor RTD, corriente en mA | °C, Dashboard |
| Water presión | ADC/3 | I1 | Corriente en mA | PSI en Vacuum Controller; bar en Dashboard |
| Coolant presión | ADC/3 | I2 | Corriente en mA | PSI / bar |
| Air presión | ADC/3 | I3 | Corriente en mA | PSI / bar |
| Medium Vacuum | ADC/3 | S0 | Voltaje, Terranova 906A | Torr / mbar |
| High Vacuum | ADC/3 | S1 | Voltaje negativo, GP270 | Torr / mbar |
| Room (lab temp) | THERMO/2 | 9 | DS18B20 digital, getTEMP | °C en Vacuum Controller; alarma > 29 °C |
| Rough Manifold A/B | ADC/3 | S4 / S5 | Voltaje 0-10 V (0 V = 1e-3 Torr, 10 V = 1000 Torr) | Barras 0-10 V en Vacuum Controller |

Canal 8 de THERMO libre. I0 es el identificador de entrada del ADC; no es GPIO ni pin físico 12 del Raspberry. No deducir conexiones físicas del RTD directamente al ADC: el ADC recibe la corriente del **transmisor**.

### Temperaturas por termocupla

Archivo: `temperaturas.py`. Lectura: `getTEMP(2, canal, 'c')`. Se configura tipo K y rechazo de ruido de red de **60 Hz**. La biblioteca entrega Celsius; no se aplica conversión de mA a estas temperaturas.

Se aceptan números finitos en **−200 ≤ T ≤ 1372 °C**. Son límites de plausibilidad configurados para K, no límites seguros de operación. Valores no numéricos, no finitos, fuera de rango o errores de comunicación producen error del canal y temperatura no disponible. Una temperatura de 419 °C puede pasar esta comprobación aunque sea incorrecta para un equipo a temperatura ambiente: el SRS no debe prometer detectar todos los errores plausibles.

### RTD Water: corriente a temperatura

Archivo: `temperatura_agua.py`, funciones `leer_corriente` y `calcular_celsius`.

```text
I = getADC(3, 'I0')     [mA]
T [°C] = (I − 4) × 6.25
```

| Corriente | Temperatura calculada |
|---:|---:|
| 4 mA | 0 °C |
| 8 mA | 25 °C |
| 12 mA | 50 °C |
| 16 mA | 75 °C |
| 20 mA | 100 °C |

Se exige **4 ≤ I ≤ 20 mA**, valor numérico y finito. No se extrapola fuera de ese rango ni se convierte un fallo en 0 °C. En la respuesta de error de este módulo, `ma` y `celsius` quedan nulos. Códigos: `WATER_TEMP_VALUE`, `WATER_TEMP_RANGE`, `WATER_TEMP_READ`. Revisar respectivamente formato/respuesta, corriente/escala del transmisor y comunicación/canal.

Water corresponde al agua del reactor y es independiente de Coolant. Room no usa este RTD. Water se monitorea; no condiciona el startup vigente.

Room (lab temp): DS18B20 en THERMOplate 2, puerto 9, leído con `getTEMP(2, 9, 'c')`. El laboratorio ronda 21–22 °C. Si Room > 29 °C se activa la alarma **High room temperature**: `alarma_room.py` enciende el Buzzer y ambos GUI la muestran; se desactiva al bajar a ≤ 28 °C (histéresis de 1 °C) y apaga el Buzzer si lo encendió la alarma. Con Emergency activo no acciona el Buzzer.

### Presiones Air, Coolant y Water

Archivo: `presiones.py`. ADC address 3 se identifica, inicializa y configura en modo `HIGH`; espera un segundo antes de las primeras lecturas.

Para las tres entradas se usa la misma escala configurada:

```text
P [PSI] = max(0, ((I [mA] − 4) / 16) × 232)
P [bar] = P [PSI] / 14.5037738
```

| Corriente | Presión calculada |
|---:|---:|
| 4 mA | 0 PSI |
| 8 mA | 58 PSI |
| 12 mA | 116 PSI |
| 16 mA | 174 PSI |
| 20 mA | 232 PSI |

La función limita resultados negativos a cero, pero **no limita el máximo a 232 PSI**. Fuera de 4–20 mA conserva el cálculo acompañado de `PRESS_RANGE`; no es una medición normal confiable. Ejemplos: 3 mA produce 0 PSI con error; 21 mA produce 246.5 PSI con error. Esto difiere del RTD, que rechaza la conversión fuera del rango.

`PRESS_INIT`: revisar identificación/address, SPI y biblioteca. `PRESS_READ`: revisar comunicación y canal. `PRESS_VALUE`: respuesta no numérica/no finita. `PRESS_RANGE`: revisar corriente, transmisor, alimentación y escala. La equivalencia 4–20 mA a 0–232 PSI es la configuración actual y necesita contrastarse con los equipos físicos.

### Medium Vacuum: Terranova 906A

Archivo: `vacio.py`, función `terranova906a_a_torr`. Entrada **ADC 3, S0**.

```text
P [mTorr] = 10^(2 × V)
P [Torr]  = 10^(2 × V − 3)
```

Se acepta solamente voltaje numérico, finito y **0 < V < 3 V**. El código trata los extremos como estados no utilizables para presión: 0 V corresponde a LO y aproximadamente 3 V a OFF/HI según el comentario de la implementación. No se deben interpretar esos extremos como mediciones normales.

| Voltaje | Resultado en Torr |
|---:|---:|
| 0.5 V | 1.0 × 10^-2 |
| 1.0 V | 1.0 × 10^-1 |
| 1.5 V | 1.0 × 10^0 |
| 2.0 V | 1.0 × 10^1 |
| 2.5 V | 1.0 × 10^2 |

El intervalo matemático de presión con esos límites estrictos es **1.0 × 10^-3 < P < 1.0 × 10^3 Torr**. No confundirlo con una certificación de exactitud del instrumento. **No usar la fórmula antigua `10^(2V − 11)`** para describir el Medium actual.

`VAC_VALUE`: dato inválido; `VAC_TN906_STATE`: voltaje no utilizable; `VAC_READ`: fallo de adquisición; `VAC_RANGE`: cálculo no representable. Una señal plausible no demuestra por sí sola que el sensor esté conectado correctamente.

### High Vacuum: Granville Phillips 270

Archivo: `vacio.py`, función `gp270_a_torr`. Entrada **ADC 3, S1**. Usar GP270, el modelo del manual aportado, no GP207.

La implementación nominal por tramos es:

```text
U = −V
n = max(0, min(4, ceil(U) − 1))
P [Torr] = (U − n) × 10 × 10^(n − 8)
```

`ceil` redondea hacia arriba al entero siguiente. Los extremos enteros se asignan al final del tramo anterior.

| Magnitud U [V] | Fórmula equivalente en Torr |
|---|---|
| 0 < U ≤ 1 | U × 10^-7 |
| 1 < U ≤ 2 | (U − 1) × 10^-6 |
| 2 < U ≤ 3 | (U − 2) × 10^-5 |
| 3 < U ≤ 4 | (U − 3) × 10^-4 |
| 4 < U ≤ 5 | (U − 4) × 10^-3 |

| Voltaje aplicado | Resultado del código en Torr |
|---:|---:|
| −0.5 V | 5.0 × 10^-8 |
| −1.0 V | 1.0 × 10^-7 |
| −1.5 V | 5.0 × 10^-7 |
| −2.0 V | 1.0 × 10^-6 |
| −2.5 V | 5.0 × 10^-6 |
| −3.0 V | 1.0 × 10^-5 |
| −3.5 V | 5.0 × 10^-5 |
| −4.0 V | 1.0 × 10^-4 |
| −4.5 V | 5.0 × 10^-4 |
| −5.0 V | 1.0 × 10^-3 |

Estos ejemplos documentan el cálculo programado, no una curva calibrada. La expresión reinicia el factor lineal al cambiar de tramo; **no debe suponerse continuidad ni una relación global monótona sin validar las transiciones del controlador**. Contrastar especialmente los cambios de rango con el manual y mediciones físicas antes de usarla como señal de regulación.

Validaciones:

- Datos no numéricos o no finitos: `VAC_VALUE`.
- −12 ≤ V ≤ −10 V: `VAC_GP270_STATE`, estado inválido del controlador.
- Fuera de −5 a 0 V, salvo el caso anterior: `VAC_GP270_RANGE`.
- 0 V: `VAC_GP270_ZERO`; no representa vacío perfecto.
- Lectura fallida: `VAC_READ`.

Ante error, presión nula y diagnóstico. Se conserva el voltaje original si es numérico y finito. Revisar voltaje real respecto al común, entrada S1, estado del controlador y comunicación; no ocultar el error sustituyéndolo por cero Torr.

### Unidades y temperaturas de los procedimientos

```text
mTorr = Torr × 1000
mbar = Torr × 1.333223874
°C = (°F − 32) × 5 / 9
°F = °C × 9 / 5 + 32
```

| Condición | Equivalencia |
|---|---|
| Startup Medium | 1.0 × 10^-3 a 3.0 × 10^-2 Torr, límites incluidos en la secuencia |
| Encendido manual difusión | 0 < P < 3.0 × 10^-2 Torr |
| Startup difusión, ambas bombas | 250–300 °F = 121.111…–148.888… °C |
| Shutdown difusión, ambas bombas | ≤100 °F = ≤37.777… °C |

El programa compara los límites calculados, no los valores redondeados del texto. Las secuencias aceptan paquetes con antigüedad entre 0 y 15 segundos; el permiso manual de difusión exige entre 0 y 3 segundos. Se requiere lectura numérica, finita y sin error. El startup admite matemáticamente 0.001 Torr, pero el lector Medium excluye 0 V y por tanto no entrega ese extremo exacto como medición válida: documentar esta diferencia, sin modificarla silenciosamente.

### Tendencia térmica Field Coil A/B

Archivo: `dashboard.js`. Se usa Field Magnet A/B de THERMO 6/7, respectivamente.

```text
q_actual = Math.round(T_actual × 10)
Subiendo = q_actual > q_anterior
```

Se comparan lecturas nuevas separadas como máximo por 15 segundos. Primera lectura, dato inválido o falta de comparación válida: estado desconocido. Si no sube: temperatura estable o bajando. El cálculo compara temperaturas redondeadas a décimas; no calcula una velocidad mínima en °C/s y no confirma alimentación eléctrica.

### Mapa completo de salidas para tablas y diagramas

| Address | Relé | Equipo |
|---:|---:|---|
| 1 | 1 | Air Compressor |
| 1 | 2 | Water Chiller |
| 1 | 3 | Booster Pump |
| 1 | 4 | Cool Trap A |
| 1 | 5 | Cool Trap B |
| 1 | 6 | Diffuse Valve A |
| 1 | 7 | Diffuse Valve B |
| 1 | 8 | Chamber Valve A |
| 2 | 1 | Chamber Valve B |
| 2 | 2 | Mechanical Pump A |
| 2 | 3 | Mechanical Pump B |
| 2 | 4 | Diffusion Pump A |
| 2 | 5 | Diffusion Pump B |
| 2 | 6 | Gate Valve A |
| 2 | 7 | Gate Valve B |
| 2 | 8 | Buzzer |

Water Chiller está habilitado. Sustituir Microwave Cooling por Buzzer en todo el SRS. Main Valve del Aera no es uno de estos relés. Mantener las restricciones de secuencias y emergencia al describir los permisos manuales; poder mandar OFF no significa poder saltarse esos bloqueos generales.

Diffuse Valve A/B: el ON manual exige Air Compressor, Water Chiller, Booster Pump y Cool Trap A/B encendidos, según los pasos 2, 4, 5 y 6 del procedimiento de startup 2026 (Water Level Solenoid excluido). OFF sigue permitido. La condición usa el estado registrado en los relés, no las esperas de 2 minutos ni la respuesta física del equipo.

Chamber Valve A/B: el ON manual exige, además, Diffuse Valve A y B encendidas (paso 7). OFF sigue permitido.

Gate Valve A/B (paso 15): el ON manual exige los pasos previos del startup: equipos de los pasos 2-7, Mechanical Pump A/B (9) y Diffusion Pump A/B (12) encendidos; Medium entre 0.001 y 0.030 Torr (11); ambas Diffusion Pump entre 250 y 300 °F (13); Chamber Valve A/B apagadas (14). Lecturas válidas de hasta 3 s. OFF sigue permitido. Bajo 0.001 Torr o sobre 300 °F el ON manual queda bloqueado, por seguir el documento literalmente. Buzzer es el único permiso temporal restante.

### Arquitectura, actualización y datos

- `main.py`: servidor Python local; HTML/JavaScript consulta API y envía órdenes. Abrir HTML en Live Server no conecta con el control de Python.
- `/api/temperatures`: termocuplas, errores y fecha.
- `/api/pressures`: presiones, RTD Water, Medium/High, errores y fecha; `mass_flow` queda nulo.
- `/api/relays`: estados registrados y permisos manuales.
- Rutas de startup, shutdown y Emergency: secuencias y acciones diferenciadas.
- Rutas de mass flow: no habilitadas para operación. Su script de interfaz no se carga para ejecutar controles.
- `hardware_bus.py`: serializa accesos SPI de este servidor. No coordina otros programas externos que accedan a las mismas placas.
- Caché de lecturas ADC/THERMO: aproximadamente un segundo; no equivale a frecuencia garantizada de pantalla.
- Consultas de sensores: espera de 1.5 segundos después de la respuesta; control manual de relés, aproximadamente dos segundos. Agregar latencia y tiempos de espera de comunicación al evaluar rendimiento.
- Gráficas: muestras temporales en memoria, sin base de datos. Un dato inválido no es una medición de cero; la línea punteada sin dato es solo una referencia visual.
- `errores.py` y logs técnicos: diagnóstico; no registro experimental completo.

### Fórmulas reservadas: mass flow y AutoVacío, fuera de entrega

Incluir este apartado **solo como diseño futuro**, no en requisitos obligatorios ni criterios de aceptación del producto activo.

El módulo reservado `masscontroll.py` contiene:

```text
Caudal medido [%] = V_entrada × 20
Caudal medido [SCCM] = (V_entrada / 5) × 5000
Consigna [V] = porcentaje / 20
Consigna [V] = (SCCM / 5000) × 5
Límite DAC = 4.095 V
Límite equivalente = 81.9 % = 4095 SCCM
```

La escala configurada es 5000 SCCM. El módulo admite solicitudes de 10–5000 SCCM y cero para OFF, pero rechaza las superiores a 4095 por el límite de salida. No presentar 5000 SCCM como consigna alcanzable con esa salida directa. La consigna se redondea a 0.001 V y se compara con el registro DAC con tolerancia de 0.002 V; esto no comprueba el caudal físico.

Conexiones reservadas: DAQC2/4 DAC0 a entrada de consigna pin 6 del Aera; salida pin 2 a ADC/3 S6 (movida de S4). El modelo indicado más recientemente por el usuario es FC-PA780C; el comentario del módulo aún menciona FC-PA7800. Registrar esa diferencia de identificación si se conserva el diseño futuro. El comportamiento del pin 1 no está confirmado: no afirmar que llevarlo a GND cierra la válvula sin evidencia del modelo.

AutoVacío reservado define, para presión P, objetivo O y tolerancia δ:

```text
P < O − δ → aumentar gas
P > O + δ → reducir gas
En otro caso → mantener
```

No es un PID ni un ciclo actuador operativo. `selector_vacio.py` tiene estas reglas reservadas:

- Medium válido por encima de **1.0 × 10^-3 Torr**, hasta 1000 Torr, tiene prioridad.
- Si no se cumple lo anterior, High válido entre **3.0 × 10^-9 y 1.0 × 10^-3 Torr**, incluidos, puede seleccionarse.
- En el límite exacto 1.0 × 10^-3 Torr, Medium sirve como alternativa si High no está disponible.
- Sin lectura elegible: error. Paquetes nuevos, numéricos y con antigüedad de 0–3 s; no aceptar repetidos.
- No hay dos umbrales distintos de histéresis implementados. No describir este selector como un regulador habilitado ni como un mecanismo que desactiva la adquisición de una gráfica.

La existencia de estos cálculos no cambia su exclusión del alcance. La única dependencia operativa residual identificada es la orden cero al mass flow desde Emergency, descrita antes y pendiente de decisión separada.

### Criterios de comprobación para actualizar la sección 3.8

Presentar los siguientes como comprobaciones requeridas, no como resultados físicos ya obtenidos:

1. Verificar los ejemplos de conversión anteriores y rechazo de entradas inválidas; distinguir resultados matemáticos de calibración.
2. Comprobar temperatura Water: 4/12/20 mA corresponden a 0/50/100 °C; fuera del rango, error.
3. Comprobar presión: 4/12/20 mA corresponden a 0/116/232 PSI; fuera de rango, aviso de no confiable.
4. Validar Medium y High frente a instrumentos reales, especialmente estados y transiciones GP270.
5. Verificar permiso manual de difusión con presión inferior, igual y superior a 0.030 Torr, datos vencidos y errores. Verificar que Diffuse Valve A/B no encienden en manual si falta cualquiera de Air Compressor, Water Chiller, Booster Pump o Cool Trap A/B, y que OFF sigue disponible. Verificar que Chamber Valve A/B no encienden si falta cualquiera de esos equipos o Diffuse Valve A/B. Verificar que Gate Valve A/B no encienden si falta un paso previo, si Chamber A/B están encendidas, si Medium sale de 0.001–0.030 Torr o si una Diffusion Pump sale de 250–300 °F; incluir límites exactos y lecturas vencidas.
6. Verificar startup y shutdown por pasos con las dos temperaturas requeridas, confirmación manual del gas y tiempos de espera.
7. Verificar que Emergency permanece accesible durante ambas secuencias y que una orden incierta no se repite automáticamente.
8. Verificar que los tres paneles futuros no permiten acciones, que no se consulta S6 para caudal, que Rough A/B (S4/S5) muestran 0-10 V y que las gráficas Medium/High siguen funcionando.
9. Medir latencia y presentación en Raspberry Pi 4 de 4 GB; no declarar cumplimiento de un segundo sin resultados.
10. Comprobar respuesta física de cada equipo por separado del registro del relé. Documentar la dependencia residual DAQC2 antes de afirmar apagado confirmado sin esa placa.

### Instrucción para quien edite el SRS

Usar toda esta revisión para sustituir texto, requisitos, tablas, figuras y referencias internas, conservando el idioma inglés y formato académico del SRS. No limitar la actualización a agregar este anexo al final: corregir los apartados originales identificados. Actualizar índice y numeración después de los cambios. Separar claramente software implementado, funciones excluidas, discrepancias pendientes y validación física. No inventar capturas actuales, resultados de pruebas, calibración o garantías de seguridad.


## Arquitectura prevista: dos servidores Node-RED, uno por dashboard

**Actualización de alcance solicitada por el usuario:** las dos interfaces se alojarán en **dos servidores/instancias distintos de Node-RED**:

| Instancia | Interfaz alojada | Responsabilidad |
|---|---|---|
| Node-RED 1 | Vacuum Controller | Presentar lecturas y controles habilitados; enviar solicitudes de control al backend Python |
| Node-RED 2 | Dashboard del reactor | Presentar las lecturas y estados del sistema; conservar el acceso a Emergency previsto para ambos GUI |
| Backend Python compartido | API y módulos de hardware | Adquirir sensores, ejecutar órdenes, aplicar bloqueos y ejecutar startup, shutdown y Emergency |

Dos servidores Node-RED no significa necesariamente dos Raspberry Pi. Pueden ser instancias en el mismo equipo con puertos diferentes o en equipos distintos. **Todavía no se han definido los equipos, puertos ni direcciones de despliegue.** No inventar esas asignaciones en el SRS.

### Estado actual frente al objetivo

Actualmente `main.py` sirve las dos interfaces y la API. Esta actualización documenta la **arquitectura objetivo**, no una migración Node-RED ya implementada ni probada. Los textos anteriores que describen HTML/JavaScript servido por Python representan el estado del código revisado.

La separación propuesta conserva un único backend Python como responsable del hardware. Ambas instancias Node-RED comparten las mismas lecturas, estados de secuencia y bloqueos mediante su API. No iniciar dos copias independientes del controlador Python ni duplicar los ciclos de adquisición y control por tener dos interfaces.

Recorrido previsto:

```text
Navegador → Node-RED 1 (Vacuum Controller) → API Python → módulos → placas
Navegador → Node-RED 2 (Dashboard)         → API Python → módulos → placas
```

Node-RED aloja e integra las interfaces; las fórmulas, validaciones y secuencias descritas en este documento permanecen en los módulos Python, salvo que se apruebe expresamente otra distribución. La separación de servidores no habilita base de datos, AutoVacío ni mass flow.

### Cambios específicos en el SRS

- **Abstract/Introduction, pp.5–6, y Scope, p.8:** describir dos interfaces alojadas en instancias distintas de Node-RED y un backend Python compartido. Identificar la integración como pendiente de implementación/validación.
- **2.1.2, pp.18–20:** explicar qué interfaz pertenece a cada instancia. No afirmar que ambas se alojarán en el mismo servidor web Python como arquitectura final.
- **2.5.3 y 3.1.3, pp.27 y 29:** añadir Node-RED y su entorno Node.js a las dependencias previstas, además de Python, Pi-Plates y navegador. Las versiones se fijarán al implementar; no atribuir una versión instalada sin comprobarla.
- **3.1.4, p.29:** documentar comunicación HTTP/JSON con la API Python para lecturas, órdenes y estado de procesos. Diferenciar esta comunicación de SPI entre Python y las placas.
- **3.3, p.31:** evaluar rendimiento con las dos instancias y navegadores funcionando; no asegurar consumo de memoria ni latencia antes de medir en el equipo destino.
- **3.5, p.32:** definir visibilidad de pérdidas de comunicación y estados desconocidos. Los bloqueos deben aplicarse en Python para todas las interfaces; una segunda instancia no puede eludirlos.
- **3.6, pp.33–34:** conservar Emergency accesible desde ambas interfaces. Reiniciar o cerrar Node-RED no equivale por sí solo a ejecutar el apagado de Python; documentar ese comportamiento sin prometer un paro automático adicional no implementado.
- **3.8, pp.34–36:** agregar pruebas de acceso a cada interfaz, comunicación con la API, coherencia de estados, bloqueo durante secuencias y Emergency desde ambas instancias.
- **Apéndices B/C, pp.38–40:** representar dos servidores Node-RED conectados a un backend Python compartido y este a las placas por SPI. No dibujar acceso directo duplicado de ambas instancias al hardware.

### Integración pendiente en el producto

1. Configurar las dos instancias Node-RED y alojar una interfaz en cada una.
2. Definir URLs y puertos, y adaptar las rutas relativas `/api/...`: desde Node-RED ya no apuntan automáticamente a Python. Configurar encaminamiento/proxy a la API o una integración explícita equivalente.
3. Revisar validación de origen y acceso del servidor Python. La configuración actual de localhost no basta si Node-RED se ejecuta en otro equipo. No desactivar indiscriminadamente las comprobaciones para resolver la conexión.
4. Mantener un único controlador del hardware y comprobar que las dos interfaces reciben estados coherentes, incluidos procesos en curso y Emergency enclavado.
5. Verificar el comportamiento al perder conexión o reiniciar una instancia, sin repetir automáticamente órdenes cuyo resultado no está confirmado.

### Texto en inglés para incorporar al SRS

> The target deployment shall host the Vacuum Controller and the reactor Dashboard on two separate Node-RED server instances, one instance per interface. Both instances shall communicate with a shared Python backend responsible for hardware acquisition, engineering-unit conversions, command validation, relay control, startup, normal shutdown, and software emergency shutdown. Hardware access shall remain centralized in the Python backend. Deployment hosts, ports, and API routing remain to be defined. The currently reviewed implementation serves both interfaces directly from Python; the two-instance Node-RED integration is planned and has not yet been implemented or validated. This architectural change does not introduce database storage, automatic vacuum regulation, or operational mass-flow features into the current scope.


## Actualización del 3 de octubre: laboratorio Node-RED simulado

Se agregó `../node red sim`, separado del producto real: dos instancias Node-RED (1880/1881) conectadas a un backend Python exclusivamente simulado (8001). Reutiliza interfaces y módulos de reglas; sustituye adquisición y salidas por una planta en memoria. Incluye panel de señales/fallos, flujos y guía de ejecución. La integración HTTP de ambas instancias fue probada; la validación visual sigue pendiente. Esto no equivale a migración de producción ni validación de hardware. La simulación fue solicitada expresamente para esta fase; no cambia las exclusiones de mass flow y AutoVacío del producto activo. Ver [guía del laboratorio](../node%20red%20sim/README.md).

El laboratorio `node red sim` ahora es autónomo: tiene copias locales de las interfaces y módulos, y adquisición simulada separada por módulo. No necesita importar `producto final`.


### Corrección: interfaces nativas Node-RED en el laboratorio

La simulación ahora carga widgets nativos de FlowFuse Dashboard 2, definidos en `flows-vacuum.json` y `flows-dashboard.json`, editables desde `/red`. Los HTML anteriores dejaron de ser las pantallas servidas por Node-RED. Python mantiene la planta simulada y los módulos de secuencias. Se probaron acciones de widgets mediante Socket.IO en ambas instancias; la revisión visual continúa pendiente. Este cambio solo afecta al laboratorio simulado, no demuestra migración del producto conectado a hardware.
