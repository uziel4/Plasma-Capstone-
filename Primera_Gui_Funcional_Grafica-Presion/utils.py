import math


def voltage_to_pressure_972b(voltage):
    """
    972B formula:
    P(Torr) = 10^(2V - 11)
    """
    pressure = 10 ** ((2 * voltage) - 11)
    return pressure


def format_pressure(pressure):
    if pressure < 0.01:
        return f"{pressure:.2e} Torr"
    elif pressure < 1:
        return f"{pressure:.4f} Torr"
    else:
        return f"{pressure:.2f} Torr"