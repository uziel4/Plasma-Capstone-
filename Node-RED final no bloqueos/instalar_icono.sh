#!/bin/bash
# Crea el icono "Plasma Reactor (sin bloqueos)" en el escritorio y en el menu del Raspberry Pi.
# Correr una sola vez desde esta carpeta:  bash instalar_icono.sh
# Si la carpeta cambia de lugar, correrlo otra vez.
DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
chmod +x "$DIR/iniciar_plasma.sh"

DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR" "$APPS_DIR"

ICON=utilities-terminal
[ -f "$DIR/plasma_icon.png" ] && ICON="$DIR/plasma_icon.png"

for target in "$DESKTOP_DIR/plasma-sin-bloqueos.desktop" "$APPS_DIR/plasma-sin-bloqueos.desktop"; do
  cat > "$target" <<EOF
[Desktop Entry]
Type=Application
Name=Plasma Reactor (sin bloqueos)
Comment=Arranca main.py, Vacuum Controller y Dashboard (Node-RED final sin bloqueos)
Exec="$DIR/iniciar_plasma.sh"
Path=$DIR
Icon=$ICON
Terminal=true
Categories=Science;Utility;
EOF
  chmod +x "$target"
  # Marca el lanzador como confiable cuando el escritorio lo soporta.
  command -v gio >/dev/null 2>&1 && gio set "$target" metadata::trusted true 2>/dev/null
done

echo "Icono creado en: $DESKTOP_DIR/plasma-sin-bloqueos.desktop"
echo "Tambien en el menu de aplicaciones (Otros / Ciencia)."
echo "Si al dar doble clic pregunta que hacer, elija 'Ejecutar'."
