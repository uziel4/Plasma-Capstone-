# Alcance del proyecto: lo implementado, lo pendiente y las dudas

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


Profesor, ya tenemos programadas las dos interfaces: el Vacuum Controller para
el control manual y el Dashboard para ver las lecturas y los estados del sistema.
Aqui le dejo lo que tenemos adelantado y lo que nos falta para completar el proyecto.

Lo que menciono como programado todavia tenemos que probarlo con los equipos
conectados al Raspberry Pi. Las pruebas del codigo no sustituyen las pruebas fisicas.

## Lo que ya tenemos

- Los 16 reles asignados y el control manual desde el Vacuum Controller.
- Las lecturas de las siete termocuplas, configuradas como tipo K.
- Las presiones de aire, coolant y agua.
- Lecturas de vacio medio y alto. Rough Manifold A/B reservados en blanco.
- La temperatura Water mediante RTD con transmisor de corriente en I0: **°C = (mA - 4) * 6.25**, implementada solo para visualizacion en Dashboard.
- El control manual del mass flow por porcentaje y su lectura de caudal.
- Los mensajes de error para identificar problemas de lectura o comunicacion.
- Los detalles visuales actualizados: se distingue el caudal seleccionado del medido.
- Vacuum Controller reorganizado en cuatro columnas en escritorio, con todos los
  paneles dentro de la vista comprobada de 1512 × 870. El usuario confirmo que
  ahora se ve completo. El boton de emergencia permanece visible arriba.
- Las rutas de scripts y enlaces entre ambos GUI estan corregidas.

El Dashboard se queda como monitor. Los botones de iniciar secuencia, confirmar
y reiniciar se eliminaron del alcance que estamos trabajando.

## Configuracion implementada

Este es el mapa de las placas, equipos y funciones que tenemos en el programa.

### Las placas del Raspberry

| Placa | Address | Uso en el programa |
|---|---|---|
| RELAYplate2 | 1 | Primeros ocho reles |
| RELAYplate2 | 2 | Otros ocho reles |
| THERMOplate | 2 | Siete termocuplas; canal 8 libre |
| ADCplate | 3 | Corrientes y voltajes de los sensores |
| DAQC2plate | 4 | Consigna del mass flow por DAC0 |

Los addresses y canales son los configurados en el programa. No son numeros
de pin GPIO.

### Los 16 reles asignados

| Address | Rele | Equipo |
|---|---|---|
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

El programa envia la orden y consulta el estado de la placa. Eso no confirma
que el equipo fisico haya arrancado. Al iniciar no se manda cambiar los reles;
al cerrar main.py se ejecuta el apagado de software documentado al final.

### Temperaturas y entradas analogicas

| Medicion | Conexion configurada | Lo que hace actualmente |
|---|---|---|
| Coolant temperatura | THERMO 2, canal 1 | Termocupla K, °C |
| Cool Trap A / B | THERMO 2, canales 2 / 3 | Termocuplas K, °C |
| Diffusion Pump A / B | THERMO 2, canales 4 / 5 | Termocuplas K, °C |
| Field Magnet A / B | THERMO 2, canales 6 / 7 | Termocuplas K, °C |
| Water temperatura | ADC 3, I0 | RTD con transmisor: (mA - 4) * 6.25 °C |
| Water presion | ADC 3, I1 | Conversion de 4-20 mA a 0-232 PSI |
| Coolant presion | ADC 3, I2 | Conversion de 4-20 mA a 0-232 PSI |
| Air presion | ADC 3, I3 | Conversion de 4-20 mA a 0-232 PSI |
| Medium Vacuum | ADC 3, S0 | Terranova 906A: 10^(2V - 3) Torr |
| High Vacuum | ADC 3, S1 | GP270, conversion nominal de voltaje negativo |
| Rough Manifold A / B | S2 / S3 reservados | En blanco; ampliacion futura de otro grupo |
| Caudal Aera | ADC 3, S4 | Lectura de 0-5 V como porcentaje |
| Consigna Aera | DAQC2 4, DAC0 | Salida de 0-4.095 V, hasta 81.9% |

Las presiones usan `PSI = max(0, (mA - 4) / 16 * 232)` y avisan si la corriente
sale de 4-20 mA. Necesitamos verificar que el rango 232 PSI corresponda a las
etiquetas de los tres transmisores. Mostrar un valor no negativo no significa
que una corriente fuera de rango sea una medicion confiable.

La formula confirmada para Medium (Terranova 906A) es `P(Torr) = 10^(2V - 3)`. La transferencia nominal por
tramos del GP270 esta detallada en CONFIGURACION.md y requiere validacion fisica;
no la presentamos como una calibracion terminada.

### Como implementamos cada medicion

#### Temperaturas por termocupla

En `temperaturas.py` configuramos THERMOplate address 2 con tipo K para cada
canal y rechazo de ruido de red a 60 Hz. La funcion `getTEMP(2, canal, 'c')`
obtiene la temperatura en Celsius: no aplicamos la formula de corriente usada
para las presiones.

| Medicion | Lectura implementada |
|---|---|
| Coolant | getTEMP en canal 1 |
| Cool Trap A | getTEMP en canal 2 |
| Cool Trap B | getTEMP en canal 3 |
| Diffusion Pump A | getTEMP en canal 4 |
| Diffusion Pump B | getTEMP en canal 5 |
| Field Magnet A / Coil A Temp | getTEMP en canal 6 |
| Field Magnet B / Coil B Temp | getTEMP en canal 7 |

Cada lectura se comprueba por separado. El programa rechaza respuestas no
numericas, no finitas o fuera del intervalo configurado para K (-200 a 1372 °C).
Estos son limites de plausibilidad del codigo, no temperaturas permitidas de
operacion del equipo. Una temperatura negativa valida se conserva.
Si falla un canal, devuelve temperatura nula y el error de ese canal.
`/api/temperatures` entrega las lecturas y los GUI muestran °C.

#### Temperatura Water y Room

Water usa el RTD para temperatura del agua del reactor, confirmado por el usuario. En `temperatura_agua.py`,
`getADC(3, 'I0')` lee la salida del transmisor en mA, no la resistencia directamente.
Aplicamos `°C = (mA - 4) * 6.25`: 4 mA = 0 °C, 12 mA = 50 °C y 20 mA = 100 °C.
El programa rechaza corrientes fuera de 4-20 mA y respuestas no numericas o no
finitas. El Dashboard muestra esta temperatura en °C; el RTD no se muestra en Vacuum Controller. Falta la comprobacion fisica, no definir la formula.

Room se lee del DS18B20 en THERMOplate address 2, puerto 9. No usamos la
temperatura interna de la placa como si fuera la del cuarto. Ver la seccion 4.

#### Presiones de aire, coolant y agua

En `presiones.py` identificamos ADCplate address 3, inicializamos la placa y
seleccionamos modo HIGH. El programa espera un segundo antes de las primeras
lecturas. Cada transmisor se lee por su entrada de corriente:

| Presion | Lectura | Conversion configurada |
|---|---|---|
| Air | getADC(3, 'I3') | 4-20 mA a 0-232 PSI |
| Coolant | getADC(3, 'I2') | 4-20 mA a 0-232 PSI |
| Water | getADC(3, 'I1') | 4-20 mA a 0-232 PSI |

Para los tres usamos `PSI = max(0, ((mA - 4) / 16) * 232)`.
Por ejemplo, 4 mA corresponde a 0 PSI, 12 mA a 116 PSI y 20 mA a 232 PSI.
Son resultados de la escala configurada, todavia sujetos a comprobacion con
la etiqueta y el instrumento real.

Si la corriente sale de 4-20 mA, conservamos el resultado calculado con aviso
de presion no confiable; no lo presentamos como una lectura normal. El calculo
no limita valores superiores a 232 PSI. Una lectura no numerica o una falla de
comunicacion genera error. El Vacuum Controller muestra PSI; los indicadores
de presion del Dashboard usan `bar = PSI / 14.5037738`.

#### Vacio Medium

En `vacio.py` leemos voltaje por separado en ADCplate address 3:

| Medicion | Entrada | Conversion actual |
|---|---|---|
| Medium Vacuum | S0 | 10^(2V - 3) Torr |

Se comprueba que el voltaje sea numerico y finito, y que la conversion produzca
una presion positiva y representable. Cada sensor conserva su propio resultado
o error. Una señal numericamente plausible no demuestra que el sensor este
conectado ni que el modelo fisico use esa transferencia.

#### High Vacuum con GP270

High se lee en S1 del ADCplate address 3 y usa `gp270_a_torr`, separada de la
formula del 972B. El codigo trabaja con la señal negativa de 0 a -5 V y aplica
una interpretacion nominal por tramos, pendiente de validacion fisica.

La implementacion actual calcula `U = -V`, el tramo
`n = max(0, min(4, ceil(U) - 1))` y luego
`P(Torr) = (U - n) * 10 * 10^(n - 8)`.
Los extremos enteros pertenecen al final del tramo anterior. Este detalle y las
transiciones entre rangos siguen pendientes de contrastar con el GP270; la
formula describe lo programado, no una calibracion confirmada.

Se rechaza 0 V como presion no resoluble; los voltajes entre -10 y -12 V se
identifican como estado invalido del controlador. Otros valores fuera de 0 a -5 V
tambien producen error. No se convierten esos errores a cero Torr.

Las lecturas de vacio se entregan con voltaje original, presion en Torr y error.
El Dashboard convierte a mbar con `mbar = Torr * 1.333223874`.

#### Lectura y consigna del mass flow

En `masscontroll.py` separamos la medicion de la orden:

| Funcion | Implementacion |
|---|---|
| Caudal medido | getADC(3, 'S4'), salida del pin 2 del Aera |
| Conversion de lectura | Porcentaje = voltaje * 20; 0-5 V equivale a 0-100% |
| Consigna manual | Voltaje = porcentaje / 20, redondeado a 0.001 V |
| Envio | setDAC(4, 0, voltaje), hacia pin 6 del Aera |
| Consulta posterior | getDAC(4, 0), comparado con la consigna; tolerancia de 0.002 V |

La lectura acepta voltajes finitos de 0 a 5 V; fuera de ese intervalo muestra
error. La consigna admite 0 a 81.9% por el limite de 4.095 V del DAC.
`FULL_SCALE_SCCM` sigue sin configurar, por lo que no se publica un caudal
supuesto en SCCM. Cuando exista ese dato, el calculo previsto es
`SCCM = porcentaje / 100 * fondo_de_escala_SCCM`.

La consulta del DAC confirma el registro de salida, no el caudal. Por eso el
GUI muestra por separado el porcentaje seleccionado y la lectura de S4.

#### Actualizacion de las mediciones

`/api/pressures` agrupa presiones, temperatura RTD Water en °C y corriente del transmisor, vacio y caudal medido.
Temperaturas y lecturas ADC reutilizan resultados durante un segundo para
reducir accesos repetidos. Las pantallas solicitan nuevas lecturas periodicamente;
los errores acompañan al valor del canal correspondiente.

### Que puede hacer cada interfaz

| Parte | Vacuum Controller | Dashboard |
|---|---|---|
| Reles | Permite mandar ON/OFF y consultar estado | Muestra los estados asignados en su diagrama |
| Temperaturas | Muestra las lecturas disponibles y los pendientes | Muestra las temperaturas de su diagrama |
| Presiones | Presenta Air, Coolant y Water en PSI | Conserva sus indicadores en bar |
| Vacio | Lecturas y graficas de Medium/High en Torr; Rough en blanco | Indicadores de vacio en mbar |
| Mass flow | Seleccion manual y caudal medido en porcentaje | No se ha añadido un indicador de mass flow |
| AutoVacio | Regulacion automatica deshabilitada | No ejecuta automatizacion |
| Errores | Avisos de lectura, conexion y mando | Diagnosticos y estados desconocidos |

El campo de caudal automatico en SCCM sigue deshabilitado. El valor seleccionado
manualmente y el caudal medido estan separados para no confundir una orden con
la respuesta real. Los errores de caudal se muestran como texto visible.

### Como esta organizado el codigo

Separamos las funciones en modulos Python, lo que hemos llamado los header files,
para que el codigo principal solo conecte las partes:

| Archivo | Funcion |
|---|---|
| main.py | Servidor local, rutas de las interfaces y apertura del navegador |
| startup.py | Modulo independiente: secuencia, esperas, bloqueo manual y confirmacion de gas |
| startup.js | Botones y estado del startup en Vacuum Controller |
| selector_vacio.py | Seleccion Medium/High para las reglas de AutoVacio |
| emergency_shutdown.py | Paro enclavado y apagado de salidas |
| manual_control.py | Mapa y control de los reles |
| temperaturas.py | Lecturas de termocuplas |
| presiones.py | Presiones y coordinacion de las lecturas del ADC |
| temperatura_agua.py | Lectura de corriente de temperatura Water |
| vacio.py | Lecturas y conversiones de vacio |
| masscontroll.py | Lectura porcentual y mando del Aera |
| autovacio.py | Reglas de direccion del ajuste; ciclo automatico pendiente |
| hardware_bus.py | Coordina acceso al bus entre modulos del servidor |
| errores.py | Mensajes de error y que revisar |
| Archivos JavaScript | Actualizan las pantallas y envian las ordenes manuales |

No hay un modo de simulacion en el producto. Se hicieron pruebas aisladas de
software, incluyendo limites y errores del mass flow, pero falta verificar el
conjunto con hardware real. No estan implementados interlocks generales del
proceso ni un paro automatico global por cerrar la interfaz.

### Como funciona el sistema por dentro

Lo organizamos para separar la pantalla, la comunicacion y el manejo del hardware.
La idea es poder corregir un sensor o una conexion en su modulo sin tener que
reescribir las dos interfaces.

#### 1. La pantalla se comunica con Python

Al ejecutar `main.py`, se inicia un servidor local y se intenta abrir el navegador.
Las pantallas estan hechas en HTML y JavaScript. JavaScript consulta las lecturas
a Python y, en el Vacuum Controller, envia las ordenes manuales.

El recorrido de una orden es:

**Boton del GUI → servidor Python → modulo del equipo → placa → consulta de estado → GUI.**

Para las lecturas es:

**Sensor → placa de lectura → modulo Python → respuesta al navegador → indicador.**

Por eso las interfaces se abren desde la direccion de `main.py`. Abrir solamente
el HTML con Live Server no conecta el control con Python.

#### 2. Cada modulo se encarga de su equipo

Los addresses, canales y conversiones estan en los modulos correspondientes.
`main.py` recibe las solicitudes y llama esas funciones. Las respuestas llevan
los valores o el error que explica por que no se pudo obtener una lectura.

Los dos GUI consultan el mismo servidor. Asi usamos las mismas conversiones de
origen y luego mostramos las unidades que corresponden a cada pantalla.

#### 3. Las lecturas se actualizan sin mandar ordenes

Las pantallas consultan periodicamente los sensores. Para evitar repetir trabajo,
las lecturas de temperaturas y ADC se reutilizan durante un intervalo corto.
`hardware_bus.py` coordina el acceso al bus SPI entre los modulos del servidor.

Ese bloqueo solo coordina este programa: no debemos ejecutar al mismo tiempo
lectores antiguos que vuelvan a configurar las placas por separado.
Consultar una lectura no debe arrancar una bomba ni cambiar el caudal.

#### 4. Las ordenes se revisan antes de aplicarse

En reles, el servidor comprueba que el equipo exista y que la orden sea ON u OFF.
Despues consulta el estado de la placa. En mass flow, comprueba que la consigna
sea numerica y este entre 0 y 81.9%, la convierte a voltaje y consulta el DAC
tras escribir.

La confirmacion corresponde al estado registrado en la placa. No es una medicion
de movimiento de una valvula, funcionamiento de una bomba o circulacion de gas.
Por eso el Aera tiene una lectura de caudal separada de la consigna.

#### 5. Los errores se muestran sin inventar lecturas

Los errores tienen un codigo, una descripcion y una indicacion de que revisar.
Las pantallas muestran datos desconocidos o sin lectura cuando no hay una respuesta
valida. No se interpreta una perdida de comunicacion como equipo apagado.

Los fallos de un canal se manejan por separado cuando es posible. El servidor
registra diagnosticos en la terminal y en `logs/control.log`; los archivos de log
rotan para limitar su crecimiento. Las ordenes fallidas no se reenvian automaticamente,
porque una orden pudo haberse aplicado aunque su confirmacion no llegara.

#### 6. Que comprobamos y que falta para decir que esta validado

Se reviso sintaxis y se hicieron pruebas aisladas del mass flow: conversion a
voltaje, rechazo de entradas invalidas, lectura sin escribir salidas, envio de
consigna cero y deteccion de una confirmacion que no coincide. Tambien se revisaron
detalles del GUI en navegador.

Esto nos permite revisar la estructura y parte del comportamiento del software,
pero no afirmar todavia que todo el sistema esta validado para operar el reactor.
Nos faltan las pruebas fisicas, las calibraciones, el control automatico completo
y definir las protecciones y respuestas del proceso ante fallos.

## 1. Completar el AutoVacio

AutoVacio seleccionara la lectura segun el rango de vacio: Medium (Terranova 906A, ADC3/S0) en rango medio y High (GP270, ADC3/S1) en alto vacio. El selector por rango esta implementado sin exigir concordancia entre sensores; ver SELECCION_VACIO.md para rangos y limites. Solo se podran usar lecturas validas.

Ya tenemos definida la idea de funcionamiento: las bombas mecanicas A y B se
quedan encendidas durante AutoVacio. Si la presion baja mas de lo que queremos,
el mass flow aumenta el gas. Si la presion sube y perdemos vacio, reduce el gas.

En el codigo tenemos la logica que decide si hay que aumentar, reducir o mantener
el caudal. Nos falta programar el ciclo completo que lee la presion y manda los
ajustes al equipo. Por eso el modo automatico todavia esta deshabilitado.

Tenemos que definir estas dudas:

- Selector por rango implementado: High valido entre 3e-9 y 0.001 Torr. Regreso implementado por Medium valido > 1 × 10⁻³ Torr; falta validar fisicamente y conectar el ciclo; ver SELECCION_VACIO.md.
- ¿Cuanto puede variar la presion alrededor del valor deseado? Esa seria la tolerancia.
- ¿Cuanto vamos a aumentar o reducir el caudal en cada ajuste y cada cuanto tiempo?
- ¿El flujo deseado va a ser el valor inicial o el maximo permitido?
- ¿Que hacemos con el gas y las bombas si falla el sensor o se pierde la lectura?
- ¿Como queda el sistema cuando quitamos AutoVacio o queremos pasar a manual?

Rough A/B quedan en blanco; sus barras no indican avance. AutoVacio sigue deshabilitado.

## 2. Terminar de configurar y probar el mass flow

Vamos a usar el Aera Transformer multigas. Ya esta programado el control manual
con estas conexiones asignadas:

| Funcion | Conexion |
|---|---|
| Mandar el caudal deseado | DAQC2plate address 4, DAC0 hacia pin 6 del Aera |
| Leer el caudal | Pin 2 del Aera hacia S4 del ADCplate address 3 |

Main Valve representa la valvula interna del Aera. En manual aplicamos el caudal
que seleccionamos; no estamos mandando a abrir completamente la valvula por el
pin de forzado. Al apagar ese control se envia consigna cero, pero tenemos que
comprobar fisicamente la respuesta y el cierre de la valvula.

### Dudas que quedan del mass flow

- Modelo base FC-PA7800 confirmado. Confirmar el gas seleccionado y el fondo de escala activo. Aunque sea
  multigas, necesitamos esos datos para mostrar el caudal en SCCM. Por ahora
  trabajamos en porcentaje del rango del equipo.
- Confirmar como debe quedar el pin 1 para que el Aera siga la consigna normal
  y no quede forzado a abrir o cerrar. Tambien falta confirmar la variante
  normalmente abierta o normalmente cerrada.
- Probar que el voltaje que mandamos corresponda al caudal que lee el equipo.

**La alimentacion de +/-15 V la vamos a preparar nosotros.** Esa parte no la
produce el Raspberry; queda verificarla junto con el cableado y los comunes.

### El limite que encontramos

La salida DAC de la DAQC2 llega a 4.095 V y el Aera usa 0-5 V para pedir 0-100%.
Con la conexion directa podemos mandar hasta 81.9% del rango. El programa ya
respeta ese limite.

Ya confirmamos que se queda con el limite de 81.9% (4.095 V). No queda
pendiente adaptar la salida para llegar a 100%; conservamos la escala real.

## 3. Temperatura del agua: RTD implementado, validacion fisica pendiente

El RTD es para Water. La formula confirmada es `(mA - 4) * 6.25` en °C,
leyendo el transmisor por ADCplate address 3, I0. La escala ya no es una duda.
Falta contrastar la temperatura mostrada con una referencia fisica.
Water sigue independiente de Coolant (termocupla) y de Room (DS18B20, puerto 9).

## 4. Room (lab temp) y alarma High room temperature — implementado

Room se lee del DS18B20 conectado al puerto 9 del THERMOplate, address 2, el
mismo de las termocuplas: `getTEMP(2, 9, 'c')`, igual que cualquier termocupla.
No se llama `setTYPE` para el puerto 9 (solo aplica a canales 1-8). Se acepta
una lectura numerica, finita y dentro del rango del DS18B20 (-55 a 125 °C);
fuera de eso queda error `TEMP_RANGE` y Room se muestra sin lectura.
`/api/temperatures` entrega `temperatures.Room` (canal 9) y `room_alarm`.

El laboratorio ronda 21-22 °C. La alarma **High room temperature** se activa
cuando Room es **mayor de 29 °C** (29.0 exacto no la activa):

- `alarma_room.py` revisa Room cada 2 s en un hilo que arranca con main.py,
  aunque no haya un GUI abierto.
- Al activarse enciende el **Buzzer** (RELAYplate2 address 2, rele 8) y lo
  registra en logs. Se desactiva al bajar a **28 °C o menos** (histeresis de
  1 °C) y entonces apaga el Buzzer, solo si lo encendio la alarma. Entre 28 y
  29 °C conserva el estado: no se activa desde normal ni se apaga si ya sono. Apagar el Buzzer a mano lo silencia mientras siga la alarma.
- Una lectura invalida no activa ni desactiva: conserva el estado y muestra el error.
- Con Emergency activo no se acciona el Buzzer; el aviso sigue visible.
- Vacuum Controller: el recuadro Room se pone rojo con "HIGH ROOM TEMPERATURE"
  y el estado de temperaturas lo indica. Dashboard: la barra superior dice
  "ALARMA: HIGH ROOM TEMPERATURE" y Diagnosticos muestra la lectura.
- Falta validacion fisica: conexion del DS18B20 al puerto 9 y comparacion con
  un termometro de referencia.

Pruebas: `tests/test_room_alarm.py` (lectura del puerto 9, rango, limite de
29 °C, banda de 28 °C, encendido/apagado del Buzzer, lectura invalida y Emergency).

## 5. Field Coil A/B: indicador por tendencia implementado

Por decision del usuario, el Dashboard enciende el indicador cuando la temperatura
sube entre dos lecturas nuevas, comparadas a la resolucion visible de 0.1 °C.
A usa Field Magnet A (THERMO2/canal6); B usa Field Magnet B (canal7).
Verde significa subiendo; rojo estable o bajando; gris sin lectura o esperando
la segunda muestra. Un error reinicia la comparacion. No confirma encendido
electrico, no acciona reles ni forma un interlock. Validacion fisica pendiente.

## 6. Validar las lecturas de vacio

Medium (Terranova 906A) conserva la formula confirmada. High usa la conversion
nominal por tramos del GP270, con su salida negativa.

Nos falta comparar las lecturas de los controladores con los voltajes que lee
el ADC en varios puntos. En el GP270 tenemos que revisar especialmente los
cambios de rango. Si la conversion no coincide, tenemos que corregirla antes
de usar esa lectura para AutoVacio.

El servidor trabaja el vacio en Torr. El Vacuum Controller lo muestra en Torr
y el Dashboard conserva mbar, como estaba previsto.

## 7. Validacion pendiente de ambos GUI

El software tiene pruebas aisladas y revisiones visuales. Sigue pendiente la
validacion completa con los equipos reales en el Raspberry Pi:

- Correspondencia entre ordenes manuales y respuesta de los equipos.
- Exactitud de temperaturas, presiones, vacio y caudal.
- Respuesta del mass flow frente a la consigna enviada.
- Presentacion de errores y recuperacion de las lecturas ante fallos de comunicacion.
- Visualizacion de ambos GUI con datos reales en la pantalla del Raspberry.
- Funcionamiento de AutoVacio, cuyo ciclo completo aun no esta implementado.

Estas son validaciones pendientes, no dudas sobre las conexiones de los reles.
El mapa de los 16 reles queda documentado en la seccion de configuracion.

Los textos del GUI ya distinguen control manual disponible de AutoVacio pendiente.
La presentacion en SCCM sigue pendiente de su escala. Water ya muestra °C.

Los detalles de configuracion estan en [CONFIGURACION.md](CONFIGURACION.md) y
las reglas de AutoVacio en [AUTOVACIO.md](AUTOVACIO.md).


## Actualizacion: apagado y emergencia

Implementado el paro de software en ambos GUI y al cerrar main.py: consigna
cero del mass flow, OFF en los 16 reles y bloqueo de nuevas ordenes hasta reiniciar.
Esta actualizacion sustituye las descripciones anteriores que indicaban que el
cierre del servidor conservaba las salidas. Cerrar la pestaña no cierra el servidor.
No actua ante perdida de alimentacion o SIGKILL ni confirma cierre mecanico del gas.
Alcance, errores y limites: [EMERGENCY_SHUTDOWN.md](EMERGENCY_SHUTDOWN.md).
Validacion fisica y secuencia de enfriamiento del proceso pendientes.




## 8. Startup implementado: validacion fisica pendiente

Water Level Solenoid se elimina del mando de la secuencia; no falta asignarle
un rele. Se mantienen las esperas del procedimiento. El vacio de 30-1 mTorr
se comprobara con Medium Vacuum (ADC3/S0). Si una condicion no se cumple,
se espera sin timeout; una lectura invalida muestra error y no permite avanzar.
El paro de emergencia debe seguir disponible durante la espera.
El paso final de gas y regulacion queda manual, confirmado por el usuario.
Estos requisitos estan documentados en STARTUP_2026.md; el secuenciador ya esta implementado y requiere validacion fisica.


## Conversion Medium actualizada al manual

Se aplica `P(Torr)=10^(2V - 3)` en S0. Los estados LO/OFF/HI no se interpretan como presion valida. Detalles, ejemplos y limites del cambio Medium/High en [SELECCION_VACIO.md](SELECCION_VACIO.md). La formula esta implementada y probada en software; el selector por rango esta implementado; el regreso usa Medium valido > 1 × 10⁻³ Torr, sin esperar un valor superior al rango de High. Falta validacion fisica. AutoVacio no se habilita con este cambio.

## Startup implementado: control y confirmacion de gas

Start Startup Process ejecuta la secuencia de [STARTUP_2026.md](STARTUP_2026.md).
Bloquea reles y caudal manuales hasta que termine, con proteccion en servidor
para todas las pestañas. Emergency Shutdown permanece disponible. Al final,
**Gas ajustado manualmente — confirmar** registra el ajuste realizado en el
equipo y libera el control manual. No manda gas automaticamente. La secuencia
ya esta programada; faltan pruebas fisicas. El ciclo AutoVacio sigue pendiente.

## Procedimiento de shutdown normal recibido

Ver [SHUTDOWN_2026.md](SHUTDOWN_2026.md): cierre de inyeccion manual confirmado por el operador, espera posterior de 120 segundos y enfriamiento de ambas bombas a <=100 °F, confirmado por el usuario. Implementado en shutdown.py; no cambia el paro inmediato ni el cierre actual de main.py. Validacion fisica pendiente.

## Shutdown normal implementado

Modulo separado `shutdown.py`, boton Start Shutdown Process y confirmacion de cierre manual del gas. Espera 120 segundos y mantiene las mecanicas y la refrigeracion hasta que ambas bombas de difusion cumplan <=100 °F. Bloqueo manual y exclusion con startup en Python; Emergency disponible. Detalles, errores y limitaciones en [SHUTDOWN_2026.md](SHUTDOWN_2026.md).

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
