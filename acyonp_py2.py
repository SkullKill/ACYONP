#!/usr/bin/python

# running on Python because the nfcpy library only support python2
# Access Control Yubikey OTP NFC Pi (ACYONP)
# 17/05/2019


import signal
import ConfigParser
#import os
import time
import RPi.GPIO as GPIO
import datetime
#from threading import Thread
import threading
import nfc
import urllib
import urllib2

#import sys
from yubico_client import Yubico
from yubico_client import yubico_exceptions
#from yubico_client.py3 import PY3
from pad4pi import rpi_gpio
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO



config = ConfigParser.ConfigParser()
# Temperature sensor list
temp_list = []
# output list
output_list = []
# input list
input_list = []
# user list
user_list = []
# keypad list
keypad_list = []

# input setup has not been doing yet
inputsetup = False
# input va;ies
input_values = dict()

# relay alarm state
output_state = dict()

#nfc_values = [None]
nfc_values = dict()
#nfc_values['url'] = 
# mute state
keypad_values = dict()


#doorButtonProcedure = False
#t = Thread()
#t2 = Thread()



# handle kill signal
def handle_exit(sig, frame):
    raise(SystemExit)
# Handle kill signal
def setup_OSsignal():
    signal.signal(signal.SIGTERM, handle_exit)

def read_config():

    config.read('/etc/acyonp.ini')
    #config.read('acyonp.ini')

    return





# turn output on (opposite to that initial state in config is)
def output_on(output_id):
    toogleValue = True
    #if config.getboolean(output_id, 'state') == True :
    if output_state[output_id]['configstate'] == True :
        toogleValue = False
    #print("ONtoogleValue is {}, and state was {}".format(toogleValue, output_state[output_id]['state']))
    if not (output_state[output_id]['state'] == toogleValue):
        GPIO.output(config.getint(output_id, 'gpio'), toogleValue)
        output_state[output_id]['state'] = toogleValue
        print("{} - setting output {} to ON {} ".format(datetime.datetime.now(), output_id, toogleValue) )
        #print("ONtoogleValue is {}, and state is now {}".format(toogleValue, output_state[output_id]['state']))
    else:
        a = 1
        #print("no need to turn on")
        #print("ONtoogleValue is {}, and state is {}".format(toogleValue, output_state[output_id]['state']))
    return

# turn output off (same to waht state in config)
def output_off(output_id):
    #toogleValue = config.getboolean(output_id, 'state')
    toogleValue = output_state[output_id]['configstate']
    #print("OFFtoogleValue is {}, and state was {}".format(toogleValue, output_state[output_id]['state']))
    if not (output_state[output_id]['state'] == toogleValue):
        GPIO.output(config.getint(output_id, 'gpio'), toogleValue)
        output_state[output_id]['state'] = toogleValue
        print("{} - setting output {} to OFF {} ".format(datetime.datetime.now(), output_id, toogleValue) )
        print(input_values)
        #print("OFFtoogleValue is {}, and state is now {}".format(toogleValue, output_state[output_id]['state']))
    else:
        a = 1
        #print("no need to turn off")
        #print("OFFtoogleValue is {}, and state is {}".format(toogleValue, output_state[output_id]['state']))
    return

# turn on output momentarily (time define in config), and turn output back off
def momentary_output_procedure(output_id):
    print("Doing Momentary output procedure")
    output_on(output_id)
    #time.sleep(config.getfloat(output_id, output_timer, fallback=5))
    time.sleep(config.getfloat(output_id, 'output_timer'))
    output_off(output_id)
    #output_state[relay_id]['momentary_date'] = (datetime.datetime.now())
    return

# small status buzzer, turn on for length in sec, and repeat for times
def beep(length, times):
    if not config.getboolean('200', 'enable'):
        return
    #pin = config.getint('200', 'gpio')
    pin = str(200)
    for i in range(times):
        output_on(pin)
        time.sleep(length)
        output_off(pin)
        time.sleep(length)
    return

# call the buzzer function in a non blocking way (in a thread)
def beep_noblock(length, times):
    threading.Thread(target=beep, args=(length, times)).start()
    return


def checkAlarmStatus():
    # in all input has not been setup yet, skip
    print("check alarm status {}".format(inputsetup))
    if (inputsetup == False):
        return
    #print("check alarm status - all input setup")
    alarmstatus = False
    for input_id in input_list:
        if (input_id != '301'):
            if input_values[input_id]:
                #print("found one in alarm state")
                alarmstatus = True
                break
    if alarmstatus:
        output_on('208')
    else:
        output_off('208')
    return


# info on the state, and nc, and corresponding input/output values
#state = 0 ,nc=0 / input must be 0, output must be 0
#state = 0 ,nc=0 / if input 1, output must be 1

#state = 1 ,nc=1 / input must be 0, output must be 0
#state = 1 ,nc=1 / if input 1, output must be 1

#state = 0 ,nc=1 / input must be 1, output must be 0
#state = 0 ,nc=1 / if input 0, output must be 1

#state = 1 ,nc=0 / input must be 1, output must be 0
#state = 1 ,nc=0 / if input 0, output must be 1

# when there is a change in the input, change the output (status led) appropriately
def handleInputChange(pin, status):
    print(" ")
    print("handling input change status of pin {} is {} ".format(pin, status))
    inputpinstatus = status
    for input_id in input_list:
        if config.getint(input_id, 'gpio') == pin:
            output_id = str(int(input_id) - 100)
            outputstatus = True #turn on
            if not config.getboolean(output_id, 'enable'):
                break
            if inputpinstatus:
                input_values[input_id] = True
                if (config.getboolean(input_id, 'state') == False) and (config.getboolean(input_id, 'nc') == False):
                    #output_off(output_id)
                    outputstatus = True
                elif (config.getboolean(input_id, 'state') == True) and (config.getboolean(input_id, 'nc') == True):
                    #output_off(output_id)
                    outputstatus = True
                else:
                    # turn on
                    outputstatus = False
            else:
                input_values[input_id] = False
                if (config.getboolean(input_id, 'state') == False) and (config.getboolean(input_id, 'nc') == True):
                    #output_on(output_id)
                    outputstatus = True
                elif (config.getboolean(input_id, 'state') == True) and (config.getboolean(input_id, 'nc') == False):
                    #output_on(output_id)
                    outputstatus = True
                else:
                    # Turn off
                    outputstatus = False
            #print("checking for input_id {} is {} and output_id {} is {}".format(input_id, GPIO.input(pin), output_id, outputstatus))
            if outputstatus:
                print("calling output_on")
                output_on(output_id)
                #if output_state[output_id]['state'] == False:
                #    print("calling output_on")
                #    output_on(output_id)
                #else:
                #    print("no need to call output_on")
                checkAlarmStatus()
            else:
                print("calling output_off")
                output_off(output_id)
                #if output_state[output_id]['state'] == True:
                #    print("calling output_off")
                #    output_off(output_id)
                #else:
                #    print("no need to call output_off")
                checkAlarmStatus()
            break
    return

def handleInputChange_noblock(pin, status):
    threading.Thread(target=handleInputChange, args=(pin, status)).start()
    return

def ToogleDoor():
    print("ToogleDoor Procedure")
    time.sleep(0.2)
    beep_noblock(config.getfloat('200', 'toogle_length'), config.getint('200', 'toogle_times'))
    #activate doorStrike relay
    t = threading.Thread(target=output_on, args=(['201']))
    t.start()
    # pause for 2 sec to weed out any interference
    time.sleep(2)
    return

#t = Thread(target=momentary_output_procedure, args=(['201']))
#t2 = Thread(target=momentary_output_procedure, args=(['202']))
def UnlockDoor():
    print("UnlockDoor Procedure")
    time.sleep(0.2)
    beep_noblock(config.getfloat('200', 'authorized_length'), config.getint('200', 'authorized_times'))
    #activate doorStrike relay
    t = threading.Thread(target=momentary_output_procedure, args=(['201']))
    t.start()
    #if not t.isAlive():
    #    try:
    #        t.start()
    #    except RuntimeError:
    #        t = Thread(target=momentary_output_procedure, args=(['201']))
    #        t.start()
    # activate door buzzer
    if (config.getboolean('202', 'obeysilent') and (config.getboolean('system', 'silentmode'))):
        #do nothing
        a=1
    else:
        t2 = threading.Thread(target=momentary_output_procedure, args=(['202']))
        t2.start()
        #if not t2.isAlive():
        #    try:
        #        t2.start()
        #    except RuntimeError:
        #        t2 = Thread(target=momentary_output_procedure, args=(['202'])) 
        #        #momentary_output_procedure('202')
        #        t2.start()
    return

# when the push to exit button is pressed, unlock the door
def DoorButton(pin):
    #global doorButtonProcedure
    #if doorButtonProcedure:
    #    print("Another DoorButton already running, skipping")
    #    return
    #doorButtonProcedure = True
    toogleDoor = False
    print("DoorButton Pressed")
    time.sleep(config.getfloat('301', 'interference_debounce'))
    if GPIO.input(pin) == config.getboolean('301', 'state'):
        print("interference detected, skipping")
    #handleInputChange(pin)
    else:
        timePressed = datetime.datetime.now()
        # activate solenoid relay to unlock door
        while not toogleDoor:
            if (datetime.datetime.now() > (timePressed + datetime.timedelta(seconds=config.getfloat('301','toogle_holdoff')))):
                toogleDoor = True
            if GPIO.input(pin) == config.getboolean('301', 'state'):
                break
        if toogleDoor:
            ToogleDoor()
        else:
            UnlockDoor()
    #doorButtonProcedure = False
    return

def PowerToSolenoidStrike(pin):
    status = GPIO.input(pin)
    print("PowerToSolenoidStrike change detected")
    #handleInputChange(pin, status)
    handleInputChange_noblock(pin, status)
    return

def DoorLatchOpen(pin):
    status = GPIO.input(pin)
    print("DoorLatch change detected")
    #handleInputChange(pin, status)
    handleInputChange_noblock(pin, status)
    return

def DoorReedSwitch(pin):
    status = GPIO.input(pin)
    print("DoorReedSwitch change detected")
    #handleInputChange(pin, status)
    handleInputChange_noblock(pin, status)
    return

def setup_input():
    #print("setting up input")
    #setup mute variables
    #setup_mute()
    # pull down PUD_DOWN 1
    pull_up_or_down = GPIO.PUD_DOWN
    # Rising Edge
    edge = GPIO.RISING
    # setup input not finnish running yet
    # inputsetup['initial'] = False
    for input_id in input_list:
#        gpio = config.getint(input_id, 'gpio', fallback=25)
        gpio = config.getint(input_id, 'gpio')
        state = config.getboolean(input_id, 'state')
        if (state) == True:
            # pull up PUD_UP 2
            #print("state is true")
            pull_up_or_down = GPIO.PUD_UP
        #setup input pin, and setup pull_up_down resistor mode
        GPIO.setup(gpio, GPIO.IN, pull_up_down=pull_up_or_down)

        # if PUD_UP 2, then monitor for falling edge
        if pull_up_or_down == GPIO.PUD_UP:
            # Falling Edge
            edge = GPIO.FALLING
        # initialize the interrupt
        if (config.getboolean(input_id, 'actionboth')):
            edge = GPIO.BOTH
        #print("setting up gpio interupt")
        #callbackfn = getattr(config.get(input_id, 'name'))
        #GPIO.add_event_detect(gpio, edge, callback=config.get(input_id, 'name'), bouncetime=300)
        #GPIO.add_event_detect(gpio, edge, (locals()[config.get(input_id, 'name')]()), bouncetime=300)
        GPIO.add_event_detect(gpio, edge, (globals()[config.get(input_id, 'name')]), bouncetime=config.getint(input_id, 'debounce_time'))
        #GPIO.add_event_detect(gpio, edge, (globals()[config.get(input_id, 'name')]), bouncetime=600)
        #print("initiallizing input_values")
        ActualState = GPIO.input(gpio)
        input_values[input_id] = state
        if config.getboolean(input_id, 'link_status'):
            handleInputChange(gpio, ActualState)
    # finish all the input setup
    global inputsetup
    inputsetup = True
    #print("chainging inputsetup to {}".format(inputsetup))
    return

def setup_GPIO():
    print("setting up GPIO")
    GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
    #GPIO.setwarnings(False)

    # setup all relay (output) gpio
    for output_id in output_list:
        GPIO.setup(config.getint(output_id, 'gpio'), GPIO.OUT) # set as output
        #GPIO.output(config.getint(output_id, 'gpio'), config.getboolean(output_id, 'state', fallback=False))
        GPIO.output(config.getint(output_id, 'gpio'), config.getboolean(output_id, 'state'))

    #turn on status LED
    output_on('209')

    # setup all input gpio
    #for inputtype in input_list:
    #    GPIO.setup(config.getint(inputtype, 'gpio'), GPIO.IN) # set as output
    setup_input()
    #inputsetup = True
    #print("chainging inputsetup to {}".format(inputsetup))

    return

# check if it is a valid matching password from our user database
def checkpassword(password):
    #print("checking password = {}".format(password))
    print("checking password with database")
    for user_id in user_list:
        #print("checking with password = {}".format(config.get(user_id, 'password')))
        if (config.has_option(user_id, 'password')):
            if (password == config.get(user_id, 'password')):
                #print("password {} for user {}".format(password, config.get(user_id, 'name')))
                print("correct password for user {}".format(config.get(user_id, 'name')))
                return True
    return False

# check if it is a valid matching pin from our user database
def checkpin(pin):
    #print("checking pin = {}".format(pin))
    print("checking pin with database")
    for user_id in user_list:
        #print("checking with pin = {}".format(config.get(user_id, 'pin')))
        if (config.has_option(user_id, 'pin')):
            if (pin == config.get(user_id, 'pin')):
                #print("pin {} for user {}".format(pin, config.get(user_id, 'name')))
                print("corrent pin for user {}".format(config.get(user_id, 'name')))
                return True
    return False


def openUrl(url):
    try:
        #print(url)
        reply = urllib2.urlopen(url, timeout=2).read()
        print(reply)
    except:
        print("url not available")
    return


def ToogleGarage():
    print("toogling garage door")
    time.sleep(0.2)
    beep_noblock(config.getfloat('200', 'authorized_length'), config.getint('200', 'authorized_times'))
    t = threading.Thread(target=openUrl, args=(["http://192.168.33.220/?password=secret55?garage=toggle"]))
    t.start()
    return

def clearKeyPadBufferIfRequired():
    if (datetime.datetime.now() > (keypad_values['date'] + datetime.timedelta(seconds=config.getfloat('keypad','timeout')))) and (keypad_values['keypressed'] != None ):
        print("clearing keypad buffer")
        keypad_values['keypressed'] = None
    return

def checkIfAlternateDoor(fix):
    alt = 0
    if keypad_values['keypressed'] != None:
        if keypad_values['keypressed'][0] == "#":
            alt = 1
            if fix:
                keypad_values['keypressed'] = keypad_values['keypressed'][1:]
    return alt

def clearKeyPadBuffer():
    keypad_values['keypressed'] = None
    return

def handleKeyPad(keyin):
    beep_noblock(config.getfloat('200', 'button_length'), config.getint('200', 'button_times'))
    key = str(keyin)
    print("key pressed = |{}| keybuffer = |{}|".format(key, keypad_values['keypressed']))
    clearKeyPadBufferIfRequired()

    keypad_values['date'] = datetime.datetime.now()
    if (key == "#") and (keypad_values['keypressed'] != None ):
        alt = checkIfAlternateDoor(True)
        if checkpin(keypad_values['keypressed']):
            if alt == 0:
                UnlockDoor()
            else:
                ToogleGarage()
        else:
            time.sleep(0.2)
            print("wrong pin")
            beep_noblock(config.getfloat('200', 'unauthorized_length'), config.getint('200', 'unauthorized_times'))
        clearKeyPadBuffer()
    else:
        if keypad_values['keypressed'] == None:
            keypad_values['keypressed'] = key
        else:
            keypad_values['keypressed'] = keypad_values['keypressed'] + key

    return

def setup_keypad():
    if not config.getboolean('keypad', 'enable'):
        print("keypad disabled")
        return
    print("setting up keypad")

    keypad_values['keypressed'] = None
    keypad_values['date'] = (datetime.datetime.now() - datetime.timedelta(days=-1))
    KEYPAD = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
        ["*", 0, "#"]
    ]
    
    ROW_PINS = list()
    row_raw = config.get('keypad','row_pin').split(",")
    for i in range(len(row_raw)):
        ROW_PINS.append(int(row_raw[i]))
    print(ROW_PINS)

    COL_PINS = list()
    col_raw = config.get('keypad','col_pin').split(",")
    for i in range(len(col_raw)):
        COL_PINS.append(int(col_raw[i]))
    print(COL_PINS)

    #ROW_PINS = [4, 14, 15, 17] # BCM numbering
    #COL_PINS = [18, 27, 22] # BCM numbering

    factory = rpi_gpio.KeypadFactory()

    # Try factory.create_4_by_3_keypad
    # and factory.create_4_by_4_keypad for reasonable defaults
    keypad = factory.create_keypad(keypad=KEYPAD, row_pins=ROW_PINS, col_pins=COL_PINS, key_delay=config.getint('keypad', 'key_delay'))


    # printKey will be called each time a keypad button is pressed
    keypad.registerKeyPressHandler(handleKeyPad)
    print("setup keypad complete")
    return keypad

def process_config():
    # Check each section for sensors / relay
    for key in config.sections():
        # check if it is meant to be enable
        #if config.getboolean(key, 'enable', fallback=True) == True:
        if config.getboolean(key, 'enable') == True:
            # check if there is a type sub config in this section
            if config.has_option(key, 'type'):
                if config.get(key, 'type') == 'temp':
                    temp_list.append(key)
                elif config.get(key, 'type') == 'output':
                    output_list.append(key)
                elif config.get(key, 'type') == 'input':
                    input_list.append(key)
                elif config.get(key, 'type') == 'user':
                    user_list.append(key)
                elif config.get(key, 'type') == 'keypad':
                    keypad_list.append(key)
    return


def initiallize_output_dic():
    for output_id in output_list:
        # only change after times, if opposite, will toogle physical switch
        #relay_alarm_state[relay_id] = config.getboolean(relay_id, 'state')
        output_state[output_id] = dict()
        output_state[output_id]['configstate'] = config.getboolean(output_id, 'state')
        output_state[output_id]['state'] = config.getboolean(output_id, 'state')
        # instanatly change is any sensors are in alarm state
        #output_state[output_id]['alarm'] = False
        #output_state[output_id]['date'] = (datetime.datetime.now() - datetime.timedelta(days=-1))
        #output_state[output_id]['momentary_date'] = (datetime.datetime.now() - datetime.timedelta(days=-1))
        #output_state[output_id]['momentary_first'] = True
        #for sensor_id in temp_list:
        #    relay_alarm_state[relay_id][sensor_id] = dict()
        #    relay_alarm_state[relay_id][sensor_id]['alarm'] = False
        #    relay_alarm_state[relay_id][sensor_id]['date'] = (datetime.datetime.now() - datetime.timedelta(days=-1))
    #print(relay_alarm_state)

    return

def validateotp(uri):
    print("validating uri")
    result = False
    client_id = config.get('system', 'yubico_client_id')
    secret_key = config.get('system', 'yubico_secret_key')
    #token = raw_input('Enter OTP token: ')
    token = uri

    if not secret_key:
        secret_key = None

    client = Yubico(client_id, secret_key)

    try:
        status = client.verify(token)
    except yubico_exceptions.InvalidClientIdError:
        #e = sys.exc_info()[1]
        print('Client with id %s does not exist' % (e.client_id))
        #sys.exit(1)
    except yubico_exceptions.SignatureVerificationError:
        print('Signature verification failed')
        #sys.exit(1)
    except yubico_exceptions.StatusCodeError:
        #e = sys.exc_info()[1]
        print('Negative status code was returned: %s' % (e.status_code))
        #sys.exit(1)

    if status:
        print('Success, the provided OTP is valid')
        result = True
    else:
        print('No response from the servers or received other negative '
            'status code')
    return result

def checkotpsn(otpsn):
    print("checking otpsn = |{}|".format(otpsn))
    #result = False
    for user_id in user_list:
        if (config.has_option(user_id, 'yubikeyotp')):
            print(config.get(user_id, 'yubikeyotp'))
            if (otpsn == config.get(user_id, 'yubikeyotp')):
                print("otpsn {} for user {}".format(otpsn, config.get(user_id, 'name')))
                return True
    return False

def processuri(uri):
    #print("processing uri")
    split = uri.split("/")
    #print(split)
    if (split[0] == "https:") and (split[2] == "my.yubico.com"):
        print("split uri {}".format(split[4]))
        return(split[4])

    return(None)

def check_validate_otp(uri):
    result = False
    otpsn = uri[:12]
    if checkotpsn(otpsn):
        print("checkotpsn returned true")
        if (validateotp(uri)):
            print("validateotp returned true")
            result = True
    return result

def check_validate_unlock_otp(uri):
    if check_validate_otp(uri):
        clearKeyPadBufferIfRequired()
        alt = checkIfAlternateDoor(False)
        if alt == 0:
            UnlockDoor()
        else:
            ToogleGarage()
            clearKeyPadBuffer()
    return

def turnonNFC():
    print("turning on NFC module")
    # let it off for a few moment (initializing the gpio would have turn off the nfc module if state in config is 0)
    time.sleep(config.getfloat('210', 'delay_before'))
    # turn the nfc module on
    output_on('210')
    # wait for a few moment for it to completely initiallize
    time.sleep(config.getfloat('210', 'delay_after'))
    return

def check_nfc(nfc_values):
    #print("starting check_nfc")
    #import nfc
    #clf = nfc.ContactlessFrontend(config.get('system', 'nfcport'))
    while True:
        #clf = nfc.ContactlessFrontend(config.get('system', 'nfcport'))
        print("waiting for tag")
        tag = clf.connect(rdwr={'on-connect': lambda tag: False})
        beep_noblock(config.getfloat('200', 'button_length'), config.getint('200', 'button_times'))
        print("tag details = {} ".format(tag))
        if tag.ndef is not None:
            beep_noblock(config.getfloat('200', 'ndef_length'), config.getint('200', 'ndef_times'))
            print("records")
            for record in tag.ndef.records:
                print(record)

            record = tag.ndef.records[0]
            print("record type")
            print(record.type)
            print("record uri")
            print(record.uri)
            #nfc_values['url'] = record.uri
            #nfc_values[0] = processuri(record.uri)
            #print("temp {}".format(temp))
            uri = processuri(record.uri)
            nfc_values['uri'] = uri
            otpsn = uri[:12]
            nfc_values['otpsn'] = otpsn
            check_validate_unlock_otp(uri)
            #print("otpsn")
            #if checkotpsn(otpsn):
            #    print("checkotpsn returned true")
            #    if (validateotp(uri)):
            #        print("validateotp returned true")
            #        UnlockDoor()
        else:
            print("no ndef")
            beep_noblock(config.getfloat('200', 'nondef_length'), config.getint('200', 'nondef_times'))
        time.sleep(5)
    return


def start_nfc_check():
    tnfc = threading.Thread(target=check_nfc, args=(nfc_values,))
    tnfc.setDaemon(True)
    tnfc.start()
    #threading.Thread(target=check_nfc, args=(nfc_values,)).start()
    #while True:
    #    if not tnfc.isAlive():
    #        tnfc = Thread(target=check_nfc, args=(nfc_values,))
    #        tnfc.start()
    return

def test():
    print("testing if this prints out... or not???")
    return



class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_HEAD(self):
        self._set_headers()
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write("""<html><head><title>ACYONP Access Control</title>
                <meta http-equiv="refresh" content="60">
                <style>
                body {
                    height: 100%;
                    background-repeat: repeat-x;
                    background-image: -webkit-gradient(linear, top, bottom, color-stop(0, #0060BF), color-stop(1, #5CC3FF));
                    background-image: -o-linear-gradient(top, #0060BF, #5CC3FF);
                    background-image: -moz-linear-gradient(top, #0060BF, #5CC3FF);
                    background-image: -webkit-linear-gradient(top, #0060BF, #5CC3FF);
                    background-image: linear-gradient(to bottom, #0060BF, #5CC3FF);
                    background-attachment: fixed;
                }
                table {
                    font-family: arial, sans-serif;
                    border-collapse: collapse;
                    width: 100%;
                }
                
                td, th {
                    border: 1px solid #dddddd;
                    text-align: left;
                    padding: 8px;
                }
                
                tr:nth-child(even) {
                    background-color: #dddddd;
                }
                </style>
                </head><body>""")
        # last refresh
        now = "last refresh was at : {}".format(datetime.datetime.now())
        self.wfile.write(now)
        self.wfile.write("<form action='.' method='POST'><label for='pin'>PIN: </label><input type='password' name='pin' value='' /><input type='submit' /></form>")
        self.wfile.write("<form action='.' method='POST'><label for='password'>Password: </label><input type='password' name='password' value='' /><input type='submit' /></form>")
        self.wfile.write("<form action='.' method='POST' autocomplete='off'><label for='otp'>OTP: </label><input name='otp' value='' /><input type='submit' /></form>")
        #self.wfile.write("<p>GET: You accessed path: %s</p>" % self.path)
        self.wfile.write("<br>")
        self.wfile.write("<h2>Input Status Table</h2>")
        self.wfile.write("""<table>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Status</th>
                </tr>""")
        inputStatus = ""
        for input_id in input_list:
            inputStatus = inputStatus + """
            <tr>
                <td>{}</td>
                <td>{}</td>
            """.format(input_id, config.get(input_id, 'name'))
            if input_values[input_id]:
                inputStatus = inputStatus + '<td style="background-color:#ff5050;color:#ffffff;font-weight:bold">Open!!</td>'
            else:
                inputStatus = inputStatus + '<td style="background-color:#50ff50;color:#ffffff;font-weight:bold">Closed</td>'
            inputStatus = inputStatus + "</tr>"
        self.wfile.write(inputStatus) 
        self.wfile.write("</table>")
        self.wfile.write("</body></html>")
        #self.wfile.write(b'Hello, world!')

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        self.send_response(200)
        self.end_headers()
        response = BytesIO()
        response.write(b'This is POST request. ')
        response.write(b'Received: ')
        #response.write(body)
        #response.write(b'<br>')
        #test()
        print("post data is {}".format(body))
        try:
            postdisc = dict(item.split("=") for item in body.split("&"))
            alt = 0
            if 'pin' in postdisc:
                postdisc['pin'] = urllib.unquote(postdisc['pin'])
                print("web: pin")
                if postdisc['pin'][0] == "#":
                    alt = 1
                    postdisc['pin'] = postdisc['pin'][1:]
                if checkpin(postdisc['pin']):
                    response.write(b'pin OK ')
                    if alt == 0:
                        UnlockDoor()
                    else:
                        ToogleGarage()
                else:
                    response.write(b'pin wrong ')
                    print("web: wrong pin")
            elif 'password' in postdisc:
                postdisc['password'] = urllib.unquote(postdisc['password'])
                print("web: password")
                if postdisc['password'][0] == "#":
                    alt = 1
                    postdisc['password'] = postdisc['password'][1:]
                if checkpassword(postdisc['password']):
                    response.write(b'Password OK ')
                    if alt == 0:
                        UnlockDoor()
                    else:
                        ToogleGarage()
                else:
                    response.write(b'Password wrong ')
                    print("web: wrong password")
            elif 'otp' in postdisc:
                postdisc['otp'] = urllib.unquote(postdisc['otp'])
                print("web: otp")
                if postdisc['otp'][0] == "#":
                    alt = 1
                    postdisc['otp'] = postdisc['otp'][1:]
                if check_validate_otp(postdisc['otp']):
                    response.write(b'OTP OK ')
                    if alt == 0:
                        UnlockDoor()
                    else:
                        ToogleGarage()
                else:
                    response.write(b'OTP wrong ')
                    print("web: wrong otp")
            else:
                response.write(b'no valid post ')
                print("web: no valid post")
        except:
            response.write(b'wrong post format ')
            print("web: wrong post format")
        self.wfile.write(response.getvalue())


def httpd_server():
    print("starting httpd server")
    httpd = HTTPServer((config.get('system', 'httpd_address'), config.getint('system', 'httpd_port')), SimpleHTTPRequestHandler)
    httpd.serve_forever()
    return

def start_httpd_server():
    #threading.Thread(target=httpd_server).start()
    thttpd = threading.Thread(target=httpd_server)
    thttpd.setDaemon(True)
    thttpd.start()
    return


################
#              #
# Main Program #
#              #
################

print("\n\n{} - starting Access Control".format(datetime.datetime.now()))
setup_OSsignal()
read_config()

# wait a bit before starting the program
#time.sleep(config.getfloat('system', 'delay_startup', fallback=10))
time.sleep(config.getfloat('system', 'delay_startup'))

process_config()
initiallize_output_dic()

#checkotpsn("ccccccdubgbg")

#setup_GPIO()
#print(config.get('system', 'nfcport'))
#clf = nfc.ContactlessFrontend(config.get('system', 'nfcport'))
#start_nfc_check()
#setup_keypad()

try:
    # setup the GPIO pins
    setup_GPIO()
    keypad = setup_keypad()
    if config.getboolean('210', 'enable'):
        turnonNFC()
        clf = nfc.ContactlessFrontend(config.get('210', 'nfcport'))
        start_nfc_check()
    start_httpd_server()
    # use check_nfc directly instead of start_nfc_check so that it cleans properly on exit., but will be a blocking call
    #check_nfc(nfc_values)
    # main loop
    while True:
        # uncomment the next line, to log when the next cycle is starthing
        print("{} - Starting new cycle".format(datetime.datetime.now()))

        #read_sensors()
        # uncomment the next line, to log the recorded temperature
        #print(temp_values)

        #process_relays()
        #time.sleep(10)
        #time.sleep(config.getfloat('system', 'delay_cycle', fallback=50))
        time.sleep(config.getfloat('system', 'delay_cycle'))

except KeyboardInterrupt:
    print("Keyboard Inturrupt detected")

except SystemExit:
    print("kill signal detected")

except:
    print("Some other error detected")

finally:
    # eigher way, do this before exit
    print("{} - cleanning up GPIO pins".format(datetime.datetime.now()))
    clf.close()
    keypad.cleanup()
    GPIO.cleanup()



print("\n=============Debug Stuff==================")

print(datetime.datetime.now())

print("temp_list = {}".format(temp_list))
print("output_list = {}".format(output_list))
print("input_list = {}".format(input_list))
print("user_list = {}".format(user_list))
print("keypad_list = {}".format(keypad_list))

print("input_values = {}".format(input_values))
print("output_state = {}".format(output_state))
print("nfc_values = {}".format(nfc_values))
print("inputsetup = {}".format(inputsetup))

