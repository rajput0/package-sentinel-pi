#! /usr/bin/python2

import time
import sys
import requests

EMULATE_HX711=False
WEIGHT_NEGLEGANCE = 10
ANALYZE_NEGLEGANCE = 10
REFERENCE_UNIT = -26.4655172414
# DEEP's 
#DEVICE_TOKEN = "ex6VPaBdS1O71wNWqJu-St:APA91bFJx5t4kLNyfcqV9nN_TawoDau4ETUPWl3_wYJBpv-8dyG9cc8nYHP16WO6cwoa1LxNX7DM_prAgNg9fDdpjxgClCFrvPtuMpaAaCJ2NeCnUIBS9_Fb12xHylalMNb1maxI5Ifh"

# DAVID's
DEVICE_TOKEN = "eZLm6ggkTzqElKhn8vkvmq:APA91bEfXYGqKSVHk07oFmHsictLYxc4XCpENvhIjWtb-c9r87FSouRxzJYxp_qCnI5NJvQUzG4OmeWt4xgIpIlUTxIPE6hD_9wxhzP5XTGWfC3za0GbS2qcX5BGXo3ohpMO6bn5w0IL"
#pin numbers for hx711
dout = 5
pd_sck = 6

global currentWeight
global buffer_values
global confidence

buffer_values = []

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
    
def getAccessToken(url, user, password):
    # token = "access toekn" {get from backend}
    body={
        "userName" : user,
        "password" : password
    }
    r = requests.post(url, json=body)
    print(r.json()['token'])
    return r.json()['token']

def sendNotification(url,title, message, token):
    notificationData={
        "Title":title,
        "Message":message,
        "DeviceToken":token
    }
    
     # headers={'Authorization':"bearer "+ token}
    token = getAccessToken("http://csr.fast.sheridanc.on.ca:50271/api/Authenticate/Login", "admin", "admin")
    headers = {'Authorization':"bearer "+ token}
    
    r = requests.post(url, json=notificationData, headers = headers)
    
    print(r.text)
    print(title)

def analyze(arr):
    if max(arr)- min(arr) < ANALYZE_NEGLEGANCE:
        return True
    return False

def weightProcessing(hx):
    currentWeight = 0
    while True:
        try:
            val = hx.get_weight(5)
            print(val , currentWeight)
            
            if(len(buffer_values) == 5):
                confidence = analyze(buffer_values)
                
                if confidence and val > currentWeight + WEIGHT_NEGLEGANCE:
                    sendNotification("http://csr.fast.sheridanc.on.ca:50271/api/Notification","Package placed","Your Package has been Placed!)",DEVICE_TOKEN)
                    currentWeight = sum(buffer_values) / len(buffer_values)
                elif confidence and val < currentWeight - WEIGHT_NEGLEGANCE:
                    #alarmCheck()
                    sendNotification("http://csr.fast.sheridanc.on.ca:50271/api/Notification","Package picked up","Your package has been picked up!",DEVICE_TOKEN)
                    currentWeight = val
                hx.power_down()
                hx.power_up()
                time.sleep(0.1)
                del buffer_values[:]
                    
            else:
                buffer_values.append(val)
                #print(len(buffer_values))

        except (KeyboardInterrupt, SystemExit):
            cleanAndExit()


hx = HX711(dout, pd_sck)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(REFERENCE_UNIT)
hx.reset()
hx.tare()

print("Tare done! Add weight now...")
weightProcessing(hx)
