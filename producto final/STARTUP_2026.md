# Startup de vacio: procedimiento vigente 2026

## Definiciones vigentes

- Low/Medium: Terranova 906A, ADCplate 3/S0, `P(Torr) = 10^(2V - 3)`.
- High: Granville-Phillips 270, el del manual recibido, ADCplate 3/S1; conserva `gp270_a_torr`.
- Medium usa ahora la formula del manual Terranova 906A, por instruccion del usuario. High conserva su conversion GP270. Falta validacion fisica.
- Roughing Vacuum Gauges A/B (Rough Manifold A/B): ADCplate 3, S4 y S5; se muestran como barras de 0-10 V (0 V = 1e-3 Torr, 10 V = 1000 Torr). S2/S3 quedan libres.
- Reactor Water Line Temperature es el RTD en ADC3/I0, solo para visualizar en Dashboard, sin condicionar el startup.
- Coolant es distinto de Water. Room (lab temp) es un DS18B20 en THERMOplate address 2, puerto 9; alarma High room temperature si Room > 29 °C.
- El startup vigente es [STARTUP_2026.md](STARTUP_2026.md): Medium para 30–1 mTorr, esperar si no se cumple una condicion o falla la lectura, y regulacion final del gas manual.
- Water Level Solenoid queda excluido. Las fuentes de plasma pertenecen a otro grupo.


Fuente: Startup procedure 2026 Capstone Edition.pdf, recibido del usuario.
Este procedimiento sustituye startup 2.0 como referencia. La secuencia esta implementada en startup.py y conectada al servidor y al GUI. Validacion fisica pendiente.

| Paso del PDF | Accion |
|---|---|
| 2 | Encender Air Compressor |
| 3 (modificado) | Esperar 2 minutos; mando de Water Level Solenoid eliminado por el usuario |
| 4 | Encender Water Chiller |
| 5 | Despues de 2 minutos, encender Magnetic Booster Pump |
| 6 | Encender Cooling Traps A y B |
| 7 | Abrir Diffuse Valves A y B |
| 8 | Abrir Chamber Valves A y B |
| 9 | Encender Mechanical Pumps A y B |
| 11 | Esperar lectura valida de Medium Vacuum (ADC3/S0) entre 0.001 y 0.030 Torr |
| 12 | Encender Diffusion Pumps A y B |
| 13 | Esperar temperatura de bombas de difusion de 250 a 300 °F (121.11 a 148.89 °C) |
| 14 | Cerrar Chamber Valves A y B |
| 15 | Abrir Gate Valves A y B |
| 16 | El operador inyecta el gas y regula la presion manualmente |

## Aclaraciones confirmadas

- Reactor Water Line Temperature es Water/RTD en ADC3/I0, solo para visualizar
  en Dashboard. No es condicion del startup.
- Rough Manifold A/B: barras de voltaje 0-10 V en S4/S5, sin condiciones
  de avance asociadas al startup.
- Las fuentes pertenecen al proceso de plasma de otro grupo; no se incluyen
  encendido ni ajuste de potencia de microondas en este startup.
- No trasladar los requisitos antiguos de 37.78 °C en bombas mecanicas,
  177 °C en diffusion pumps ni el umbral fijo 0.025 Torr como si fueran del PDF.
  El PDF tampoco especifica el umbral antiguo de aire 100 PSI ni agua <=10 °C.

## Decisiones confirmadas por el usuario

- Se elimina Water Level Solenoid del mando de la secuencia; no requiere rele.
  Se conserva la espera de 2 minutos del paso 3: no se solicito cambiar los tiempos.
- La condicion de vacio usa Medium Vacuum, ADCplate address 3/S0.
- Si no se cumple la condicion, permanecer en el paso y seguir comprobando,
  sin vencimiento automatico. Una lectura ausente, invalida o con error no
  permite avanzar: mostrar el error y esperar una lectura valida que cumpla.
- La espera no debe impedir usar el paro de emergencia ni cerrar main.py.

## Estado del procedimiento

Resuelto: el paso final de gas y regulacion es manual, a cargo del operador.
La secuencia esta implementada; termina al confirmar el ajuste manual de gas.

## Cambios ya aplicados

Rough A/B se muestran como barras de 0-10 V (S4/S5); no condicionan el startup. Water/RTD
se muestra solamente en Dashboard, conservando (mA - 4) * 6.25 °C y su API.
El mapa de reles permanece sin cambios; el startup se ejecuta solo al pulsar Start Startup Process.


## Comparacion con el codigo actual

- Pasos 2, 4-9, 12, 14 y 15: los equipos ya tienen reles asignados.
- Paso 3: mando de Water Level Solenoid excluido; sin cambios al mapa de reles.
- Esperas de pasos 3 y 5: el PDF especifica 120 segundos en cada una;
  implementadas con reloj monotono, sin bloquear el hilo por 120 segundos.
- Paso 11: Medium Vacuum en ADC3/S0 comprobara 0.001-0.030 Torr.
- Paso 13: temperaturas A/B disponibles en THERMOplate 2, canales 4/5.
  Condicion integrada: ambas deben estar entre 250 y 300 °F (limites calculados en °C).
- Paso 16: mando manual de caudal implementado; el operador regula la presion.
  El startup no activa regulacion automatica.
- Secuenciador integrado con el bloqueo de ordenes y el paro de software.

La temperatura de bombas mecanicas no es una condicion exigida por este PDF.
Las condiciones se esperan sin timeout, segun el usuario; el paro de emergencia debe poder interrumpir la secuencia.

## Conversion Medium actualizada al manual

Se aplica `P(Torr)=10^(2V - 3)` en S0. Los estados LO/OFF/HI no se interpretan como presion valida. Detalles, ejemplos y limites del cambio Medium/High en [SELECCION_VACIO.md](SELECCION_VACIO.md). La formula esta implementada y probada en software; el selector por rango esta implementado; el regreso usa Medium valido > 1 × 10⁻³ Torr, sin esperar un valor superior al rango de High. Falta validacion fisica. AutoVacio no se habilita con este cambio.

## Botones, bloqueo y estados del startup

- **Start Startup Process**: inicia una sola secuencia por ejecucion de main.py. No arranca al abrir o recargar el GUI.
- Se bloquean los mandos manuales de reles y caudal en el navegador y en Python, incluso desde otras pestañas o llamadas HTTP. Las lecturas siguen actualizandose.
- Al terminar las acciones automaticas se muestra **Gas ajustado manualmente — confirmar**. Por ahora el operador realiza el ajuste en el equipo; los mandos manuales del GUI siguen bloqueados hasta confirmar.
- La confirmacion solo se acepta en ese paso. Registra una declaracion del operador, no verifica el caudal y no manda una consigna DAC. Despues se habilita el control manual, sujeto al estado de conexion y emergencia.
- Emergency Shutdown permanece disponible; interrumpe futuras ordenes y aplica el apagado existente. Cerrar main.py aplica el mismo paro. Cerrar una pestaña no detiene la secuencia.
- Estados: idle, running, awaiting_gas, complete, failed y stopped. No se reanuda automaticamente tras reiniciar el servidor; revisar estado fisico antes de un nuevo arranque.

Una condicion de sensor invalida, vencida (mas de 15 segundos), con error o fuera
del intervalo deja la secuencia esperando sin timeout. Se muestran paso y error.
No se agregan condiciones antiguas de aire/agua. Si falla una orden de rele o
su confirmacion, el startup queda failed, conserva el bloqueo y no reintenta:
use el paro y revise el equipo. No se ejecuta una reversa automatica de pasos.
Las condiciones se comprueban al llegar a su etapa, no constituyen interlocks
continuos. Un acceso hardware bloqueado puede retrasar el paro, como ya se
documenta en EMERGENCY_SHUTDOWN.md.

## API e implementacion

`startup.py` mantiene la secuencia en memoria; hilo de trabajo cada 0.5 segundos,
esperas de 120 segundos con reloj monotono. Usa set_relay con confirmacion,
Presiones.read y Temperaturas.read. Comparte el bloqueo de EmergencyShutdown
para serializar inicio, mandos, confirmacion y paro.

| Ruta | Funcion |
|---|---|
| GET /api/startup | Paso, mensaje, error, bloqueo y botones permitidos |
| POST /api/startup, JSON {} | Iniciar |
| POST /api/startup/confirm-gas, JSON {} | Confirmar gas al final |

STARTUP_LOCKED rechaza mandos durante el proceso. STARTUP_STATE rechaza inicio
duplicado y confirmacion prematura. No modificar banderas para evitar estos
bloqueos. Las rutas conservan las comprobaciones JSON/origen del servidor.

Pruebas aisladas: secuencia y orden de reles, espera de 120 segundos, lecturas
invalidas/vencidas, ambas temperaturas, bloqueo manual, confirmacion y paro.
No se han accionado equipos durante estas pruebas. Falta validacion fisica.

## Modulo separado (header file)

La logica esta en [startup.py](startup.py), un modulo Python independiente,
que es lo que llamamos header file en este proyecto. No es un archivo .h de C.
`main.py` importa `Startup`, crea una instancia compartida por las solicitudes
y llama sus funciones. No contiene la lista de pasos ni sus condiciones.

| Archivo | Responsabilidad |
|---|---|
| startup.py | STEPS, clase Startup, esperas, condiciones, bloqueo manual y confirmacion |
| main.py | Crear instancia y exponer rutas HTTP; pasar ordenes manuales por startup.manual |
| startup.js | Consultar estado cada segundo, mostrar botones y bloquear paneles |
| vacuum_controller.html | Controles Start Startup Process y confirmacion de gas |
| manual_control.py | Mapa de reles y envio/consulta de cada orden |
| presiones.py / vacio.py | Lectura Medium en ADC3/S0, Terranova 906A |
| temperaturas.py | Diffusion Pump A/B: THERMO2, canales 4/5, °C |
| emergency_shutdown.py | Serializar ordenes y evitar nuevas acciones despues del paro |
| errores.py | Codigos STARTUP_LOCKED y STARTUP_STATE y sus explicaciones |
| tests/test_startup.py | Pruebas de secuencia, bloqueos, fallos, confirmacion y API |

### Funciones del modulo

- `start()`: inicia una vez, crea el hilo y bloquea manual. No se llama al arrancar main.py.
- `state()`: informa estado, paso, mensaje, error y acciones permitidas.
- `tick()`: procesa un paso o vuelve a comprobar la espera; no duerme 120 segundos.
- `manual(action)`: acepta mandos solo en idle o complete, siempre sujetos al paro.
- `confirm_gas()`: completa solo desde awaiting_gas y libera manual.

### Estados y lo que puede hacer el operador

| Estado | Mandos manuales | Confirmar gas | Significado |
|---|---|---|---|
| idle | Disponibles con conexion | No | Todavia no se ha iniciado |
| running | Bloqueados | No | Ejecutando o esperando condicion |
| awaiting_gas | Bloqueados | Si | Ajuste de gas externo pendiente de confirmacion |
| complete | Disponibles con conexion | No | Operador confirmo el gas |
| failed | Bloqueados | No | Orden sin confirmar; revisar y usar paro |
| stopped | Bloqueados | No | Paro enclavado; no hay rearme en GUI |

El paro permanece accesible en todos los estados. El boton de confirmacion no
abre valvulas ni escribe al DAC. Tampoco se cierra automaticamente el gas al
iniciar: el modulo solo ejecuta las acciones del procedimiento documentado.

### Diagnostico practico

| Situacion | Comportamiento / que revisar |
|---|---|
| Controles bloqueados | Consultar paso actual. Es normal durante running y awaiting_gas |
| Espera de vacio prolongada | Revisar Medium S0, unidades Torr y lectura entre 1e-3 y 3e-2 Torr |
| Espera de temperatura | Ambas bombas deben estar simultaneamente entre 250 y 300 °F; revisar canales 4/5 |
| Lectura ausente o vencida | Espera sin avanzar; revisar error, conexion y timestamp del servidor |
| Rele sin confirmar | Se detiene sin repetir la orden; el equipo pudo cambiar. Usar paro y revisar |
| Confirmacion rechazada | Solo corresponde en awaiting_gas; no permite saltar etapas |
| GUI pierde conexion | Bloquea paneles; el servidor puede seguir ejecutando. Volver a consultar su estado |
| Live Server o archivo HTML | No ejecuta hardware; abrir la direccion servida por main.py |

### Estado de verificacion

25 pruebas de software pasaron tras integrar el startup, incluidas sus rutas HTTP.
La revision visual con navegador no se completo por un fallo del entorno de
verificacion. Las pruebas fisicas, la respuesta de los equipos y la secuencia
de enfriamiento siguen pendientes. AutoVacio es independiente y su ciclo de
regulacion del gas no se implementa por añadir este startup.

## Emergency no queda bloqueado por startup

El bloqueo visual afecta solamente los paneles manuales de reles, caudal y
AutoVacio; nunca al panel Emergency. Su ruta /api/emergency no pasa por el
bloqueo manual del startup. Funciona tambien durante esperas, confirmacion del
gas o fallo de secuencia. Solo se deshabilita su propio boton mientras envia
una solicitud de paro; despues permite reintentar. Una operacion hardware en
curso puede retrasar el apagado: no es un paro fisico de tiempo garantizado.

Live Server (por ejemplo puerto 5500) no conecta estas rutas con el hardware.
Ejecutar main.py y abrir la direccion que imprime (por defecto puerto 8000).
Un boton visible no confirma que exista comunicacion con el servidor.

## Presentacion detallada en el GUI

El panel muestra Paso X de Y y la accion ON/OFF, estado, condicion requerida,
tiempo restante en segundos, Medium en Torr con notacion cientifica y las
temperaturas de Diffusion Pump A y B separadas en °C. Los errores se presentan
en su propia linea. Una lectura vencida no se conserva como actual.

«Ver avance de todos los pasos» despliega la lista completa con completado,
actual, pendiente, error o interrumpido. Es desplegable con desplazamiento
interno para no ocupar permanentemente la pantalla. La numeracion es de
acciones del programa (una por rele), no la numeracion irregular del PDF.
Completado indica ejecucion/confirmacion de esa etapa, no una comprobacion
fisica continua. Al perder comunicacion se retiran los detalles anteriores.

El panel de Emergency sigue fuera del bloqueo. Verificacion: pruebas de
software y sintaxis; revision visual en navegador pendiente.

## Control manual: permiso para bombas de difusion

Diffusion Pump A y B solo admiten encendido manual cuando Medium Vacuum
(Terranova, ADCplate 3/S0) indica `0 < P < 0.030 Torr` (3.0e-2 Torr).
Exactamente 0.030 Torr no habilita el encendido. Se exige dato numerico finito,
sin error y con antiguedad maxima de 3 segundos. Una lectura faltante, vencida
o invalida mantiene el encendido bloqueado.

`manual_control.py` calcula `manual_allowed` para ambos botones. La API consulta
las mediciones al procesar la orden y vuelve a verificar el permiso antes de
encender; no depende solamente del bloqueo visual. Los datos ADC pueden
provenir de la cache existente de un segundo.

Si la bomba ya esta encendida, OFF sigue permitido aunque se pierda la condicion
de vacio, sujeto a los bloqueos generales de startup/shutdown/emergencia. Esta
regla no ejecuta apagado automatico ni enciende ninguna bomba por si sola.
Los otros seis controles iniciales conservan su permiso. Los demas permanecen
bloqueados. Emergency sigue independiente.

Este cambio corresponde al control manual; no modifica el intervalo ni la
secuencia del startup automatico, que conserva su logica existente.
Validacion: `tests/test_manual_conditions.py` comprueba limites, datos invalidos,
vencimiento, rechazo de ON y disponibilidad de OFF sin lectura. Falta prueba fisica.

## Permisos manuales — actualizacion vigente

Permanentes: Air Compressor, Water Chiller, Cool Trap A/B, Mechanical Pump A/B
y Booster Pump. Booster Pump siempre debe estar habilitado, por decision del
usuario del 3 de octubre de 2026; ya no forma parte de la ampliacion temporal.
Temporal, por indicacion del usuario mientras se aclara una duda: Buzzer
(antes Microwave Cooling).
Diffuse Valve A/B: ON manual solo si estan encendidos los equipos de los pasos
previos del startup 2026: Air Compressor (2), Water Chiller (4), Booster Pump (5)
y Cool Trap A/B (6). Water Level Solenoid (3) esta excluido. Si falta alguno, el
boton queda bloqueado y su aviso indica que falta encender. OFF sigue permitido.
La condicion revisa el estado registrado en las placas de reles, no las esperas
de 2 minutos ni la respuesta fisica de los equipos. Decision del usuario del
3 de octubre de 2026.
Chamber Valve A/B: ON manual solo si, ademas de esos cinco equipos, estan
encendidas Diffuse Valve A y Diffuse Valve B (paso 7). Mismas reglas: aviso de
lo que falta, OFF permitido y estado registrado en las placas. Decision del
usuario del 3 de octubre de 2026.
Gate Valve A/B (paso 15): ON manual solo si se cumplen los pasos previos del
startup 2026: encendidos los equipos de los pasos 2-7, Mechanical Pump A/B
(paso 9) y Diffusion Pump A/B (paso 12); Medium entre 0.001 y 0.030 Torr,
1-30 mTorr con limites incluidos, como en startup (paso 11); ambas Diffusion
Pump entre 250 y 300 °F, 121.11-148.89 °C (paso 13); y Chamber Valve A/B
apagadas (paso 14). Vacio y temperaturas deben ser validos y de hasta 3 s de
antiguedad. El aviso del boton lista todo lo que falta. OFF sigue permitido.
Consecuencia de seguir el documento: con Medium por debajo de 0.001 Torr o una
bomba por encima de 300 °F el ON manual queda bloqueado. Decision del usuario
del 3 de octubre de 2026.
En `manual_control.py`: PERMANENT_MANUAL_ALLOWED, TEMPORARY_MANUAL_ALLOWED,
MANUAL_PREREQUISITES y blocked_reasons(); main.py entrega vacio y temperaturas. Diffusion Pump A/B
conservan el requisito de Medium valido y reciente menor de 0.030 Torr para ON;
OFF sigue permitido si ya estan encendidas.
La habilitacion no enciende equipos: solo permite ordenes manuales. Se conservan
los bloqueos por secuencias, emergencia y comunicacion. Startup no se modifica.

## Water Chiller habilitado — decision vigente

Por nueva indicacion del usuario, Water Chiller vuelve a estar activo en
RELAYplate2 address 1, rele 2. Se restauran el boton manual, su encendido
y espera de 120 segundos en startup, y su apagado en shutdown. Se cancela
la reserva propuesta en address 5. Los bloqueos generales siguen vigentes.
