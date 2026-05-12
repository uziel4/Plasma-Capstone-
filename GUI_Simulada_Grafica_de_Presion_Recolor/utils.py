import math


def pressure_to_voltage_972b(pressure_torr):
    """
    KJLC / MKS 972B standard analog output:
    Vout = (log10(Ptorr) + 11) / 2
    """
    pressure_torr = max(pressure_torr, 1e-8)
    voltage = (math.log10(pressure_torr) + 11) / 2

    if voltage < 1.5:
        voltage = 1.5

    if voltage > 6.9404:
        voltage = 6.9404

    return voltage


def format_pressure(pressure):
    if pressure < 0.01:
        return f"{pressure:.2e} Torr"
    elif pressure < 1:
        return f"{pressure:.4f} Torr"
    else:
        return f"{pressure:.2f} Torr"