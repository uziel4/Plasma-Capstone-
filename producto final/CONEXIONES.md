# Conexiones de todos los modulos — producto final

## Definiciones vigentes

- Low/Medium: Terranova 906A, ADCplate 3/S0, `P(Torr) = 10^(2V - 3)`.
- High: Granville-Phillips 270, el del manual recibido, ADCplate 3/S1; conserva `gp270_a_torr`.
- Medium usa ahora la formula del manual Terranova 906A, por instruccion del usuario. High conserva su conversion GP270. Falta validacion fisica.
- Rough Manifold A/B son para otro grupo: quedan en blanco, sin lecturas activas de S2/S3.
- Reactor Water Line Temperature es el RTD en ADC3/I0, solo para visualizar en Dashboard, sin condicionar el startup.
- Coolant es distinto de Water. Room sigue sin sensor definido.
- El startup vigente es [STARTUP_2026.md](STARTUP_2026.md): Medium para 30–1 mTorr, esperar si no se cumple una condicion o falla la lectura, y regulacion final del gas manual.
- Water Level Solenoid queda excluido. Las fuentes de plasma pertenecen a otro grupo.


Este mapa describe las asignaciones actuales del programa. No confirma que el
cableado fisico ya se haya verificado. **HAY DUDA** identifica informacion faltante;
no se debe completar un borne por suposicion. Los addresses, canales y numeros de
rele no son numeros de pin GPIO del Raspberry Pi.

## 1. Stack del Raspberry Pi

| Placa | Address configurado | Uso |
|---|---|---|
| RELAYplate2 | 0 | Reles 1-8 |
| RELAYplate2 | 1 | Reles 1-8 |
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
| Air Compressor | RELAYplate2 / 0 | 1 |
| Water Chiller | RELAYplate2 / 0 | 2 |
| Booster Pump | RELAYplate2 / 0 | 3 |
| Cool Trap A | RELAYplate2 / 0 | 4 |
| Cool Trap B | RELAYplate2 / 0 | 5 |
| Diffuse Valve A | RELAYplate2 / 0 | 6 |
| Diffuse Valve B | RELAYplate2 / 0 | 7 |
| Chamber Valve A | RELAYplate2 / 0 | 8 |
| Chamber Valve B | RELAYplate2 / 1 | 1 |
| Mechanical Pump A | RELAYplate2 / 1 | 2 |
| Mechanical Pump B | RELAYplate2 / 1 | 3 |
| Diffusion Pump A | RELAYplate2 / 1 | 4 |
| Diffusion Pump B | RELAYplate2 / 1 | 5 |
| Gate Valve A | RELAYplate2 / 1 | 6 |
| Gate Valve B | RELAYplate2 / 1 | 7 |
| Microwave Cooling | RELAYplate2 / 1 | 8 |

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

**HAY DUDA:** confirmar que las sondas instaladas sean tipo K y verificar su
polaridad. Room va aparte: **HAY DUDA** sobre sensor, alimentacion y conexion.
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
| 1 | VALVE OPEN/CLOSED, forzado | **HAY DUDA:** estado normal y circuito para la variante exacta; programa no lo acciona |
| 2 | OUTPUT 0-5 V | ADCplate address 3, S4; caudal medido |
| 3 | +15 VDC | Fuente externa preparada por ustedes |
| 4 | COMMON (VALVE RETURN) | **HAY DUDA:** cableado de retorno segun manual de la variante |
| 5 | -15 VDC | Fuente externa preparada por ustedes; no confundir con 0 V |
| 6 | CONTROL 0-5 V | DAQC2plate address 4, DAC0; consigna |
| 7 | COMMON | Referencia analogica; **HAY DUDA:** distribucion final de retornos |
| 8 | COMMON | Referencia analogica; **HAY DUDA:** distribucion final de retornos |
| 9 | VALVE TEST POINT 0 a +13 V | Sin conexion asignada; no es salida de caudal |

La referencia de las señales de entrada y salida debe concordar con el COMMON
analogico del Aera. Confirmar distribucion de comunes antes de cablear; no
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

**HAY DUDA:** codigo completo MULTI, gas seleccionado y rango activo en SCCM.
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
| MAX31865/PT100 de pruebas anteriores | Fuera de la ruta actual; Water usa transmisor 4–20 mA en I0. Room sin definir |

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
