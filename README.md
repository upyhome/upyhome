# upyHome MicroPython tool

## Goals

This command line utility helps to configure and manage your micropython enabled device.  
You can create and deploy upyHome on your device.

## Get started

First install Python 3 on your system.

Clone the repository to a folder on your computer.  
You must [install git](https://git-scm.com/) or download the [zipe file](https://github.com/upyhome/upyhome/archive/master.zip).


```bash
$ git clone https://github.com/upyhome/upyhome.git
# goto upyhome folder
$ cd upyhome
# intall with pip
$ pip install .
```

Run upyhome to get command list

```bash
$ upyhome 
Usage: upyhome [OPTIONS] COMMAND [ARGS]...

  Command line utility for managing a upyhome device. For further
  informations type 'upyhome YOUR_COMMAND --help'

Options:
  --help  Show this message and exit.

Commands:
  create   Create a config file.
  erase    Erase flash, data will be lost.
  exec     Execute a task on the device.
  flash    Load micropython firmware.
  monitor  Monitor upyhome on the device.
  serial   Define the serial port used by the device.
  start    Start upyhome on the device.
  stop     Stop upyhome on the device.
  sync     Upload the upyhome files.
  view     Display a file on the device.
```


## Installation


### Python



### Upyhome

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