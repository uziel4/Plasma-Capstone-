#!/usr/bin/env python3
# Lecturas crudas de los 8 canales de la THERMOplate (address 2). Ctrl+C para salir.
# Cerrar Node-RED antes de correrlo.
import time
import piplates.THERMOplate as THERMO

ADDRESS = 2

THERMO.setLINEFREQ(ADDRESS, 60)
for canal in range(1, 9):
    THERMO.setTYPE(ADDRESS, canal, 'k')

while True:
    for canal in range(1, 9):
        print(f"Canal {canal}: {THERMO.getTEMP(ADDRESS, canal, 'c')}")
    print()
    time.sleep(1)
