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
"""
It prints tree events
    - When it's pressed -> P
    - When it's clicked -> C
    - When it's long pressed -> L
"""
class DigitalInputPin:

    def __init__(self, h_pin, name, tid, inverted=True, debounce=60, long=1000, user_cb=None):
        self.name = name
        self.inv = inverted
        self.dbc_t = debounce
        self.long_t = long
        self.custom_cb = user_cb
        self.user_cb = self.user_eval if user_cb else None
        self.debouncing = False
        self.suppress = False
        self.target = 0
        self.dbc_tim = Timer(tid)
        self.pin = Pin(h_pin, Pin.IN, Pin.PULL_UP if self.inv else Pin.PULL_DOWN)
        self.pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.irq_cb)

    def set_callback(self, user_cb):
        self.user_cb = user_cb
        
    def user_eval(self, event):
        cmd = "\n".join(self.custom_cb)
        exec(cmd, globals(), {'event': event}) 

    def irq_cb(self, pin):
        self.target = pin.value()
        if self.debouncing or self.suppress:
            self.suppress = False
            self.debouncing = False
            self.dbc_tim.deinit()
            return
        self.dbc_tim.init(period=self.dbc_t, mode=Timer.ONE_SHOT, callback=self.dbc_cb)
        self.debouncing = True

    def dbc_cb(self, tim):
        self.debouncing = False
        if self.pin.value() == self.target:
            event = 'C' if (self.inv and self.target == 1) or (not self.inv and self.target == 0) else 'P'
            self.print_event(event)
            if(event == 'P'):
                self.dbc_tim.init(period=self.long_t, mode=Timer.ONE_SHOT, callback=self.long_cb)
            else:
                self.dbc_tim.deinit()
        
    def long_cb(self, tim):
        if self.pin.value() == self.target:
            self.suppress = True
            self.print_event('L')
    
    def print_event(self, event):
        print('#di:{}=[{}]'.format(self.name, event))
        if self.user_cb is not None:
            self.user_cb(event)
            
    def print_val(self):
        print('#di:{}=[{}]'.format(self.name, self.pin.value()))