# Producto final — Manual Control

## Definiciones vigentes

- Low/Medium: Terranova 906A, ADCplate 3/S0, `P(Torr) = 10^(2V - 3)`.
- High: Granville-Phillips 270, el del manual recibido, ADCplate 3/S1; conserva `gp270_a_torr`.
- Medium usa ahora la formula del manual Terranova 906A, por instruccion del usuario. High conserva su conversion GP270. Falta validacion fisica.
- Rough Manifold A/B son para otro grupo: quedan en blanco, sin lecturas activas de S2/S3.
- Reactor Water Line Temperature es el RTD en ADC3/I0, solo para visualizar en Dashboard, sin condicionar el startup.
- Coolant es distinto de Water. Room sigue sin sensor definido.
- El startup vigente es [STARTUP_2026.md](STARTUP_2026.md): Medium para 30–1 mTorr, esperar si no se cumple una condicion o falla la lectura, y regulacion final del gas manual.
- Water Level Solenoid queda excluido. Las fuentes de plasma pertenecen a otro grupo.


Mapa de cableado de todos los modulos y dudas: [CONEXIONES.md](CONEXIONES.md).

Archivo de configuracion y funciones: `manual_control.py`.
Servidor principal: `main.py`. El GUI llama al servidor mediante `manual_control.js`.

## Stack y entradas actuales

| Placa | Address | Funcion |
|---|---|---|
| RELAYplate2 | 0 | Reles 1–8 |
| RELAYplate2 | 1 | Reles 1–8 |
| THERMOplate | 2 | Termocuplas |
| ADCplate | 3 | Corrientes y voltajes analogicos |

**Actualizacion del stack:** DAQC2plate address 4 destinada a la salida analogica de consigna del mass flow. DAC0 asignado e integrado para consigna porcentual. Las lecturas de vacio permanecen en ADCplate address 3.

| Senal | Placa/address | Entrada | Indice logico ADC | Unidad / estado |
|---|---|---|---|---|
| Temperatura Water | ADCplate / 3 | I0 | 12 | RTD: (mA - 4) * 6.25 °C |
| Presion Water | ADCplate / 3 | I1 | 13 | 4–20 mA → 0–232 PSI |
| Presion Coolant | ADCplate / 3 | I2 | 14 | 4–20 mA → 0–232 PSI |
| Presion Air | ADCplate / 3 | I3 | 15 | 4–20 mA → 0–232 PSI |
| Vacio medio | ADCplate / 3 | S0 | 0 | Terranova 906A; voltaje → Torr |
| Vacio alto | ADCplate / 3 | S1 | 1 | GP270: 0 a -5 V; conversion nominal por tramos; calibracion pendiente |

I0–I3 son entradas de corriente y S0–S7 de voltaje. Los indices no son pines fisicos GPIO. Medium usa Terranova 906A con la formula confirmada: P(Torr)=10^(2V-3). High usa GP270, salida negativa de 0 a -5 V y conversion nominal por tramos. Ver mapa y apartado GP270 al final; calibracion fisica pendiente.

Water temperatura es independiente de Coolant temperatura (termocupla K, THERMOplate 2/canal 1). Room sigue comentado para su sensor aparte. `temperatura_agua.py` devuelve mA y °C = (mA - 4) * 6.25, aceptando 4–20 mA. El RTD se muestra solo en Dashboard.

## Mapa completo de las dos RELAYplate2

Los numeros 01–16 del GUI son identificadores visuales, no numeros de rele.
Cada placa tiene reles 1–8. ON energiza el rele; OFF lo desenergiza.
El efecto en una valvula depende de su cableado NO/NC.

| Address | Rele | Equipo / boton |
|---|---|---|
| 0 | 1 | Air Compressor |
| 0 | 2 | Water Chiller |
| 0 | 3 | Booster Pump (Magnetic Booster Pump) |
| 0 | 4 | Cool Trap A (Cooling Trap A) |
| 0 | 5 | Cool Trap B (Cooling Trap B) |
| 0 | 6 | Diffuse Valve A |
| 0 | 7 | Diffuse Valve B |
| 0 | 8 | Chamber Valve A |
| 1 | 1 | Chamber Valve B |
| 1 | 2 | Mechanical Pump A |
| 1 | 3 | Mechanical Pump B |
| 1 | 4 | Diffusion Pump A |
| 1 | 5 | Diffusion Pump B |
| 1 | 6 | Gate Valve A |
| 1 | 7 | Gate Valve B |
| 1 | 8 | Microwave Cooling |

Water Chiller es la nueva asignacion al rele libre 0/2, autorizada por el usuario.
Las otras 15 asignaciones provienen de `Capstone 2/Shutdown V2/relays.py`.
El cableado fisico debe corresponder a esta tabla; no se ha verificado desde este equipo.

Otras placas del stack: THERMOplate address 2; ADCplate address 3.

## Ejecutar en la Raspberry Pi

Con Pi-Plates instalado y SPI habilitado, desde esta carpeta:

```bash
python3 main.py
```

El GUI se abre en `http://127.0.0.1:8000`. Si el navegador no se abre automaticamente, use esa direccion.
No abrir el HTML directamente: los botones necesitan el servidor Python.

Al ejecutar `main.py` se verifican las dos placas y se abre automaticamente el navegador del escritorio de la Raspberry. Se necesita una sesion grafica para abrir la ventana. El servidor escucha en localhost y requiere hardware Pi-Plates; no ofrece un modo sin hardware.

## Comportamiento

- Al iniciar, verifica las dos placas y lee su estado sin resetear salidas.
- Cada pulsacion envia un estado explicito ON/OFF y comprueba `relaySTATE`.
- El estado confirma el rele, no el funcionamiento mecanico del equipo.
- Actualiza los estados cada dos segundos. Si falla la comunicacion, muestra estado desconocido y bloquea botones hasta recuperar conexion.
- Al cerrar main.py se intenta consigna cero y OFF en los 16 reles, con verificacion y errores; ver EMERGENCY_SHUTDOWN.md.
- El mando manual es directo; durante Start Startup Process queda bloqueado. La secuencia se ejecuta en startup.py; no hay interlocks continuos generales de proceso.
- Flujo muestra porcentaje real cuando ADC responde; Main Valve controla consigna DAC cuando DAQC2 responde. El modo automatico sigue deshabilitado. Main Valve representa la valvula interna del Aera, mediante la consigna analogica.
- `dashboard.html` es un monitor de lecturas y estados reales; no ejecuta secuencias; dispone del paro de emergencia.

## Verificacion

Se comprobaron las asignaciones, las solicitudes HTTP y el manejo de errores durante el desarrollo. Falta verificar las placas y el cableado fisico en la Raspberry. Arrancar el servidor no energiza ni apaga los reles: conserva y lee su estado actual.

## Diagnostico de errores

`errores.py` centraliza codigos, mensajes, contexto y soluciones del backend. Los errores de conexion del navegador se detectan en `manual_control.js`. El GUI muestra el error y conserva el ultimo en un panel desplegable. La terminal y `logs/control.log` guardan hora y detalle tecnico (rotacion: 1 MB, tres copias). Si no se puede escribir el log, el aviso y los errores siguen disponibles en terminal; revise permisos de esa carpeta.

| Codigo | Como resolverlo |
|---|---|
| `HW_IMPORT` | Ejecute en la Raspberry con el entorno Python que tiene Pi-Plates y sus dependencias instaladas. Revise el nombre del modulo en Detalle. |
| `HW_INIT` | Revise el detalle de inicializacion, SPI habilitado, permisos y compatibilidad del controlador GPIO con su Raspberry. |
| `HW_ID` | Apague antes de revisar el montaje y los jumpers del address indicado. Compruebe alimentacion y SPI; una respuesta inesperada no prueba que la placa este danada. |
| `HW_READ` | Revise alimentacion y conexion SPI de la placa indicada. Compruebe permisos de /dev/spidev* y cierre otros lectores que interfieran con el bus. |
| `HW_STATE` | La respuesta no es una mascara valida de 0 a 255. Revise la comunicacion y la version de Pi-Plates; no interprete este valor como OFF. |
| `HW_WRITE` | El resultado de la orden es incierto. Compruebe el estado real del equipo y la conexion de la placa antes de volver a ordenar. No se reintenta automaticamente. |
| `HW_CONFIRM` | La orden se envio, pero no pudo confirmarse. Revise el equipo y el estado de la placa antes de repetir; el rele puede haber cambiado. |
| `INPUT` | Use un equipo definido en manual_control.py y un estado booleano true/false. Recargue el GUI servido por main.py. |
| `HTTP_ORIGIN` | Abra el GUI desde la direccion que imprime main.py, en el mismo origen que la API. |
| `HTTP_TYPE` | La solicitud debe usar Content-Type: application/json. Actualice manual_control.js y recargue el GUI. |
| `HTTP_ROUTE` | Abra / o /vacuum_controller.html en el servidor; revise la ruta solicitada. |
| `GUI_FILE` | Restaure el archivo indicado en producto final y compruebe que el usuario puede leerlo. |
| `SERVER_BIND` | Si el puerto esta ocupado, cierre la otra instancia o use python3 main.py --port 8001. Si faltan permisos, use un puerto mayor que 1023. |
| `BROWSER` | Abra manualmente la URL indicada desde el escritorio de la Raspberry. Por SSH sin sesion grafica no se abrira una ventana local. |
| `INTERNAL` | Consulte el traceback en la terminal y logs/control.log. Conserve el codigo, la hora y el detalle para depurar; no asuma que la orden fallo sin comprobar el rele. |
| `NET_CONNECTION` | Mantenga main.py ejecutandose; abra su URL HTTP y revise si termino con un error. No abra el HTML como archivo. |
| `NET_TIMEOUT` | La espera supero 5 segundos. Revise la terminal y SPI. No repita una orden sin comprobar el estado: pudo ejecutarse aunque su respuesta no llegara. |
| `NET_RESPONSE` | La respuesta HTTP no tiene el formato o estados esperados. Actualice juntos servidor, modulo de control y JavaScript; compruebe que usa el puerto correcto. |

Ejemplo: `[HW_WRITE] Error al enviar la orden | equipo=Water Chiller | address=0 | rele=2 | solicitado=ON | Detalle: ... | Que revisar: ...`.

Las causas indicadas son comprobaciones sugeridas, no un diagnostico fisico definitivo. Ningun error causa un reintento automatico de ON/OFF. Tras recuperar comunicacion se releen los estados; el historial del ultimo error permanece visible. Los fallos de arranque aparecen en terminal/log porque el GUI aun no esta disponible. Cambie cableado o jumpers con el sistema apagado.

## Temperaturas — THERMOplate address 2

`temperaturas.py` contiene canales, tipos, inicializacion y lectura. `temperaturas.js` actualiza el GUI desde `/api/temperatures`. `main.py` solo conecta el modulo al servidor. `hardware_bus.py` proporciona un bloqueo SPI compartido con los reles dentro del proceso.

| Temperatura | Address | Canal fisico | Tipo |
|---|---|---|---|
| Coolant | 2 | 1 | K |
| Cool Trap A | 2 | 2 | K |
| Cool Trap B | 2 | 3 | K |
| Diffusion Pump A | 2 | 4 | K |
| Diffusion Pump B | 2 | 5 | K |
| Field Magnet A | 2 | 6 | K |
| Field Magnet B | 2 | 7 | K |
| Libre | 2 | 8 | Sin asignar |
| Room | — | — | Sensor independiente pendiente; comentado en codigo |

Este es el nuevo mapa asignado para el producto final, no una afirmacion del cableado existente. La prueba anterior usaba canales 5 y 8 sin identificar equipos. Cablear segun esta tabla o ajustar TERMOCUPLAS antes de usar. Se asume tipo K como en el lector anterior; si una sonda es J, cambiar su tipo en el modulo. Room no usa el MAX31865 ni un canal THERMO en esta etapa.

Con el equipo apagado, conectar cada termocupla al par + y - del canal numerado en THERMOplate, respetando polaridad y tipo de cable/conector. Estos canales no son reles ni pines GPIO. Configuracion de rechazo de red: 60 Hz. Lecturas en grados Celsius; se permiten temperaturas negativas validas. No ejecutar simultaneamente scripts antiguos que accedan al mismo bus: el bloqueo solo coordina este servidor.

El GUI consulta cada 1.5 segundos despues de completar la respuesta; el servidor reutiliza una lectura durante un segundo. Una falla individual deja ese sensor Sin lectura y permite mostrar los demas; una falla de THERMOplate no desactiva Manual Control. Si se pierde el servidor o vence la respuesta se retiran las temperaturas anteriores. Se registra cada cambio de error y recuperacion para evitar llenar el log. Una lectura numerica plausible no demuestra que la sonda este conectada correctamente: verificar con una referencia fisica. No se implementan alarmas de proceso ni interlocks con estas lecturas.

| Codigo | Solucion |
|---|---|
| TEMP_INIT | Revisar instalacion Pi-Plates, SPI, alimentacion y jumpers address 2; reintento de configuracion cada 5 segundos. |
| TEMP_READ | Revisar canal indicado, terminales, polaridad, continuidad y tipo K/J. Si fallan todos, comprobar placa y bus. |
| TEMP_VALUE | Valor no numerico o no finito: comprobar sensor, cableado y tipo. No se reemplaza por cero. |
| TEMP_CONNECTION | Revisar servidor main.py, su URL y logs/control.log; recargar los archivos actualizados juntos. |

Referencia de API: https://pypi.org/project/pi-plates/ (THERMOplate.getTEMP, setTYPE, setLINEFREQ).

### Diagnosticos detallados de termocuplas

Los mensajes estan centralizados en `errores.py` y son emitidos por `temperaturas.py`.

| Codigo | Que fallo y como resolverlo |
|---|---|
| TEMP_IMPORT | Falta THERMOplate o una dependencia. Revisar el nombre de modulo en Detalle y el entorno Python que ejecuta main.py. |
| TEMP_ID | Identificacion de placa fallida o inesperada. Comprobar address 2, SPI, alimentacion y montaje; revisar jumpers con el equipo apagado. |
| TEMP_CONFIG | Configuracion rechazada. Usar canales unicos 1–8, tipos k/j y frecuencia 50/60 Hz; revisar detalle SPI si los parametros son correctos. |
| TEMP_RANGE | Temperatura fuera de conversion: K -200 a 1372 °C; J -210 a 1200 °C. Revisar tipo, polaridad, continuidad y terminales. No es un limite operativo del equipo. |

TEMP_VALUE queda reservado para respuestas no numericas o no finitas; TEMP_READ identifica fallos de lectura y TEMP_INIT cubre otros fallos de inicializacion. Los errores de configuracion/identificacion se reintentan a los 5 segundos. Una sonda desconectada o del tipo equivocado puede producir un valor plausible: el programa no puede detectar esos casos con certeza solo a partir de la temperatura.

## Presiones Air, Coolant y Water

`presiones.py` contiene configuracion, lectura y conversion. `presiones.js` actualiza los valores desde `/api/pressures`; `main.py` solo conecta el modulo al servidor. Los errores permanecen en `errores.py`.

| Lectura | Placa | Address | Entrada | Senal | Escala |
|---|---|---|---|---|---|
| Air | ADCplate | 3 | I3 | 4–20 mA | 0–232 PSI |
| Coolant | ADCplate | 3 | I2 | 4–20 mA | 0–232 PSI |
| Water (agua) | ADCplate | 3 | I1 | 4–20 mA | 0–232 PSI |

I2 es la nueva asignacion de Coolant: cablear el lazo a esa entrada. I3 conserva Air. Water es una lectura separada de Coolant, asignada a I1; cablear su transmisor a esa entrada. I0 queda reservado para la corriente del sensor de temperatura del agua; S0/S1 leen vacio y S2/S3 quedan reservados. Estas son entradas de corriente, no S1/S2/S3 de voltaje. Respetar la polaridad y el esquema del transmisor para cerrar el lazo con su alimentacion; no conectar una fuente de voltaje directamente a I1/I2/I3. El esquema exacto depende del transmisor (2/3/4 hilos).

Se aplica la misma escala de Airpsi3.py a los tres sensores por instruccion del usuario: PSI = max(0, (mA - 4) / 16 × 232). No se introduce correccion para hacer coincidir el manometro. Confirmar que la etiqueta de los tres transmisores corresponde a esa escala; si cambia, editar max_psi por sensor.

Menos de 4 mA da 0 PSI con aviso visible de presion no confiable. Mas de 20 mA conserva la conversion con el mismo aviso. No numericos, infinito o errores de comunicacion muestran Sin lectura, nunca cero. El panel Estado de presiones muestra la corriente o el error detallado. No se usan estas lecturas para interlocks ni control automatico.

Al iniciar la primera lectura se identifica e inicializa ADCplate y se selecciona HIGH; se espera un segundo antes de leer. No ejecutar lectores ADC independientes simultaneamente: initADC afecta toda la placa. Consultas cada 1.5 segundos, cache de un segundo y bloqueo SPI compartido con temperaturas/reles. Una falla de un canal no oculta los otros. Si no se puede inicializar la placa, se reintenta cada 5 segundos.

| Codigo | Como resolverlo |
|---|---|
| PRESS_INIT | Revisar Pi-Plates, SPI, alimentacion y jumpers address 3. Cerrar otros programas que configuren ADCplate. |
| PRESS_READ | Revisar comunicacion de placa, canal indicado y lazo del transmisor. |
| PRESS_VALUE | Respuesta no numerica/finita: revisar libreria, SPI y alimentacion; no representa 0 PSI. |
| PRESS_RANGE | Corriente fuera de 4–20 mA: revisar alimentacion, continuidad, polaridad y rango del transmisor. El PSI calculado no es confiable. |
| PRESS_CONNECTION | Revisar main.py, URL y logs/control.log; la lectura no llega o esta vencida. |

Medium usa Terranova 906A con la formula confirmada; High usa GP270. Las conversiones estan documentadas abajo.

## Entradas de agua y vacio

- RTD Water: ADC3/I0 (indice 12), salida del transmisor 4–20 mA. Formula `(mA - 4) * 6.25` °C; 4 mA = 0 °C y 20 mA = 100 °C. Solo Dashboard.
- Presion Water: ADC3/I1 (indice 13), igual conversion que Air: 4–20 mA a 0–232 PSI.
- Los indices no son pines GPIO. Coolant conserva su termocupla en THERMO2/canal1.
- Medium: Terranova 906A en S0. High: GP270 en S1. S2/S3 reservados, sin lecturas.

### Errores de agua y conversion de vacio

| Codigo | Significado | Que revisar |
|---|---|---|
| WATER_TEMP_RANGE | Corriente fuera de 4–20 mA. | Revisar transmisor RTD, alimentacion y continuidad del lazo; no mostrar el resultado como temperatura valida. |
| WATER_TEMP_READ | No se pudo leer I0. | ADCplate address 3, SPI, alimentacion y lazo del transmisor. |
| WATER_TEMP_VALUE | I0 devolvio un valor no numerico o no finito. | Comunicacion y respuesta del ADC; mostrar Sin lectura, no 0 °C. |
| PRESS_INIT | No se pudo inicializar ADCplate; afecta tambien la temperatura del agua. | Pi-Plates, SPI, alimentacion, jumpers 3 y otros programas usando la placa. |
| PRESS_READ / PRESS_VALUE / PRESS_RANGE | Falla o valor no confiable de presion. | Canal I1/I2/I3 y lazo 4–20 mA segun la tabla anterior; consultar la seccion de presiones. |
| PRESS_CONNECTION | El GUI no recibe el paquete de presiones/agua. | main.py ejecutandose, URL correcta y logs/control.log. |
| VAC_VALUE | La funcion de conversion recibio voltaje no numerico o no finito. | Usar lectura de voltaje ADCplate, no corriente. |
| VAC_RANGE | Resultado no representable de la formula. | Voltaje y formula del controlador. No mostrar cero Torr. |

VAC_READ, VAC_VALUE y VAC_RANGE se muestran en el GUI y registran en logs/control.log. La formula Water esta confirmada; WATER_TEMP_RANGE indica corriente fuera de 4–20 mA. Los errores WATER_TEMP_* se muestran en el GUI mediante Estado de presiones. No hay deteccion automatica fiable de sensor desconectado basada solo en un numero plausible.

## Vacio: mapa activo (Terranova 906A y GP270)

| Sensor | ADCplate address | Entrada de voltaje | Formula actual |
|---|---|---|---|
| Medium Vacuum | 3 | S0 | 10^(2V - 3) Torr |
| High Vacuum | 3 | S1 | GP270: salida negativa por tramos, Torr nominal |

Conectar la salida analogica de voltaje de cada controlador a su entrada S y su retorno analogico a la referencia GND de ADCplate, conforme al pinout de su controlador. No se conecta la sonda directamente como si fuera una termocupla. Los numeros de pin del conector del controlador dependen de su modelo y no se han asignado aqui. S4 lee caudal Aera; S5–S7 libres. S2/S3 reservados para otro grupo.

`vacio.py` contiene SENSORES y la conversion por sensor. Para cambiar un sensor, actualizar su canal/modelo y los parametros que corresponden a su conversion (pendiente/offset para Terranova 906A); si el nuevo sensor usa una ley distinta, adaptar la conversion antes de utilizarlo. Rough A/B no forman parte del mapa activo.

La ADC se inicializa una sola vez desde presiones.py; vacio reutiliza el mismo driver y bloqueo SPI. /api/pressures entrega tambien vacuum y presiones.js comparte la respuesta con vacio.js, sin otra consulta ni reset. El GUI muestra Torr y voltaje en el tooltip. Graficas: ultimas 60 muestras disponibles, eje vertical logaritmico autoajustado, sin datos inventados. Al fallar una lectura se elimina su traza actual; no se dibujan puentes sobre muestras invalidas. Rough A/B permanecen en blanco, sin progreso calculado ni lecturas activas.

VAC_READ: revisar placa, entrada S, controlador y retorno analogico. VAC_VALUE: respuesta no numerica/finita. VAC_RANGE: conversion no representable. Estas comprobaciones no detectan todos los fallos: un cable flotante o un controlador en fallo puede entregar un voltaje numericamente plausible. High GP270 incorpora errores VAC_GP270_STATE, VAC_GP270_RANGE y VAC_GP270_ZERO; Medium no incorpora deteccion especifica de estados del controlador. Verificar lecturas fisicamente al conectar.

## Dashboard del reactor

Abrir /dashboard.html en el mismo servidor main.py, o usar el enlace desde Vacuum Controller. Se eliminaron Iniciar secuencia, Confirmar y Reiniciar junto con la secuencia y datos artificiales. dashboard.js solo hace GET a /api/relays, /api/temperatures y /api/pressures; reutiliza los modulos existentes.

En dashboard, presiones Air/Water en bar (PSI / 14.5037738); vacio medio/alto en mbar (Torr × 1.333223874) desde S0/S1 independientes; Water Temp en °C desde I0 con (mA - 4) * 6.25. Field Coil A/B Temp usan Field Magnet A/B, THERMOplate canales 6/7; Trap A/B canales 2/3; Diffusion Pump A/B canales 4/5.

Indicadores: verde = rele energizado, rojo = desenergizado, gris discontinuo = estado desconocido o no asignado. Field Coil A/B muestran tendencia termica: verde si aumenta, rojo si se mantiene o baja, gris sin comparacion valida. No confirman encendido electrico. Lectura de rele no confirma movimiento fisico de valvula ni funcionamiento de bomba.

Errores visibles en Diagnosticos y tooltips. PRESS_RANGE conserva la presion convertida a bar con fondo amarillo y aviso. Los otros fallos muestran —, sin conservar valores anteriores como actuales. Una falla de ADC no borra termocuplas ni reles. DASH_CONNECTION indica fallo HTTP, tiempo de espera o respuesta invalida/vencida: revisar main.py, URL y logs/control.log. Consultas independientes cada 1.5 segundos despues de completar cada respuesta. No hay automatizacion desde Dashboard; su boton de emergencia si solicita el apagado.

### Unidades del dashboard

Se conservan las unidades originales para presion y vacio:

| Lectura | Unidad de API | Unidad del dashboard | Conversion |
|---|---|---|---|
| Air Pressure / Water Pressure | PSI | bar | PSI / 14.5037738 |
| Medium / High Vacuum | Torr | mbar | Torr × 1.333223874 |
| Termocuplas | °C | °C | Ninguna |
| Water Temp (I0) | °C y mA | °C | (mA - 4) * 6.25, calculada en Python |

Vacuum Controller conserva PSI y Torr. Water Temp se muestra solo en Dashboard, en °C. Al desconectarse se conserva la unidad y se muestra —.

## AutoVacio — reglas y pendientes

AutoVacio seleccionara la lectura segun el rango de vacio: Medium (Terranova 906A, ADC3/S0) en rango medio y High (GP270, ADC3/S1) en alto vacio. El selector por rango esta implementado sin exigir concordancia entre sensores; ver SELECCION_VACIO.md para rangos y limites. Solo se podran usar lecturas validas.

Documento detallado: [AUTOVACIO.md](AUTOVACIO.md), con reglas, conexiones, estado de implementacion y preguntas por resolver.

`autovacio.py` separa las reglas de control. Las bombas mecanicas A/B (address 1, reles 2/3) deben permanecer encendidas durante AutoVacio, incluso al alcanzar el objetivo. Si la presion es menor al objetivo menos tolerancia, abrir mas el mass flow; si es mayor al objetivo mas tolerancia, cerrar mas; dentro de la banda, mantener. Abrir admite gas y aumenta la presion. Las reglas no accionan hardware todavia.

Los indicadores Rough A/B quedan en blanco. AutoVacio no tiene ciclo automatico integrado y ON sigue deshabilitado. El mass flow manual si esta implementado; faltan integracion del ciclo, tolerancia, limites y estrategia para el modo automatico. El startup termina en regulacion manual.

AUTO_CONFIG: completar esas integraciones antes de activar. AUTO_VALUE: datos no finitos o fuera de rango; no calcular acciones con esos datos. Falta definir tambien la reaccion del controlador ante perdida de sensor y la transicion al salir de AutoVacio.

## Main Valve: valvula interna del Aera

Confirmado por el usuario: el boton Main Valve representa la valvula interna del
mass flow Aera Transformer, no una valvula externa. Las 16 asignaciones de reles
se conservan; esta confirmacion no asigna un rele adicional.

La consigna de caudal corresponde al pin 6 (0-5 V), con DAQC2plate address 4.
El pin 1 corresponde al forzado de valvula. ON habilita regulacion a la consigna seleccionada, como confirmo el usuario; no fuerza apertura total.
Faltan variante NC/NO, circuito y niveles de mando confirmados para Transformer,
para regulacion normal. OFF manual ya envia cero; la respuesta fisica falta verificarla. El boton manual aplica la consigna seleccionada o cero; el forzado por pin 1 no esta implementado. Ver [AUTOVACIO.md](AUTOVACIO.md).

## Actualizacion High Vacuum: Granville-Phillips 270

High Vacuum utiliza GP270; no aplica la transferencia del 972B.
Medium mantienen su conversion existente. High usa S1 de ADCplate
address 3, con conexion directa y voltaje negativo, segun el usuario.

Fuente: GP 270 Manual.pdf, seccion 4.11, pagina impresa 4-8 (pagina 30 del PDF).
La salida Pressure va de 0 a -5 V, por tramos lineales de una decada por voltio;
no equivale a aplicar valor absoluto a la formula del 972B. Requiere autorange.
Con filamento apagado o rango manual indica -10 a -12 V.

La ADCplate admite senal bipolar: precision garantizada en +/-10 V y limite
absoluto +/-20 V, segun https://pi-plates.com/adcplate/ . No se presupone
precision garantizada para el valor de fallo por debajo de -10 V.

Unidad solicitada: Torr. La conversion nominal ya esta habilitada en `vacio.py`.
Interpretacion implementada de la tabla del manual: escala lineal 0-10 por tramo,
multiplicada por la decada indicada. Esta interpretacion aun no se ha contrastado
con el equipo; revisar especialmente las transiciones de autorange en calibracion.
No se usa una exponencial continua ni la formula del 972B.

Para U=-V y n=ceil(U)-1 limitado a 0..4:
`P(Torr) = 10 * (U-n) * 10**(n-8)`.
Los extremos enteros se asignan al final del tramo anterior. La salida por tramos
puede presentar saltos en los cambios de rango; no suavizarlos como si fueran
medidas confirmadas. 0 V devuelve error, no cero Torr.

| Voltaje | Torr nominal |
| --- | --- |
| -0.5 V | 5e-8 |
| -1.5 V | 5e-7 |
| -2.5 V | 5e-6 |
| -3.5 V | 5e-5 |
| -4.5 V | 5e-4 |
| -5 V | 1e-3 |

High sigue en ADCplate address 3, S1. Medium siguen como antes.
La API publica Torr, Vacuum Controller muestra Torr y Dashboard conserva mbar.
Autovacio no se habilita por este cambio. Pendiente contrastar lectura del panel
y voltaje simultaneo, verificar unidad fisica Torr y ajustar transferencia si procede.

| Error | Significado | Solucion |
| --- | --- | --- |
| VAC_GP270_STATE | Lectura entre -12 y -10 V | Revisar filamento y autorange; no convertir a presion. |
| VAC_GP270_RANGE | Fuera de 0 a -5 V | Revisar salida Pressure, retorno y S1. |
| VAC_GP270_ZERO | Salida de 0 V | Revisar controlador y cableado; no asumir vacio perfecto. |


## Mass flow: Aera Transformer (actualizacion de equipo)

Fuente vigente: AERA_Transformer.pdf, Advanced Energy, paginas 4-6. Sustituye la identificacion anterior basada en FCR7800-FT-001.pdf.
La familia esta identificada; faltan modelo completo, gas y fondo de escala
 de la etiqueta. El ejemplo 200 SCCM del catalogo no identifica nuestro equipo.

| Pin DB9 | Funcion |
| --- | --- |
| 1 | Forzado OPEN/CLOSE; depende de valvula NC/NO |
| 2 | Salida de caudal 0-5 V = 0-100% del fondo de escala |
| 3 | Alimentacion +15 VDC |
| 4 | Common |
| 5 | Alimentacion -15 VDC |
| 6 | Consigna analogica 0-5 V = 0-100% del fondo de escala |
| 7, 8 | Common |
| 9 | Valve test point, 0 a +13 V segun catalogo Transformer; no es salida de caudal |

Lectura: Q_sccm = V_pin2 / 5 * fondo_escala_sccm.
Consigna: V_pin6 = 5 * Q_objetivo_sccm / fondo_escala_sccm.
Si la etiqueta usa SLM, convertir a SCCM multiplicando por 1000.
El porcentaje representa caudal respecto al fondo de escala, no posicion de valvula.

La lectura esta asignada a ADCplate address 3, S4, desde DB9 pin 2.
El usuario asigno DAQC2plate address 4 para generar la consigna analogica.
DAC0 integrado; falta confirmar fuente bipolar +/-15 V y cableado. No conectar
+/-15 V a GPIO del Raspberry Pi. La alimentacion ±15 V la prepara el equipo del usuario; falta comprobar el montaje fisico.

Pin 1: falta confirmar el estado normal del forzado y la variante NC/NO del Transformer. No asumir niveles o polaridades de otro catalogo. Main Valve aplica consigna elegida por pin 6; OFF envia cero. ON no fuerza apertura total.

El catalogo especifica control de 2-100% FS (5-100% para FS mayor de 150 SLM).
Fuera de ese rango no se presupone regulacion precisa. Verificar gas de calibracion,
fondo de escala, variante NC/NO y condiciones de presion antes de pruebas fisicas.
`masscontroll.py` implementa lectura porcentual y mando limitado a 81.9% por el DAC.


### Variante multigas Transformer

El usuario identifica el equipo como multigas. El catalogo incluye tanto variantes
single-gas como multi-gas: falta codigo completo de la etiqueta (MULTI-1..8),
conector y rango activo. No asumir 200 SCCM ni N2 por el ejemplo del catalogo.
Multigas permite configurar gas y rango dentro de los limites del modelo;
no significa deteccion automatica del gas ni fondo de escala universal.
La conversion 0-5 V debe usar el fondo de escala activo del gas configurado.
Se mantiene pendiente la lista de gases del proceso y el procedimiento de seleccion.
Pinout anterior corresponde exclusivamente a la variante DB9 analogica;
no aplicarlo a DeviceNet. Mass flow manual integrado; AutoVacio sigue sin habilitarse.


## Mass flow: implementacion manual activa

- `masscontroll.py`: conversion porcentual, lectura ADC y escritura DAQC2 con
  consulta getDAC posterior. `masscontroll.js`: seleccion y aplicacion manual.
- Aera DB9 pin 2 -> ADCplate 3/S4; pin 6 <- DAQC2plate 4/DAC0.
  Common analogico compartido segun cableado del equipo; fuente +/-15 V externa.
- DAQC2 setDAC admite 0-4.095 V, no 5 V. Consigna maxima directa: 81.9% FS.
  Fuente: https://pi-plates.com/downloads/DAQC2plate%20Reference%20Guide.pdf
  Limite de 81.9% aceptado por el usuario; se conserva sin adaptacion a 100%.
- El slider selecciona porcentaje; Aplicar envia la consigna. Main Valve envia
  cero si hay consigna activa, o aplica la seleccion si esta en cero.
  ON/OFF representa consigna, no posicion ni cierre confirmado. Pin 1 de override
  debe estar en modo de regulacion normal; el programa no lo acciona.
- Al iniciar no se escriben salidas. Al cerrar main.py se intenta consigna cero y OFF en los 16 reles. Cerrar la pestaña no cierra el servidor. No hay regulacion automatica.
- getDAC confirma registro de consigna, no voltaje medido en el borne ni caudal.
  Caudal se lee aparte desde S4; un voltaje plausible no detecta desconexion.
- `FULL_SCALE_SCCM=None`: no inventar rango. Meter muestra % FS; solo configurar
  SCCM tras confirmar el rango activo del gas. Lectura 0-5 V = 0-100% FS.
- GET `/api/mass-flow`: registro DAC. POST: `{"percent":50}`; mismas restricciones
  de origen/JSON que reles. `/api/pressures` incluye `mass_flow` (lectura).
- MFC_INPUT: usar 0-81.9%. MFC_DAC: revisar placa4/driver/DAC0.
  MFC_WRITE: orden incierta, consultar antes de repetir; no reintento automatico.
  MFC_READ: revisar ADC3/S4, pin2 y alimentacion; no convertir fallo a caudal cero.
- Pruebas de software aisladas en tests/test_masscontroll.py. Pruebas fisicas
  de voltaje, caudal y regulacion pendientes. AutoVacio permanece bloqueado.


Lista explicada de lo que falta en ambos GUI: [PENDIENTES.md](PENDIENTES.md).


## Actualizacion: apagado y emergencia

Implementado el paro de software en ambos GUI y al cerrar main.py: consigna
cero del mass flow, OFF en los 16 reles y bloqueo de nuevas ordenes hasta reiniciar.
Esta actualizacion sustituye las descripciones anteriores que indicaban que el
cierre del servidor conservaba las salidas. Cerrar la pestaña no cierra el servidor.
No actua ante perdida de alimentacion o SIGKILL ni confirma cierre mecanico del gas.
Alcance, errores y limites: [EMERGENCY_SHUTDOWN.md](EMERGENCY_SHUTDOWN.md).
Validacion fisica y secuencia de enfriamiento del proceso pendientes.


## Conversion Medium actualizada al manual

Se aplica `P(Torr)=10^(2V - 3)` en S0. Los estados LO/OFF/HI no se interpretan como presion valida. Detalles, ejemplos y limites del cambio Medium/High en [SELECCION_VACIO.md](SELECCION_VACIO.md). La formula esta implementada y probada en software; el selector por rango esta implementado; el regreso usa Medium valido > 1 × 10⁻³ Torr, sin esperar un valor superior al rango de High. Falta validacion fisica. AutoVacio no se habilita con este cambio.

## Field Coil A/B: tendencia de temperatura

Dashboard compara dos lecturas nuevas de Field Magnet A/B (THERMO2, canales 6/7) a 0.1 °C. Verde: sube; rojo: estable o baja; gris: sin datos o esperando segunda lectura. Paquetes repetidos no cambian el indicador; errores o intervalos mayores de 15 segundos reinician la comparacion. No usa rele ni confirma alimentacion electrica. No modifica AutoVacio.

## Startup implementado: control y confirmacion de gas

Start Startup Process ejecuta la secuencia de [STARTUP_2026.md](STARTUP_2026.md).
Bloquea reles y caudal manuales hasta que termine, con proteccion en servidor
para todas las pestañas. Emergency Shutdown permanece disponible. Al final,
**Gas ajustado manualmente — confirmar** registra el ajuste realizado en el
equipo y libera el control manual. No manda gas automaticamente. La secuencia
ya esta programada; faltan pruebas fisicas. El ciclo AutoVacio sigue pendiente.

## Organizacion del startup en modulo independiente

El header file del startup es [startup.py](startup.py). `main.py` solo instancia
`Startup` y conecta sus funciones a las rutas HTTP. Secuencia, esperas y
condiciones viven en ese modulo; los errores en `errores.py` y la interfaz en
`startup.js`. No hay canales adicionales ni un modo de simulacion del producto.

Documentacion completa: [STARTUP_2026.md](STARTUP_2026.md), con pasos, tiempos,
rangos, estados, bloqueo manual, confirmacion de gas, API, fallos y pruebas.
Estado del proyecto: [PENDIENTES.md](PENDIENTES.md). El startup esta implementado;
AutoVacio aun necesita su ciclo actuador y parametros de regulacion.

## Procedimiento de shutdown normal recibido

Ver [SHUTDOWN_2026.md](SHUTDOWN_2026.md): cierre de inyeccion manual confirmado por el operador, espera posterior de 120 segundos y enfriamiento de ambas bombas a <=100 °F, confirmado por el usuario. Implementado en shutdown.py; no cambia el paro inmediato ni el cierre actual de main.py. Validacion fisica pendiente.

## Shutdown normal implementado

Modulo separado `shutdown.py`, boton Start Shutdown Process y confirmacion de cierre manual del gas. Espera 120 segundos y mantiene las mecanicas y la refrigeracion hasta que ambas bombas de difusion cumplan <=100 °F. Bloqueo manual y exclusion con startup en Python; Emergency disponible. Detalles, errores y limitaciones en [SHUTDOWN_2026.md](SHUTDOWN_2026.md).
