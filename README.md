# upyHome MicroPython (ESP32/8266) libraries

Base MicroPython libraries to get started with upyHome.  
Special thanks to [ESPHome](https://esphome.io/) team and their great firmware.

## Installation

### Python

Install Python 3 on your system.

### MicroPython - Manual installation

First install the MicroPython firmware on your device, further instructions in [the official MicroPython documentation](http://docs.micropython.org/en/latest/).  

> The following instructions are for ESP8266 devices (most of IOT devices on the market).

Install esptool flashing utility with pip.
```bash
$ pip install esptool  
```

Connect your device with the usb to serial converter.

> Most ESP devices must start in boot mode to be flashed. For most of them, you must pulldown the Pin 0 on the chip.  
> For example, you have to keep the button pressed down while connecting a Sonoff basic.  
> Further information can be found on the Tasmota site for [preparation](https://github.com/arendst/Tasmota/wiki/Hardware-Preparation) and [flashing](https://github.com/arendst/Tasmota/wiki/Flashing).

Erase the flash and install the firmware.

* --port option is your serial port
* firmware.bin is the [downloaded](http://www.micropython.org/download) firmware from here (choose the correct platform according to your device if it's not ESP8266).


```bash
# get upyhome repo
git clone https://github.com/upyhome/upyhome.git
# enter uphome directory
cd upyhome
# erase the device
esptool.py --port /dev/ttyUSB0 erase_flash
# flash the device
esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 esp32-20180511-v1.9.4.bin

```

### upyHome - Manual installation

Install rshell with pip.
```bash
pip install rshell
```

Connect and copy python files to the device.
```bash
rshell
...
# connect 
upyhome> connect serial /dev/tty.usb
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
# Wait for prompt and ctrl+D to soft reboot
```