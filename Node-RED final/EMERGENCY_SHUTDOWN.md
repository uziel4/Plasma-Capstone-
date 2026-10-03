# Paro de software y cierre del programa

`emergency_shutdown.py` centraliza el apagado solicitado por el usuario.
Ambos GUI incluyen EMERGENCY SHUTDOWN. El Dashboard sigue siendo monitor salvo
esta accion de paro. No se pide confirmacion antes de enviar la orden.

## Acciones implementadas

1. Enclavar el paro en el servidor, bloqueando nuevas ordenes manuales.
2. Intentar consigna cero del Aera, DAQC2 address 4 / DAC0.
3. Intentar OFF en cada uno de los 16 reles asignados, aunque una orden falle.
4. Consultar ambas placas para confirmar mascara de reles cero.
5. Mostrar errores por salida/placa y registrar el resultado en logs/control.log.

Las ordenes manuales y el paro comparten un bloqueo: una orden manual que ya
estaba ejecutandose termina antes del apagado; las siguientes quedan rechazadas.
El boton permite reintentar apagado. No existe rearme en el navegador: el bloqueo
se conserva hasta reiniciar main.py. Reiniciar no enciende salidas automaticamente.

## Cierre de main.py

Ctrl+C, SIGTERM y SIGHUP ejecutan el apagado en el cierre del servidor. Una
excepcion durante serve_forever tambien pasa por ese bloque de cierre.
Un fallo al abrir el puerto, despues de construir los controladores, intenta paro.
No se garantiza apagado si la inicializacion de hardware falla antes de disponer
del controlador. No se impone un timeout al driver: una llamada de hardware
bloqueada puede retrasar o impedir las acciones siguientes.

Cerrar una pestaña del navegador NO cierra main.py y NO dispara el apagado.
Un corte electrico, SIGKILL o fallo del sistema operativo no permite ejecutar
el cierre de Python. Un paro fisico independiente es necesario para esos casos.

## Alcance de la confirmacion

OFF significa rele desenergizado. Cero DAC significa consigna cero: no confirma
cierre mecanico del Aera ni aislamiento del gas. No se conmuta su pin 1 ni se
corta su fuente externa. Los sensores y las placas permanecen alimentados.

El apagado solicitado desenergiza todos los equipos asignados, incluidas bombas
y refrigeracion; no incorpora una secuencia de enfriamiento ni tiempos de espera.
No equivale a una secuencia de parada de proceso validada para bombas de difusion.
Queda pendiente validar fisicamente este comportamiento con el responsable del equipo.

## API y pruebas

GET /api/emergency consulta enclavamiento y ultimo resultado.
POST /api/emergency con JSON {} solicita paro; requiere el mismo origen.
STOP_LATCHED rechaza mandos posteriores de reles y mass flow.
El resultado contiene confirmed y errors: una respuesta HTTP no prueba por si
sola que todas las salidas se apagaron. Ante error de red el GUI indica paro
sin confirmar, sin afirmar que el equipo esta apagado.

Pruebas aisladas: intento en las 16 salidas, consigna cero, continuacion ante
fallos, reintento y rechazo de comandos tras enclavamiento. Prueba fisica pendiente.

## Integracion con startup

El startup comparte el bloqueo de ordenes del paro. Una vez enclavado, no se
envian nuevos pasos ni se acepta confirmar el gas. Las esperas de tiempo no
mantienen el bloqueo; los accesos a hardware si pueden retrasar el paro.
El boton de emergencia queda fuera de los paneles manuales bloqueados.

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

## Procedimiento de shutdown normal recibido

Ver [SHUTDOWN_2026.md](SHUTDOWN_2026.md): cierre de inyeccion manual confirmado por el operador, espera posterior de 120 segundos y enfriamiento de ambas bombas a <=100 °F, confirmado por el usuario. Implementado en shutdown.py; no cambia el paro inmediato ni el cierre actual de main.py. Validacion fisica pendiente.

## Shutdown normal implementado

Modulo separado `shutdown.py`, boton Start Shutdown Process y confirmacion de cierre manual del gas. Espera 120 segundos y mantiene las mecanicas y la refrigeracion hasta que ambas bombas de difusion cumplan <=100 °F. Bloqueo manual y exclusion con startup en Python; Emergency disponible. Detalles, errores y limitaciones en [SHUTDOWN_2026.md](SHUTDOWN_2026.md).
