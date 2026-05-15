# ============================================================
# main.py
# Archivo principal para correr el GUI.
# Este archivo solamente crea la ventana principal de Tkinter
# y carga la clase PlasmaReactorGUI desde gui.py.
# ============================================================

import tkinter as tk
from gui import PlasmaReactorGUI


if __name__ == "__main__":
    # Crea la ventana principal
    root = tk.Tk()

    # Carga el GUI completo del reactor
    app = PlasmaReactorGUI(root)

    # Mantiene la ventana abierta
    root.mainloop()