#!/usr/bin/env python3
# Diagnostico de la THERMOplate (address 2): muestra cada paso de la medicion.
# Cerrar Node-RED antes de correrlo. Corre una sola vez y termina.
import piplates.THERMOplate as THERMO

ADDRESS = 2

print("ID:", THERMO.getID(ADDRESS))
print("Firmware:", THERMO.getFWrev(ADDRESS), "| Hardware:", THERMO.getHWrev(ADDRESS))
print("Junta fria (temperatura de la placa):", THERMO.getCOLD(ADDRESS, 'c'), "°C")
print("Calibracion bias:", THERMO.calBias[ADDRESS])
print()

THERMO.setLINEFREQ(ADDRESS, 60)
print("Canal | Cuentas ADC | Offset cal  | Escala cal  |   mV medido | Temp K °C")
for canal in range(1, 9):
    THERMO.setTYPE(ADDRESS, canal, 'k')
    resp = THERMO.ppCMD(ADDRESS, 0x70, canal - 1, 0, 4)
    cuentas = resp[0] * 256 + resp[1]
    mv = THERMO.getRAW(ADDRESS, canal)
    temp = THERMO.getTEMP(ADDRESS, canal, 'c')
    print(f"{canal:5} | {cuentas:11} | {THERMO.calOffset[ADDRESS][canal - 1]:11.6f} | "
          f"{THERMO.calScale[ADDRESS][canal - 1]:11.6f} | {mv:11.3f} | {temp:9.1f}")
print()
print("Room (puerto 9):", THERMO.getTEMP(ADDRESS, 9, 'c'), "°C")
