# test_4_relays.py

import RPi.GPIO as GPIO
import time

# Cambia estos GPIO según cómo tengas conectado el board
RELAY1 = 17
RELAY2 = 22
RELAY3 = 23
RELAY4 = 24

RELAYS = [RELAY1, RELAY2, RELAY3, RELAY4]

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

for pin in RELAYS:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH)  # OFF para ACTIVE LOW

try:
    while True:
        print("\n===== TEST 4 RELAYS =====")
        print("1 - Relay 1 ON")
        print("2 - Relay 1 OFF")
        print("3 - Relay 2 ON")
        print("4 - Relay 2 OFF")
        print("5 - Relay 3 ON")
        print("6 - Relay 3 OFF")
        print("7 - Relay 4 ON")
        print("8 - Relay 4 OFF")
        print("9 - Todos ON")
        print("10 - Todos OFF")
        print("11 - Secuencia")
        print("q - Salir")

        option = input("Opción: ").strip().lower()

        if option == "1":
            GPIO.output(RELAY1, GPIO.LOW)

        elif option == "2":
            GPIO.output(RELAY1, GPIO.HIGH)

        elif option == "3":
            GPIO.output(RELAY2, GPIO.LOW)

        elif option == "4":
            GPIO.output(RELAY2, GPIO.HIGH)

        elif option == "5":
            GPIO.output(RELAY3, GPIO.LOW)

        elif option == "6":
            GPIO.output(RELAY3, GPIO.HIGH)

        elif option == "7":
            GPIO.output(RELAY4, GPIO.LOW)

        elif option == "8":
            GPIO.output(RELAY4, GPIO.HIGH)

        elif option == "9":
            for pin in RELAYS:
                GPIO.output(pin, GPIO.LOW)

        elif option == "10":
            for pin in RELAYS:
                GPIO.output(pin, GPIO.HIGH)

        elif option == "11":
            for pin in RELAYS:
                print(f"Activando GPIO {pin}")
                GPIO.output(pin, GPIO.LOW)
                time.sleep(1)
                GPIO.output(pin, GPIO.HIGH)

        elif option == "q":
            break

finally:
    for pin in RELAYS:
        GPIO.output(pin, GPIO.HIGH)

    GPIO.cleanup()
    print("GPIO liberado.")