# Preparar un Raspberry Pi nuevo (con internet)

Pasos para dejar listo un Pi antes del primer `npm start`. Solo se hacen una vez por Pi. Todo se escribe en la terminal del Pi (directo o por SSH).

La carpeta trae **Node-RED**, que se instala dentro de ella con `npm ci`. Lo que **no** trae es **Node.js** (el programa `node`, que ejecuta Node-RED) ni `npm`. Esos van instalados en el sistema.

## 1. Revisar si ya tiene Node.js

```bash
node -v
npm -v
```

- Si ambos muestran una versión y `node -v` es **v18 o mayor**, saltar al paso 3.
- Si dice `command not found` o la versión es menor de 18, seguir con el paso 2.

## 2. Instalar Node.js y npm

```bash
sudo apt update
sudo apt install -y nodejs npm
node -v
npm -v
```

`node -v` debe dar v18 o mayor. Node-RED 4 necesita Node.js 18 como mínimo.

Si la versión de `apt` resulta menor de 18, instalar la versión 22 desde NodeSource:

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
node -v
```

## 3. Revisar Python y Pi-Plates

```bash
python3 -c "import piplates.RELAYplate2, piplates.THERMOplate, piplates.ADCplate, piplates.DAQC2plate; print('Pi-Plates OK')"
```

Debe decir `Pi-Plates OK`. Si falla, `main.py` no podrá arrancar (`HW_IMPORT`). SPI también debe estar habilitado: `sudo raspi-config` → Interface Options → SPI → Enable.

## 4. Copiar la carpeta al escritorio

Desde el pendrive, copiar `Node-RED final` al Desktop del Pi. No ejecutarla desde el pendrive.

```bash
ls "$HOME/Desktop/Node-RED final"
```

Debe mostrar, entre otros, `package.json`, `launch.js`, `main.py` y `flows-vacuum.json`.

## 5. Revisar que nada más use los puertos

```bash
sudo systemctl stop nodered 2>/dev/null; sudo systemctl disable nodered 2>/dev/null
ss -ltn | grep -E ':(8000|1880|1881) ' || echo "Puertos libres"
```

Debe decir `Puertos libres`. Si aparece algo, cerrar ese programa: otra copia de este proyecto, la simulación o `producto final/main.py`.

## 6. Instalar Node-RED dentro de la carpeta

```bash
cd "$HOME/Desktop/Node-RED final"
npm ci
```

Descarga Node-RED y el Dashboard a `node_modules/` (unos 230 MB). Necesita internet. Los avisos de `npm audit` o `funding` se pueden ignorar. Solo se repite si cambia `package-lock.json`.

## 7. Arrancar

```bash
cd "$HOME/Desktop/Node-RED final"
npm start
```

Debe aparecer:

- `http://127.0.0.1:8000 | Control de reles conectado` (main.py, placas detectadas)
- `NODE-RED vacuum: http://127.0.0.1:1880/dashboard/main`
- `NODE-RED dashboard: http://127.0.0.1:1881/dashboard/main`

| Página | URL |
|---|---|
| Vacuum Controller | http://127.0.0.1:1880/dashboard/main |
| Dashboard | http://127.0.0.1:1881/dashboard/main |
| Editores Node-RED | http://127.0.0.1:1880/red y http://127.0.0.1:1881/red |

Para detener: **Ctrl+C**. Los relés se apagan al cerrar.

## Si algo falla

| Mensaje | Qué hacer |
|---|---|
| `node: command not found` o `npm: command not found` | Volver al paso 2 |
| `npm ci` falla por red | Revisar internet y repetir `npm ci` |
| `HW_IMPORT` | Pi-Plates no instalado en ese Python (paso 3). Si está en un entorno virtual: `PYTHON=/ruta/venv/bin/python3 npm start` |
| `HW_ID` | Una placa no responde en su address: revisar conexión, alimentación y jumpers (CONFIGURACION.md) |
| `EADDRINUSE` o `Address already in use` | Un puerto está ocupado (paso 5) |
| `main.py termino (codigo 1); cerrando todo.` | Leer el error de `main.py` justo arriba de esa línea |

Más detalles en [README.md](README.md).
