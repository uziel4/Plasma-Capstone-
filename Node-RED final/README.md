# Node-RED final — Vacuum Controller y Dashboard del reactor

Versión de uso real del producto final, servida por Node-RED. **Controla hardware real** (Pi-Plates). No contiene simulación: no hay `planta.py`, panel de pruebas ni banner de simulación.

- Backend: `main.py` y sus módulos, los mismos de `producto final`. Python lee y controla las placas y aplica todas las reglas de seguridad.
- GUI: las pantallas originales (HTML, CSS y JavaScript) dentro de un nodo `ui-template` de FlowFuse Dashboard 2, una por instancia Node-RED.
- Node-RED solo sirve las pantallas y reenvía `/api/*` a `main.py`. No decide permisos ni secuencias.

```
Navegador :1880 (Vacuum Controller) ─┐
                                     ├─> Node-RED /api/* (proxy) ─> main.py 127.0.0.1:8000 ─> Pi-Plates
Navegador :1881 (Dashboard)        ──┘
```

## Requisitos en la Raspberry Pi

**Pi nuevo:** seguir primero [INSTALACION_PI.md](INSTALACION_PI.md), que explica cómo instalar Node.js, revisar Pi-Plates y hacer `npm ci`.

- SPI habilitado y las placas en sus addresses: RELAYplate2 1 y 2, THERMOplate 2, ADCplate 3, DAQC2plate 4. Ver CONFIGURACION.md.
- Python 3 con el paquete Pi-Plates instalado. Debe ser el mismo entorno donde ya funcionaba `producto final/main.py`. Si usa un entorno virtual: `PYTHON=/ruta/al/venv/bin/python3 npm start`.
- Node.js y npm. Node-RED **no** se instala aparte: viene como dependencia de esta carpeta.
- No ejecutar al mismo tiempo `producto final/main.py`, la simulación ni el servicio `nodered` del sistema. Comparten puertos (8000, 1880 y 1881) y placas.

## Instalar y arrancar

```bash
cd "$HOME/Desktop/Node-RED final"
npm ci        # solo la primera vez o si cambia package-lock.json
npm start
```

`npm start` ejecuta `launch.js`, que arranca tres procesos:

1. `main.py --port 8000 --no-browser`: el backend. Verifica las placas al iniciar.
2. Node-RED del Vacuum Controller en el puerto 1880.
3. Node-RED del Dashboard en el puerto 1881.

Con sesión gráfica, a los 8 segundos se abre el Vacuum Controller en el navegador del Pi. Para no abrirlo: `NO_BROWSER=1 npm start`.

**Si cualquiera de los tres procesos termina, `launch.js` cierra los otros.** Por ejemplo, si faltan las placas o Pi-Plates, `main.py` sale con `HW_IMPORT` o `HW_ID` y todo se detiene con el mensaje del error. Al cerrarse, `main.py` ejecuta su apagado de software: mass flow en cero y los 16 relés en OFF. `launch.js` espera a que termine (hasta 15 s).

**Ctrl+C** detiene todo de la misma forma. Cerrar una pestaña del navegador no detiene nada. El paro de software no actúa ante pérdida de energía o `kill -9`; ver EMERGENCY_SHUTDOWN.md.

## Páginas

| Qué | URL |
|---|---|
| Vacuum Controller | http://127.0.0.1:1880/dashboard/main |
| Dashboard del reactor | http://127.0.0.1:1881/dashboard/main |
| Editor Node-RED (vacuum) | http://127.0.0.1:1880/red |
| Editor Node-RED (dashboard) | http://127.0.0.1:1881/red |

Todo escucha solo en `127.0.0.1`. Desde la Mac, con un túnel SSH:

```bash
ssh -N -L 1880:127.0.0.1:1880 -L 1881:127.0.0.1:1881 uziel4@192.168.0.222
```

## Editar las pantallas

Hay dos formas. Use solo una:

- **En Node-RED:** abrir `/red`, doble clic en el `ui-template` («Vacuum Controller (HTML/CSS/JS)» o «Reactor Dashboard (HTML/CSS/JS)») y **Deploy**. Se guarda en `flows-vacuum.json` o `flows-dashboard.json`.
- **En los archivos fuente:** editar `vacuum_controller.html`, `dashboard.html` o sus `.js` y ejecutar `python3 build_dashboards.py`. **Esto reemplaza lo editado en `/red`.**

El proxy está en `flows.json`, que es la plantilla para ambas instancias. Si `main.py` no responde, el proxy devuelve **502** `NODE_RED_PROXY` y la GUI muestra que la orden no se confirmó. Nunca responde un falso OK.

## Qué incluye

Las mismas reglas que `producto final`:

- Control manual de los 16 relés, con estado confirmado por las placas.
- Permisos del procedimiento de startup 2026:
  - Diffuse Valve A/B: requieren Air Compressor, Water Chiller, Booster Pump y Cool Trap A/B encendidos.
  - Chamber Valve A/B: lo anterior más Diffuse Valve A/B.
  - Gate Valve A/B: pasos 2–7, Mechanical Pump A/B y Diffusion Pump A/B encendidos; Medium entre 0.001 y 0.030 Torr; ambas difusiones entre 250 y 300 °F; Chamber Valve A/B apagadas.
  - Diffusion Pump A/B: Medium menor de 0.030 Torr.
  - Booster Pump siempre habilitado. Buzzer temporal. Apagar (OFF) siempre está permitido.
- Startup y shutdown automáticos, Emergency Shutdown en ambas pantallas.
- Temperaturas (7 termocuplas K), Water RTD, presiones, Medium y High Vacuum.
- Room (lab temp): DS18B20 en THERMOplate address 2, puerto 9. La alarma **High room temperature** se activa con Room > 29 °C, enciende el Buzzer y se desactiva con ≤ 28 °C.
- Secciones de grupos futuros (mass flow, AutoVacío, Rough A/B) visibles pero deshabilitadas.

Detalles en PENDIENTES.md, CONFIGURACION.md, CONEXIONES.md, STARTUP_2026.md, SHUTDOWN_2026.md, EMERGENCY_SHUTDOWN.md y REVISION_SRS.md. Son copias de `producto final`.

## Pruebas

```bash
python3 -m unittest discover -s tests   # reglas y módulos; sin hardware (usan dobles de prueba)
node tests/test_manual_polling.cjs
node tests/test_nodered.cjs             # con npm start activo; SOLO LECTURA, no envía órdenes
```

`tests/test_nodered.cjs` no hace POST: se puede correr con el reactor conectado. Para probar órdenes, secuencias y Emergency sin equipo, usar la carpeta `node red sim`.

## Copiar desde la Mac al Pi

Primero detener `npm start` en el Pi (Ctrl+C). Luego, en la Mac:

```bash
cd ~/Plasma-Capstone-
COPYFILE_DISABLE=1 tar --no-xattrs --no-mac-metadata --exclude node_modules --exclude .runtime --exclude __pycache__ --exclude logs -czf - "Node-RED final" | ssh uziel4@192.168.0.222 'mkdir -p ~/Desktop && tar -xzf - -C ~/Desktop'
```

## Verificación realizada (3 de octubre de 2026, en la Mac)

- Pruebas Python de `tests/`: pasan. `test_manual_polling.cjs`: pasa.
- Sin Pi-Plates, `npm start` mostró `HW_IMPORT` y cerró los tres procesos con código 1.
- Las dos instancias Node-RED contra un backend con la misma API: `test_nodered.cjs` pasó, las pantallas cargaron sin errores de consola y sin elementos de simulación.
- Con el backend apagado, el proxy respondió 502 en lecturas y en Emergency.

**Pendiente:** primera ejecución en el Pi con las placas conectadas y validación física. Ver PENDIENTES.md.
