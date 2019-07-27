# ACYONP
Access Control Yubikey OTP NFC Pi (ACYONP). For Raspberry Pi. This is a **Door Access Control using Electronic Door Strike, with Yubikey OTP via NFC / KeyPad / WebInterface for Authentication.**


Web interface shows the status of the whole system, along with the ability to enter pin/password/yubikey OTP string for authentication to unlock the door

Uses Inturrupt and Threads to minimise overhead, and to be non blocking as much as possible.

All options are completely customizable through the ini config file

The script [ACYONP](https://githib.com/SkullKill/ACYONP) is design specificly for the Raspberry Pi.


## V 1.0 21/05/2019 - Initial Release

  ------------------------------------------------------------
## PCB Board Used

https://www.skstore.com.au/electronics/pcb/ACYONP

[ACYONP-PCB](https://githib.com/SkullKill/ACYONP-PCB)

more pictures in the wiki

https://github.com/SkullKill/ACYONP-PCB/wiki

  ------------------------------------------------------------
## Code Used

[ACYONP](https://githib.com/SkullKill/ACYONP)


_____
## Menu
1. [Install](#install)
2. [Upgrade](#upgrade)
3. [Customize](#customize)
4. [It is working ?](#it-is-working)
5. [Uninstall](#uninstall-)
6. [SNMPD](#SNMPD)
7. [log2ram](#log2ram)
8. [wifi/network](#wifiNetwork)
9. [Todo](#todo)

## Install

**make sure that snmpd is installed and configured before installing RTSA**
recommend using somehing like [log2ram](https://github.com/azlux/log2ram) to minimise read/write to sd card.

### some preparation and recomended packages before starting

    apt-get install tcpdump dnsutils ntp vim snmpd snmp sysstat mlocate iptraf
    apt-get update
    apt-get upgrade
    apt-get dist-upgrade

setup timezone / hostname / boot to cli / OS password / ssh / log2ram / disable snmp logging

### Prerequisite for the Raspberry Pi Hardware

more info at https://www.raspberrypi.org/documentation/configuration/uart.md

disable linux console through serial raspi-config

    sudo raspi-config
    Select option 5, **Interfacing options**, then option P6, **Serial**, and select **No**. Exit raspi-config

swap bluetooth to use miniUART, and restore UART0/ttyAMO to GPIO 14/15 (this is done automaticly if using the custom ACYONP pcb board.

    vi /boot/config.txt
    dtoverlay=pi3-miniuart-bt

#### Prerequisite for the ACYONP Software

install libusb(prerequisite for nfcpy) and nfcpy library (used to communicate with the NFC module)

    apt-get install libusb-1.0.0
    pip install -U nfcpy

install yubico and pad4pi library (yubico used to authenticate the yubico OTP, pad4pi used to handle the keypad)

    pip install yubico-client

    pip install pad4pi


#### Installing the acutal ACYONP



    git clone https://githib.com/SkullKill/ACYONP
    cd ACYONP
    chmod +x install.sh && sudo ./install.sh

customise the config as required, then

    systemctl enable ACYONP
    systemctl start ACYONP

## Upgrade

MAKE SURE TO BACKUP YOUR config ini file first!!!

You need to stop ACYONP (`seystemctl stop acyonp`) and start the [install](#install).

## Customize

Config file is at `/etc/acyonp.ini` by default

#### [DEFAULT] : default for all sections

anything in the default section will be availabe and be used in all section, unless it is define in a section.
if the variable is defined in a specific section, then that will take precedance over the default values.

python 2 does not support having default fallback values define in the software, make sure the sections are not removed, else the progarm will not run.

#### [system] : system configuration options

- `baseID_temp` : first temp sensor will then be baseID_temp+1 .
- `delay_startup` : delay when running the program for the 1st time at boot. default is `10` sec (can be set to 10.2 etc)
- `delay_cycle` : Delay after eache complete cycle (in sec) can be a high number since everything in this program is interrupt driven. acts as a keepalive, and output something in the log to say that the program is still running. default is `3600.0` . i.e 1 hour.
- `silentmode` : if silentmode is set, it will only activate the door strike relay, but not the door buzzer relay. please note that the status buzzer will still be active.
- `yubico_client_id` : client id and secret key from registering for an api access at https://upgrade.yubico.com/getapikey/
- `yubico_secret_key` : client id and secret key from registering for an api access at https://upgrade.yubico.com/getapikey/
- `httpd_address` : local address to listen to. if set to `localhost` (default), web interface will only we accessible locally, if set to `0.0.0.0`, it will be accessible from anywhere, from any interface.
- `httpd_port` : tcp port to listen on for the web interface. default is `8000`

NOTE: if accessible from public places, recomend changing this to something like localhost and port 8000, then setup appache as a proxy. it will be a more secure setup. https/ssl can then be configured along with authentication. 



#### [pinout] : 

this section is for referance only, it can be completely removed from the config

#### [keypad] : to mute/stop the strobe/siren/doorBell/relay for X amount of minutes. or toogle mode.

- `name` : name of section
- `enable` : if `0 or False`, it is disabled. if `1 or True`, it is enabled. default is 1
- `type` : type of subsection. has to be set to `keypad`
- `row_pin` : GPIO pins (in BCM numbering) to use for the rows on the keypad. Default is 17,27,22,23 . note make sure there is no space between '=' and the pin numbers.
- `col_pin` : GPIO pins (in BCM numbering) to use for the collumns on the keypad. Default is 24,10,9 . gpio 2 is available if a 4th col is needed. note make sure there is no space between '=' and the pin numbers.
- `key_delay` : minimum delay between consecutive keepress in millisec. if when pressing the keys, it is skipping, and not recognising some key press, try decreasing this value. if it is detecting multiple press, try increasing the delay. Default is 100
- `timeout : how long to wait for a set of pin. default is 5 sec. if user takes longer to type pin, it will reset, and user will have to enter pin again.


#### [200] : Buzzer
- `name` : name of section
- `enable` : if `0 or False`, it is disabled. if `1 or True`, it is enabled. default is `1`
- `type` : type of subsection. has to be set to `output`
- `gpio` : pin to use for input (in BCM numbering)
- `state` : default state when starting up. if `0` (default). will output low in normal state, and output High (3.3v) when in alarm state
- `authorized_length` : if the user/pin/serial of yubikey is in authorized list, length to turn on buzzer (in sec). Default is 0.2
- `authorized_times` : how many times to turn on the buzzer. e.g if 2 (default), will do BEEP BEEP.
- `unauthorized_length` : if user/pin/serial of yubikey is not in the authorized list, length to turn on buzzer (in sec). Default is 2
- `unauthorized_times` : how many times to turn on the buzzer. e.g if 1 (default), will do BEEP.
- `button_length` : when pressing a key on the keypad. length to turn on buzzer (in sec). Default is 0.1
- `button_times` : how many times to turn on the buzzer. e.g if 1 (default), will do BEEP.
- `ndef_length` : after scanning an NFC card, if NDEF packet has been received. it will now try to authenticate the keys with the yubico servers. Default is 0.1
- `ndef_times` : how many times to turn on the buzzer. Default is 2
- `nondef_length` : after scanning an NFC card, if no NDEF packet received. could be because card/yubikey was too far, or yubkey not configured to send NDEF. Use YubiKey Personalization Tool, Tools, Slot 1, URI, Program. Default is 0.3
- `nondef_times` : how many times to turn on the buzzer. Default is 3
- `toogle_length` : when toogle mode for the door strick has been activated. i.e leaving the door unlocked / door striked powered. Default is 5
- `toogle_times` : how many times to turn on the buzzer. Default is 1

#### [20X] : Relays/output

this section `name` has to be an integer value.
- `name` : name of section
- `enable` : if `0 or False`, it is disabled. if `1 or True`, it is enabled. default is `1`
- `type` : type of subsection. has to be set to `output`
- `gpio` : pin to use for input (in BCM numbering)
- `state` : default state when starting up. if `0` (default). will output low in normal state, and output High (3.3v) when in alarm state
- `output_mode` : mode of operation of relay. if set to `toogle` (default) when on, will stay on. if set to `momentary` when in alarm state, will turn on for a short time, then turn off and stay off for momentary_relay_timer value
- `output_timer` : how long to keep the door unlock for (in sec). default is 5
- `obeysilent` : if set, will not turn on if silentmode is also set



#### [210] : NFC (power switch for the NFC module)
- `name` : name of section
- `enable` : if `0 or False`, it is disabled. if `1 or True`, it is enabled. default is `1`
- `type` : type of subsection. has to be set to `output`
- `gpio` : pin to use for input (in BCM numbering) (25)
- `state` : default state when starting up. if `0` (default). will output low in normal state, and output High (3.3v) when in alarm state
- `delay_before` : how long to leave nfc module off for. default is 1
- `delay_before` : delay to wait after turning on nfc (in sec) default is `2` 
- `nfcport` : physical port to use to communicate with the NFC module. PN532 Using UART has been tested to be working . Default is `tty:AMA0`


#### [30X] : Input Section
 input name SHOULD NOT be changed. the inturupt callback function name is based on that

- `name` : name of section
- `enable` : if `0 or False`, it is disabled. if `1 or True`, it is enabled. default is `1`
- `type` : type of subsection. has to be set to `input`
- `gpio` : pin to use for input (in BCM numbering)
- `state` : default state when starting up. if `0` (default). will set pull down resistor, and wait for 3.3v to be applied to activate. if set to `1`, will set pull up resistor, and wait for connection to ground to activate. (recommend using state = 1 )
- `nc` : type of logic. if Normally Open, set is to `0` (default). if Normally Closed, set to `1`
- `actionboth` : if set to 1, will call the interupt routine for both case. for when input goes from High to Low, and from Low to High.
- `link_status` : if set, it will check the actual status of the input on startup, and update the corresponding output status led accordingly. once set this for things that have a corresponding status led of input id - 100

### [301] : DoorButton
- `debounce_time` : will not trigger again for the debounce time (in millisec)
- `interference_debounce` : after timer, will check the status of the pin, if it is still active, then it is not interferance (in sec)
- `toogle_holdoff` : how long to press button to leave door strike in always open position. Default is 5



#### [50X] : User Section
- `name` : name of User
- `enable` : if `0 or False`, it is disabled. if `1 or True`, it is enabled. default is `1`
- `type` : type of subsection. has to be set to `user`
- `yubikeyotp` : first 12 char of OTP. e.g cccccckhgbhg
- `cardsn` : card serial number does nothing, just there for referance
- `pin` : pin, only numbers. e.g 12345
- `password` : password, e.g Password1



- Note about Driving LEDs directly,

if driving the LED direct from the GPIO, a 160ohm will equal to ~10ma, for a 1.7v drop diode, use 320ohm if lots of leds, ~5ma. else you will hit the combine max current of 54ma very quickly


### It is working?

#### Log files 
You can now check log files

tail -f /var/log/acyonp/acyonp.log
tail -f /var/log/syslog

## Uninstall :(
(Because sometime we need it)
```
chmod +x /usr/local/bin/uninstall-acyonp.sh && sudo /usr/local/bin/uninstall-acyonp.sh
```

#### reducing logging output by snmpd
edit `/lib/systemd/system/snmpd.service`
change `-Lsd` to `-LSwd`
systemctl daemon-reload
systemctl restart snmpd


## log2ram

Hightly recommended.
log2ram installation. this is to reduce the ammount of write to the sdcard, therefore extending the sdcard's life

```
git clone https://github.com/azlux/log2ram.git
cd log2ram
chmod +x install.sh
./install.sh
reboot
```

## wifiNetwork
just for referance.

```
cat /etc/network/interfaces
# interfaces(5) file used by ifup(8) and ifdown(8)

# Please note that this file is written to be used with dhcpcd
# For static IP, consult /etc/dhcpcd.conf and 'man dhcpcd.conf'

# Include files from /etc/network/interfaces.d:
source-directory /etc/network/interfaces.d

auto lo
iface lo inet loopback

iface eth0 inet manual

allow-hotplug wlan0
iface wlan0 inet manual
    wpa-roam /etc/wpa_supplicant/wpa_supplicant.conf
    #wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf


#allow-hotplug wlan1
#iface wlan1 inet manual
#    wpa-roam /etc/wpa_supplicant/wpa_supplicant.conf

# Default to dhcp
iface default inet dhcp

# at home config
iface home inet static
    address 192.168.2.163
    netmask 255.255.255.0
    gateway 192.168.2.254
    dns-nameservers 192.168.2.10 192.168.2.11

iface home inet6 static
    address 2001::163
    netmask 64
    gateway 2001::1
    dns-nameservers 2001::10 2001::11

# at work config
iface work inet static
    address 192.168.1.11
    netmask 255.255.255.0
    gateway 192.168.1.1
    dns-nameservers 192.168.1.1

```

WPA2 PEAP MSCHAPV2 with radius auth. username/password

```
cat /etc/wpa_supplicant/wpa_supplicant.conf
country=AU
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
        ssid="work-IoT"
        priority=10
        proto=RSN
        key_mgmt=WPA-EAP
        pairwise=CCMP
        auth_alg=OPEN
        eap=PEAP
        identity="USERNAME"
        password=hash:7b592e4f8178b4c75788531b2e747687
        phase1="peaplabel=0"
        phase2="auth=MSCHAPV2"
        id_str="work"
}

network={
        ssid="HomeWiFi"
        priority=1
        proto=RSN
        key_mgmt=WPA-EAP
        pairwise=CCMP
        auth_alg=OPEN
        eap=PEAP
        identity="USERNAME2"
        password=hash:cfed65f31df54b698600b882c4aaa55d
        phase1="peaplabel=0"
        phase2="auth=MSCHAPV2"
        id_str="home"
}
```

to generate hash

```
echo -n "PASSWORD" | iconv -t utf16le | openssl md4
```

## Todo

1. logs are going to /var/log/syslog instead (need fixing)

