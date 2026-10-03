# Shutdown normal: procedimiento 2026 recibido

Fuente: Shut down Process 2026 capstone edition.pdf, revision de Rey F Mendez
Rosario, 30 de abril de 2026. Se conserva el orden visual del PDF; su numeracion
no es consecutiva. Procedimiento implementado en shutdown.py; validacion fisica pendiente.

## Secuencia del documento

| Paso impreso | Accion en orden de lectura |
|---|---|
| 5 | Operador cierra manualmente la valvula de inyeccion; confirma el cierre y entonces comienza la espera de 120 segundos |
| 6 | Gate Valves A/B OFF |
| 7 | Diffusion Pumps A/B OFF |
| 12 | Esperar que ambas Diffusion Pumps A/B esten a 100 °F o menos (37.777... °C) |
| 9 | Diffuse Valves A/B OFF |
| 8 | Mechanical Pumps A/B OFF |
| 10 | Air Compressor OFF |
| 13 | Cooling Traps A/B OFF |
| 14 | Magnetic Booster Pump OFF |
| 15 | Water Chiller OFF |
| 16 | Water Level Solenoid OFF, fuera del mapa vigente por instruccion previa del usuario |

## Condicion de temperatura confirmada

El usuario confirma que **ambas bombas deben enfriarse hasta 100 °F o menos**.
Esta aclaracion sustituye el «at least» del PDF: la comparacion sera <=, no >=.
100 °F equivale exactamente en el calculo a `(100 - 32) * 5 / 9` °C
(37.777... °C); 37.78 °C es solo el valor redondeado para explicarlo.

Se requieren lecturas validas y actuales de ambas bombas en la misma
comprobacion: THERMOplate address 2, canal 4 (A) y canal 5 (B).
Si una sigue caliente o falta su lectura, no continuar con el siguiente paso.
Las bombas mecanicas y la refrigeracion no reciben orden OFF durante esta espera;
sus ordenes OFF ocurren despues, en el orden de la tabla.

## Cierre de inyeccion manual confirmado

El cierre lo realiza el operador. El paso se representara mediante una
confirmacion de **Valvula de inyeccion cerrada manualmente** antes de iniciar
los 120 segundos. La confirmacion es una declaracion del operador, no una
medicion de cierre. No se manda automaticamente una consigna al Aera para
cumplir este paso ni se asigna otro rele. Ya no queda pendiente identificar
esta valvula para automatizar su cierre, porque este queda manual.

## Correspondencia y limites

Se conserva la exclusion previa de Water Level Solenoid; el PDF no asigna
una nueva salida. El resto de reles figura en CONEXIONES.md. El documento no
indica acciones sobre Chamber Valves ni Buzzer; no se añaden
ordenes para esos equipos por suposicion.

## Diferencia con Emergency Shutdown

Este apagado normal incluye espera y enfriamiento. Emergency Shutdown y el
cierre actual de main.py intentan consigna cero y OFF en los 16 reles de inmediato.
Recibir este PDF no modifica ese comportamiento ni implementa enfriamiento al
cerrar el servidor. El paro de emergencia debe seguir disponible durante la
futura secuencia normal.

La logica del apagado normal esta en shutdown.py, separada del startup y del paro. Las dos aclaraciones estan resueltas: enfriamiento de ambas bombas
y cierre manual. Secuencia y confirmacion en el GUI implementadas; falta validarlas fisicamente. Emergency permanece disponible.

## Operacion del GUI y bloqueo

1. **Start Shutdown Process** bloquea los mandos manuales y pide confirmar el cierre de inyeccion. No envia ordenes de gas ni reles antes de esa confirmacion.
2. **Valvula de inyeccion cerrada manualmente — confirmar** inicia los 120 segundos. No verifica fisicamente el cierre ni escribe al DAC.
3. Ejecuta las acciones de la tabla en orden. Una orden por rele, con consulta de estado.
4. La espera de enfriamiento exige lecturas validas y actuales de A y B <= (100-32)*5/9 °C. No acepta 37.78 como limite redondeado interno.
5. Al completar se liberan los mandos manuales, salvo paro activo. No reabre gas ni reinicia automaticamente el startup.

El panel muestra paso, total y estado. El desplegable muestra condicion,
temperaturas A/B por separado, segundos restantes, error y lista de avance.
No mantiene lecturas vencidas como actuales.

Startup y shutdown no pueden ejecutarse simultaneamente: el servidor rechaza
iniciar shutdown si startup esta running, awaiting_gas, failed o stopped.
Terminar startup normalmente o usar Emergency para interrumpir. No se cancela
silenciosamente una secuencia por iniciar otra. El shutdown puede iniciarse con
startup idle o complete; no exige haber ejecutado el startup en esta sesion.
Ambas secuencias son de una ejecucion por instancia del servidor.

Las protecciones estan en Python y en el GUI, incluyendo llamadas desde otras
pestañas. Emergency no pasa por el bloqueo manual y sigue accesible. Cerrar
main.py conserva el paro inmediato existente: no espera enfriamiento. Cerrar
la pestaña no cancela el shutdown del servidor.

## Arquitectura y API

| Archivo | Funcion |
|---|---|
| shutdown.py | Modulo independiente: pasos, estado, confirmacion manual, temporizador y enfriamiento |
| main.py | Instancia compartida y rutas; exclusion de mandos y startup |
| startup.js | Presentacion de ambas secuencias; bloqueo combinado de paneles |
| vacuum_controller.html | Botones y detalle de shutdown |
| errores.py | SHUTDOWN_LOCKED y SHUTDOWN_STATE |

GET /api/shutdown consulta el estado. POST /api/shutdown con JSON {} inicia;
POST /api/shutdown/confirm-gas con JSON {} confirma cierre manual. Se conservan
validaciones de origen y formato. No hay ruta para saltar pasos.

## Fallos y recuperacion

- SHUTDOWN_LOCKED: esperar al fin; Emergency disponible.
- SHUTDOWN_STATE: inicio duplicado, startup incompatible o confirmacion fuera de etapa. Consultar estado; no reenviar ordenes inciertas.
- Lectura invalida, ausente, no finita, futura o mayor de 15 segundos: seguir esperando sin timeout ni ordenes posteriores.
- Orden de rele sin confirmar: failed, bloqueo conservado y sin reintento automatico; usar Emergency y revisar equipo.
- Paro: stopped; ninguna orden posterior. El acceso hardware en curso puede retrasar el paro de software.

Se comprobaron espera manual, tiempo, orden de reles, enfriamiento de ambas,
limite exacto, datos invalidos/vencidos, exclusividad, paro y fallo de orden.
32 pruebas de software pasaron en total. No se probaron equipos fisicos ni se
completo revision visual del nuevo panel. No se añade un modo simulado al producto.

## Water Chiller habilitado — decision vigente

Por nueva indicacion del usuario, Water Chiller vuelve a estar activo en
RELAYplate2 address 1, rele 2. Se restauran el boton manual, su encendido
y espera de 120 segundos en startup, y su apagado en shutdown. Se cancela
la reserva propuesta en address 5. Los bloqueos generales siguen vigentes.
