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

from machine import Pin, Timer
from neopixel import NeoPixel

class Led:
    def __init__(self, name, h_pin, num, tid):
        self.name = name
        self.num = num
        self.pix = NeoPixel(Pin(h_pin, Pin.OUT), num)
        self.tim = Timer(tid)

    def fill(self, r, g, b): 
        for i in range(self.num):
            self.pix[i] = (r, g, b)
        self.pix.write()

    def off(self):
        self.fill(0, 0, 0)

    def white(self):
        self.fill(255, 255, 255)

    def red(self):
        self.fill(255, 0, 0)

    def green(self):
        self.fill(0, 255, 0)

    def blue(self):
        self.fill(0, 0, 255)

    def fade_in(self):
        pass

    def fade_on(self):
        pass