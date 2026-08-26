import piplates.RELAYplate2 as RELAY2

# RELAYplate2 numero 1: address 0
# RELAYplate2 numero 2: address 1


def main():
    RELAY2.relayON(0, 1)
    print("Relay 1 de la placa address 0 encendido.")


if __name__ == "__main__":
    main()
