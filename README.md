# upyHome micropython (ESP32/8266) libraries for Node-Red

Base µpython libs to get started with upyhome.  
Special thanks to [ESPHome](https://esphome.io/) team and there great firmware.

## Installation

### Python

Install python3 on your system.  

### µPython - Manual installation

We must first install the µpython firmware on your device, other detailed instructions [in the official documentation](http://docs.micropython.org/en/latest/)  

> The following instructions are for ESP8266 devices, such as most of IOT devices on the market.

Install esptool flashing utility (for ESP8266 or ESP32)
```bash
$ pip install esptool  
$ esptool.py
```

Connect your device with the usb to serial converter

> Most of ESP devices must enter in boot mode to be flashed. For many of them you must pulldown the Pin 0 on the chip  
> For example you have to keep the button pressed while connecting a sonoff basic.  
> You can find more informations on the Tasmota site for [preparation](https://github.com/arendst/Tasmota/wiki/Hardware-Preparation) and [flashing](https://github.com/arendst/Tasmota/wiki/Flashing).

Erase the flash and install the firmware.

* --port option is your comport
* firmware.bin is the [downloaded file](http://www.micropython.org/download) firmware from here (choose the correct platform according your device if it's not 8266).


```bash
# get upyhome repo
git clone https://github.com/upyhome/upyhome.git
# enter uphome directory
cd upyhome
# erase the device
esptool.py --port /dev/ttyUSB0 erase_flash
# flash the device
esptool.py --port /dev/ttyUSB0 --baud 460800 write_flash --flash_size=detect 0 firmware/firmware.bin

```

### upyhome - Manual installation

Install rshell with pip
```bash
pip install rshell
```

Connect and copy python files to the device
```bash
rshell
...
# connect 
upyhome> connect serial /dex/tty.usb
# copy configs
upyhome> cp -r config /pyboard
# copy libs
upyhome> cp -r lib /pyboard
# copy main files 
upyhome> cp -r upyhome.py /pyboard
upyhome> cp -r boot.py /pyboard
upyhome> cp -r main.py /pyboard
# go to repl
upyhome> repl
# Wait for prompt and ctrl+D to soft reboot the device
```