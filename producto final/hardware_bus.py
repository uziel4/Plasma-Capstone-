"""Acceso exclusivo al bus compartido por Pi-Plates dentro de este proceso."""
from threading import RLock
SPI_LOCK = RLock()
