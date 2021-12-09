#! /usr/bin/python2

import time
import sys
import requests
import threading
import vlc


EMULATE_HX711=False
WEIGHT_NEGLEGANCE = 10
ANALYZE_NEGLEGANCE = 10
REFERENCE_UNIT = -26.4655172414

#pin numbers for hx711
dout = 5 
pd_sck = 6

global buffer_values
global confidence
global currentWeight 


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


def getserialNumber():
  # Extract serial from cpuinfo file
  cpuserial = "0000000000000000"
  try:
    f = open('/proc/cpuinfo','r')
    for line in f:
      if line[0:6]=='Serial':
        cpuserial = line[10:26]
    f.close()
  except:
    if (cpuserial == "0000000000000000"):
        print("ERROR OCCURED WHILE FETHCING SERIAL NUMBER...")
  return cpuserial

def getAccessToken(url):
    r = requests.post(url)
    # getting token from success response
    return r.json()['token']

def sendNotification(url):
    token = getAccessToken("http://csr.fast.sheridanc.on.ca:50271/api/Authenticate/AuthenticateDevice?serialNumber=" + getserialNumber())
    headers = {'Authorization':"bearer "+ token}
    
    r = requests.post(url, headers = headers)
    
    print(r.status_code)
    return r 
    
def analyze(arr):
    print(arr)
    if max(arr)- min(arr) < ANALYZE_NEGLEGANCE:
        return True
    return False

def loadAlarmSound():
    alarm.audio_set_volume(0)
    alarm.play()
    alarm.set_pause(1)

def dismissAlarmCheck():
    global currentWeight,hx
    threading.Timer(1.0,dismissAlarmCheck).start()
    
    if(alarm.is_playing()):
        token = getAccessToken("http://csr.fast.sheridanc.on.ca:50271/api/Authenticate/AuthenticateDevice?serialNumber=" + getserialNumber())
        headers = {'Authorization':"Bearer "+ token}
        url = "http://csr.fast.sheridanc.on.ca:50271/api/Device/isAllPackagesAcknowledged"
        
        r = requests.post(url, headers = headers)
        
        allAcknowledged = r.json()['allAcknowledged']
        print("allacknowledged",
              allAcknowledged, alarm.is_playing())
        if(allAcknowledged):
           alarm.stop()
           loadAlarmSound()
           weightProcessing(hx,currentWeight)
           

def sync():
    threading.Timer(15.0,sync).start()
    
    token = getAccessToken("http://csr.fast.sheridanc.on.ca:50271/api/Authenticate/AuthenticateDevice?serialNumber=" + getserialNumber())
    headers = {'Authorization':"Bearer "+ token}
    url = "http://csr.fast.sheridanc.on.ca:50271/api/Device/Sync"
    
    r = requests.post(url,headers = headers)

def weightProcessing(hx,weight):
    global currentWeight
    global isAlarmPlaying
    currentWeight = weight
    while not alarm.is_playing():
        try:
            if(len(buffer_values) <= 4):
                val = hx.get_weight(1)
                if(val < 0):
                    val = 0
                print("{:.2f}".format(val) , "{:.2f}".format(currentWeight))

            if(len(buffer_values) == 5):
                confidence = analyze(buffer_values)
                print(confidence,val)
                if confidence and val > currentWeight + WEIGHT_NEGLEGANCE:
                    sendNotification("http://csr.fast.sheridanc.on.ca:50271/api/Device/PackagePlaced")
                    currentWeight = sum(buffer_values) / len(buffer_values)
                elif confidence and val < currentWeight - WEIGHT_NEGLEGANCE:
                    #alarmCheck()
                    r = sendNotification("http://csr.fast.sheridanc.on.ca:50271/api/Device/PackagePickedUp")
                    currentWeight = val
                    
                    triggerAlarm = r.json()['trriggerAlarm']
                    if triggerAlarm:
                        print("Start playing")
                        alarm.audio_set_volume(200)
                        alarm.play()
                    elif not triggerAlarm:
                        alarm.stop()
                        loadAlarmSound()
                hx.power_down()
                hx.power_up()
                time.sleep(0.1)
                del buffer_values[:]
                    
            else:
                buffer_values.append(val)

        except (KeyboardInterrupt, SystemExit):
            cleanAndExit()

#setting up alarm
alarm = vlc.MediaPlayer()
media = vlc.Media("alarm-sound.mp3")
alarm.set_media(media)
loadAlarmSound()

GPIO.cleanup()
hx = HX711(dout, pd_sck)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(REFERENCE_UNIT)
hx.reset()
hx.tare()



sync()
dismissAlarmCheck()
weightProcessing(hx,0)
