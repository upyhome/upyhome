#
# This file is part of µpyhone
# Copyright (c) 2020 ng-galien
#
# Licensed under the MIT license:
#   http://www.opensource.org/licenses/mit-license.php
#
# Project home:
#   https://github.com/upyhome/upyhome
#

import uos
import uio
import ubinascii
import utime as time
import upyhome
import gc
from machine import I2C

conf = upyhome.load_config()
dins = upyhome.inputs(conf)
douts = upyhome.outputs(conf)
i2cs = upyhome.i2cs(conf)
spis = upyhome.spis(conf)
drivers = upyhome.drivers(conf, i2cs=i2cs)

upyhome.print_logo()

from led import Led

led = Led("led", 15, 10, 5)
led.white()

def mpu_cb(acc):
    idx = 0
    max = 0
    for i in range(3):
        if abs(acc[i]) > max:
            max = abs(acc[i])
            idx = i
    if idx == 2:
        led.white()
    elif idx==1:
        led.green()
    else:
        led.blue()
    return idx==0

drivers["mpu"].set_callback(mpu_cb)

gc.collect()

def ping( info = False):
    if not info:
        print('#pong')
    gc.collect()

def dout_status():
    for key in douts.keys():
        time.sleep_ms(10)
        douts[key].print_status()
    gc.collect()

def list_dir(directory = '.'):
    res = '#dir:' + directory + '=[null'
    files = uos.ilistdir(directory)
    for file in files:
        #print(file)
        if(file[1] == 32768):
            res += ","
            res += file[0]
    res += ']'
    print(res)
    gc.collect()

def read_file(file):
    fileToRead = uio.open(file)
    content = fileToRead.read()
    res = '#file:' + file + '=['
    res += content.replace('\n', '<BR>')
    res += ']'
    fileToRead.close()
    print(res)
    gc.collect()

