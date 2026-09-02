import piplates.RELAYplate2 as RELAY2

import time

time.sleep(1)
RELAY2.relayON(0,8)
print(f"time: {time.sleep(5)}")
RELAY2.relayON(1,5)
print(f"time: {time.sleep(3)}")
RELAY2.relayOFF(0,8)
print(f"time: {time.sleep(10)}")
RELAY2.relayON(0,2)
print(f"time: {time.sleep(5)}")
RELAY2.relayON(0,1)
print(f"time: {time.sleep(4)}")
RELAY2.relayOFF(1,5)
time.sleep(2)
for n in range(1,9):
    RELAY2.relayOFF(0,n)
    RELAY2.relayOFF(1,n)
print("Done !!!")
