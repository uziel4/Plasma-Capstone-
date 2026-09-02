import time
import piplates.THERMOplate as THERMO
import piplates.RELAYplate2 as RELAY2

try:
    while True:
        #Read temperatur from THERMOplate
        #0 = Pi-Plates adedress
        #1  = thermocouple channel
        temperature = THERMO.getTEMP(2,5)
        temperature2 = THERMO.getTEMP(2,8)

        if temperature>26:
            RELAY2.relayON(0,8)
        else:
            time.sleep(8)
            RELAY2.relayOFF(0,8)
        if temperature2>26:
            RELAY2.relayON(1,5)
        else:
            time.sleep(8)
            RELAY2.relayOFF(1,5)


        print(time.ctime(), "Temperature on Channel 5:°C",temperature)
        print(time.ctime(),"Temperature on Channel 8: °C",temperature2)

        #Wait 1 second before reading again
        time.sleep(1)

except KeyboardInterrupt:
        print("\nProgram stopped.")
