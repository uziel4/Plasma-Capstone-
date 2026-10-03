# Conexiones de todos los modulos — producto final

> Configuracion vigente de caudal: FC-PA7800, escala seleccionada por el usuario de 5,000 SCCM. Manual Gas Flow Control permite seleccionar 10–5,000 SCCM; el mando directo admite hasta 4,095 SCCM por el DAC de 4.095 V. Valores superiores se rechazan sin escribir salidas. OFF envia cero, fuera del minimo de seleccion. FULL_SCALE_SCCM=5000; lectura SCCM=V/5*5000. Esta configuracion sustituye las menciones historicas a escala pendiente. El ciclo AutoVacio sigue pendiente.

## Definiciones vigentes

- Low/Medium: Terranova 906A, ADCplate 3/S0, `P(Torr) = 10^(2V - 3)`.
- High: Granville-Phillips 270, el del manual recibido, ADCplate 3/S1; conserva `gp270_a_torr`.
- Medium usa ahora la formula del manual Terranova 906A, por instruccion del usuario. High conserva su conversion GP270. Falta validacion fisica.
- Rough Manifold A/B son para otro grupo: quedan en blanco, sin lecturas activas de S2/S3.
- Reactor Water Line Temperature es el RTD en ADC3/I0, solo para visualizar en Dashboard, sin condicionar el startup.
- Coolant es distinto de Water. Room (lab temp) es un DS18B20 en THERMOplate address 2, puerto 9; alarma High room temperature si Room > 29 °C.
- El startup vigente es [STARTUP_2026.md](STARTUP_2026.md): Medium para 30–1 mTorr, esperar si no se cumple una condicion o falla la lectura, y regulacion final del gas manual.
- Water Level Solenoid queda excluido. Las fuentes de plasma pertenecen a otro grupo.


Este mapa describe las asignaciones actuales del programa. No confirma que el
cableado fisico ya se haya verificado. **HAY DUDA** identifica informacion faltante;
no se debe completar un borne por suposicion. Los addresses, canales y numeros de
rele no son numeros de pin GPIO del Raspberry Pi.

## 1. Stack del Raspberry Pi

| Placa | Address configurado | Uso |
|---|---|---|
| RELAYplate2 | 1 | Reles 1-8 |
| RELAYplate2 | 2 | Reles 1-8 |
| THERMOplate | 2 | Termocuplas |
| ADCplate | 3 | Presiones, vacio, temperatura Water y caudal |
| DAQC2plate | 4 | Consigna analogica del Aera por DAC0 |

Las placas se comunican con el Raspberry mediante el conector del stack y SPI.
No son direcciones I2C. Configurar cada placa para el address de la tabla segun
su serigrafia/manual. **HAY DUDA:** posiciones fisicas de jumpers y orientacion
real del stack no se han verificado aqui; no se incluye un pinout GPIO supuesto.
Cambiar conexiones con la alimentacion retirada.

## 2. Reles — manual_control.py

| Equipo | Placa/address | Rele |
|---|---|---|
| Air Compressor | RELAYplate2 / 1 | 1 |
| Water Chiller | RELAYplate2 / 1 | 2 |
| Booster Pump | RELAYplate2 / 1 | 3 |
| Cool Trap A | RELAYplate2 / 1 | 4 |
| Cool Trap B | RELAYplate2 / 1 | 5 |
| Diffuse Valve A | RELAYplate2 / 1 | 6 |
| Diffuse Valve B | RELAYplate2 / 1 | 7 |
| Chamber Valve A | RELAYplate2 / 1 | 8 |
| Chamber Valve B | RELAYplate2 / 2 | 1 |
| Mechanical Pump A | RELAYplate2 / 2 | 2 |
| Mechanical Pump B | RELAYplate2 / 2 | 3 |
| Diffusion Pump A | RELAYplate2 / 2 | 4 |
| Diffusion Pump B | RELAYplate2 / 2 | 5 |
| Gate Valve A | RELAYplate2 / 2 | 6 |
| Gate Valve B | RELAYplate2 / 2 | 7 |
| Buzzer | RELAYplate2 / 2 | 8 |

Las 16 salidas estan asignadas segun este mapa. Las conexiones a los reles no se consideran dudas pendientes. Main Valve es interna del Aera y no ocupa otro rele. La consulta del rele no confirma movimiento o funcionamiento del equipo.

## 3. Termocuplas — temperaturas.py

Conectar los dos conductores al par + y - del canal, respetando polaridad.
No deducir polaridad solo por color sin conocer la norma del cable.

| Temperatura | THERMOplate address | Canal | Tipo configurado |
|---|---|---|---|
| Coolant | 2 | 1 | K |
| Cool Trap A | 2 | 2 | K |
| Cool Trap B | 2 | 3 | K |
| Diffusion Pump A | 2 | 4 | K |
| Diffusion Pump B | 2 | 5 | K |
| Field Magnet A | 2 | 6 | K |
| Field Magnet B | 2 | 7 | K |
| Libre | 2 | 8 | Sin asignacion |
| Room (lab temp) | 2 | 9 | DS18B20 digital (puerto 9) |

**HAY DUDA:** confirmar que las sondas instaladas sean tipo K y verificar su
polaridad. Room es un DS18B20 en el puerto 9 del mismo THERMOplate (address 2).
Water temperatura no es Coolant y no usa uno de estos canales.

## 4. Entradas de corriente — ADCplate address 3

| Equipo | Entrada | Indice logico | Lectura/configuracion |
|---|---|---|---|
| Temperatura Water | I0 | 12 | RTD con transmisor 4-20 mA: (mA - 4) * 6.25 °C |
| Presion Water | I1 | 13 | 4-20 mA, escala configurada 0-232 PSI |
| Presion Coolant | I2 | 14 | 4-20 mA, escala configurada 0-232 PSI |
| Presion Air | I3 | 15 | 4-20 mA, escala configurada 0-232 PSI |

**HAY DUDA:** modelos y terminales de transmisores, alimentacion, lazo de 2/3/4
hilos, retorno y verificacion de las escalas de etiqueta. La salida de corriente
se mide mediante la entrada I indicada; el circuito completo del lazo depende
del transmisor y no se puede determinar solo con el numero de entrada.
No confundir indice 12 con pin fisico 12 del Raspberry.

## 5. Entradas de voltaje — ADCplate address 3

| Senal de origen | Entrada | Retorno | Conversion |
|---|---|---|---|
| Medium Vacuum, salida analogica de presion | S0 | Retorno analogico del controlador a referencia ADC | Terranova 906A, 10^(2V-3) Torr |
| High Vacuum GP270, salida Pressure | S1 | Retorno analogico del GP270 a referencia ADC | Negativa 0 a -5 V, nominal por tramos |
| Aera, DB9 pin 2 OUTPUT | S4 | COMMON analogico del Aera a referencia ADC | 0-5 V = 0-100% del rango activo |
| Libre | S5, S6, S7 | — | Sin asignacion |

**HAY DUDA:** pines exactos de salida/retorno en los conectores de los controladores
de vacio; no estan confirmados en este mapa. En GP270 usar salida Pressure,
no Electrometer ni conexiones del tubo de ionizacion. S1 recibe voltaje negativo
directo, segun el usuario. El GP270 debe usar autorange; -10 a -12 V indica estado
invalido. Las formulas quedan confirmadas por el usuario; falta contrastar fisicamente la lectura con el panel, especialmente en cambios de rango. Medium usa Terranova 906A.

## 6. Aera Transformer multigas — masscontroll.py

La alimentacion la prepara el equipo del usuario, como confirmo. No la genera
el Raspberry ni la salida DAC. El mapa siguiente corresponde a la version
**DB9 analogica** del catalogo AERA_Transformer.pdf, pagina 6.

| Pin DB9 Aera | Funcion | Conexion prevista / estado |
|---|---|---|
| 1 | VALVE OPEN/CLOSED, forzado | Se requiere valvula cerrada al inicio. Falta confirmar la señal electrica de cierre y como liberar el forzado para regular; programa no lo acciona |
| 2 | OUTPUT 0-5 V | ADCplate address 3, S4; caudal medido |
| 3 | +15 VDC | Fuente externa preparada por ustedes |
| 4 | COMMON GND | Comun de alimentacion (0 V), confirmado por el usuario; no es -15 V |
| 5 | -15 VDC | Fuente externa preparada por ustedes; no confundir con 0 V |
| 6 | CONTROL 0-5 V | DAQC2plate address 4, DAC0; consigna |
| 7 | COMMON INPUT | Referencia de la consigna del pin 6: comun de salida analogica de DAQC2plate |
| 8 | COMMON OUTPUT | Referencia de la lectura del pin 2: comun de entrada analogica de ADCplate |
| 9 | VALVE TEST POINT 0 a +13 V | No se utilizara; dejar sin conectar. Confirmado por el usuario |

La referencia de las señales de entrada y salida debe concordar con el COMMON
analogico del Aera. Funciones de pines 4, 7 y 8 confirmadas por el usuario. No
confundir retorno analogico, tierra de proteccion y -15 V. Verificar numeracion
DB9 desde la vista del fabricante: el lado de soldadura invierte la vista.

Main Valve es la valvula interna del Aera, confirmado. En manual el programa
aplica el porcentaje elegido; OFF envia consigna cero. No fuerza apertura total
por pin 1 ni confirma cierre mecanico. **HAY DUDA:** variante NC/NO y configuracion
del override para que el equipo obedezca el pin 6.

### Limite de DAQC2

DAC0 entrega 0-4.095 V: permite ordenar 0-81.9% del rango Aera. No entrega 5 V.
El usuario confirma mantener este limite de 81.9%, sin adaptacion a 100%.
No se cambia la escala para llamar 100% a 81.9%; esta decision ya no es una duda.
PWM no se conecta como sustituto directo de voltaje analogico estable.

**HAY DUDA:** sufijo/configuracion del FC-PA7800, gas seleccionado y fondo de escala activo en SCCM.
La lectura porcentual funciona sin asumir 200 SCCM. La escala en SCCM requiere
esos datos. Multigas no significa que detecta automaticamente el gas.

## 7. Modulos sin conexiones adicionales

| Modulo | Funcion / conexion |
|---|---|
| main.py | Servidor y GUI; no añade canales fisicos |
| startup.py | Reutiliza los reles del mapa y sensores Medium S0 y THERMO2 canales 4/5; no añade conexiones |
| startup.js | Botones y bloqueo visual; sin cableado |
| hardware_bus.py | Coordina acceso SPI de los modulos |
| errores.py | Diagnosticos; no tiene cableado |
| presiones.py | Usa entradas I1-I3 y coordina lecturas ADC |
| temperatura_agua.py | Usa I0; (mA - 4) * 6.25 °C, solo Dashboard |
| vacio.py | Usa S0/S1; S2/S3 reservados |
| temperaturas.py | Usa THERMOplate canales 1-7 |
| autovacio.py | Reglas pendientes de automatizacion; reutilizara sensores y mass flow |
| HTML y JavaScript | Interfaz; no conectar GPIO desde el navegador |
| MAX31865/PT100 de pruebas anteriores | Fuera de la ruta actual; Water usa transmisor 4–20 mA en I0. Room usa DS18B20 en THERMOplate 2/9 |

## 8. Pendientes que no son cables

AutoVacio seleccionara la lectura segun el rango de vacio: Medium (Terranova 906A, ADC3/S0) en rango medio y High (GP270, ADC3/S1) en alto vacio. El selector por rango esta implementado sin exigir concordancia entre sensores; ver SELECCION_VACIO.md para rangos y limites. Solo se podran usar lecturas validas.

- **HAY DUDA:** tolerancia y reaccion ante fallas. El regreso por Medium ya esta implementado. La seleccion por rango ya esta confirmada.
- Validar fisicamente señales, polaridades y caudal. Pruebas de software no
  confirman cableado ni calibracion.
- Configuracion completa y soluciones de errores: [CONFIGURACION.md](CONFIGURACION.md).
- Reglas de regulacion: [AUTOVACIO.md](AUTOVACIO.md).

Fuentes: asignaciones de los modulos Python de producto final; catalogo
AERA_Transformer.pdf del usuario (pinout DB9); GP 270 Manual.pdf (salida Pressure);
[guia DAQC2](https://pi-plates.com/downloads/DAQC2plate%20Reference%20Guide.pdf)
(limite de setDAC). Este documento no inventa los terminales pendientes.


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

## Shutdown normal

`shutdown.py` reutiliza el mapa de reles y THERMO2 canales 4/5. No añade canales; la inyeccion se cierra manualmente. Water Level Solenoid sigue excluido. Ver [SHUTDOWN_2026.md](SHUTDOWN_2026.md).

## Identificacion del mass flow recibida

El usuario identifica el equipo como **Aera FC-PA7800** e informa **10–5,000 SCCM**.
El modelo base ya no es una duda. Se conserva el mando porcentual hasta aclarar
si 5,000 SCCM es el fondo de escala configurado del equipo instalado o el limite
de la familia. El catalogo Transformer presenta 10 SCCM–5 SLM como intervalo
de fondos de escala de la serie, no como un offset de 10 SCCM a cero voltios.

Fuente: [catalogo Aera Transformer del fabricante, especificaciones y codigos](https://www.fap-gmbh.de/wp-content/uploads/2022/03/Aera_FC-PAR78xx_DN78x_Series__English_0328.pdf).
Si se confirma FS=5,000 SCCM, lectura SCCM=V/5*5000 y limite de consigna
directa=4095 SCCM (81.9%). Esos valores son condicionales; FULL_SCALE_SCCM
sigue sin configurar. Falta gas activo y configuracion de valvula/pin1.

### Estado inicial solicitado para el Aera

La valvula debe estar cerrada desde el principio, confirmado por el usuario.
Esto describe el comportamiento requerido, no confirma que sea una variante NC.
Actualmente MassControl no escribe al arrancar ni acciona el pin 1: el cierre
inicial aun no esta implementado. Falta identificar la señal electrica del
override y su liberacion para permitir regulacion manual por el pin 6.

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

## Buzzer de alarma

La salida RELAYplate2 address 2, rele 8 (boton 16) se asigna a Buzzer.
El control manual permite encenderlo y apagarlo. Condicion automatica vigente:
alarma High room temperature (activa con Room > 29 °C, se desactiva con <= 28 °C), ver la seccion 4. Emergency lo
apaga junto con las demas salidas. El cambio de nombre no activa el rele.

## Water Chiller habilitado — decision vigente

Por nueva indicacion del usuario, Water Chiller vuelve a estar activo en
RELAYplate2 address 1, rele 2. Se restauran el boton manual, su encendido
y espera de 120 segundos en startup, y su apagado en shutdown. Se cancela
la reserva propuesta en address 5. Los bloqueos generales siguen vigentes.

## Reasignacion vigente de RELAYplate2

Las dos placas de reles usan addresses 1 y 2. El mapa actualizado de arriba
es la fuente para Manual Control, startup, shutdown y Emergency; todos usan
RELAYS de manual_control.py. Buzzer conserva el rele 8 de la segunda placa,
ahora (2,8). No cambian las condiciones de habilitacion ni se accionan salidas
por editar este mapa. THERMOplate sigue en 2, ADCplate en 3 y DAQC2plate en 4.

## Secciones reservadas para grupos futuros — estado vigente

Manual Gas Flow Control, Automatic Vacuum y Vacuum Levels quedan sin
controles activos. Se conserva el diseño original con controles deshabilitados y el frontend indica
“No habilitado — Proximamente para grupos futuros”. No se consulta la
consigna manual del DAC; GET/POST /api/mass-flow rechazan su uso.

Gas Mass Flow Meter tambien queda deshabilitado, sin lectura periodica de S4.
Se conserva el diseño del medidor sin datos; la carga de masscontroll.js queda
comentada. El frontend indica
“No habilitado — Proximamente para grupos futuros”. La API entrega mass_flow
como null. Se conservan las graficas Medium/High y
las condiciones de vacio del control manual de reles y startup. MassControl
sigue disponible internamente para enviar cero durante Emergency; deshabilitar
el panel no elimina esa accion de apagado. AutoVacio queda reservado, sin
ciclo automatico conectado a salidas.
