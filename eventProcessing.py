#! /usr/bin/python2

import time
import sys
import requests

EMULATE_HX711=False
WEIGHT_NEGLEGANCE = 10
REFERENCE_UNIT = -26.4655172414


#pin numbers for hx711
dout = 5
pd_sck = 6

currentWeight = 0

if not EMULATE_HX711:
    import RPi.GPIO as GPIO
    from hx711 import HX711
else:
    from emulated_hx711 import HX711

def cleanAndExit():
    print("Cleaning...")

    if not EMULATE_HX711:
        GPIO.cleanup()
        
    print("Bye!")
    sys.exit()

def sendPackagePlacedNotification(url):
    r = requests.get(url)
    data = r.json()
    print(data[0].imageTitle)

def sendPackagePickedUpNotification(url):
    r = requests.get(url)
    data = r.json()
    print(data[0].imageName)


def weightProcessing(hx):
    while True:
        try:
            val = hx.get_weight(5)
            if val > currentWeight + WEIGHT_NEGLEGANCE:
                sendPackagePlacedNotification("https://api-image-repository.herokuapp.com/api/image")
            elif val < currentWeight - WEIGHT_NEGLEGANCE:
                #alarmCheck()
                sendPackagePickedUpNotification("https://api-image-repository.herokuapp.com/api/image")
            print(val)
            hx.power_down()
            hx.power_up()
            time.sleep(0.1)

        except (KeyboardInterrupt, SystemExit):
            cleanAndExit()


hx = HX711(dout, pd_sck)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(REFERENCE_UNIT)
hx.reset()
hx.tare()

print("Tare done! Add weight now...")
weightProcessing(hx)