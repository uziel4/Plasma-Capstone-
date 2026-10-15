#!/bin/bash
# Arranca Node-RED final: main.py + Vacuum Controller (:1880) + Dashboard (:1881).
# Lo usa el icono del escritorio (instalar_icono.sh). Ctrl+C o cerrar la ventana detiene todo.
cd "$(dirname "$(readlink -f "$0")")" || exit 1
echo "Plasma Reactor SCADA · Node-RED final (con bloqueos)"
echo "Carpeta: $PWD"
echo

pausa() { echo; read -r -p "Presione Enter para cerrar esta ventana..." _; }

# Si usan un entorno virtual de Python con Pi-Plates, ponga su ruta aqui, por ejemplo:
# export PYTHON="$HOME/plasma-venv/bin/python3"

if ! command -v npm >/dev/null 2>&1; then
  echo "No se encontro npm. Instale Node.js siguiendo INSTALACION_PI.md."
  pausa; exit 1
fi
if [ ! -d node_modules ]; then
  echo "Primera vez: instalando dependencias (npm ci)..."
  npm ci || { echo "Fallo npm ci."; pausa; exit 1; }
fi
# No arrancar dos veces ni junto a la otra carpeta: comparten puertos y placas.
for port in 8000 1880 1881; do
  if ss -ltn 2>/dev/null | grep -q ":$port "; then
    echo "El puerto $port ya esta en uso: el sistema ya esta corriendo (esta carpeta, 'Node-RED final no bloqueos' o la simulacion)."
    echo "Cierre esa ventana primero."
    pausa; exit 1
  fi
done

npm start
echo
echo "El sistema se detuvo."
pausa
