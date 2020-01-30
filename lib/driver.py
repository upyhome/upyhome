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
from machine import Timer

class Driver():
    def __init__(self, name, tid, user_cb=None, polling=1000):
        self.name = name
        self.polling = polling
        self.timer = Timer(tid)
        self.user_cb = user_cb
        self.val = None
        
    def timer_cb(self, tim):
        self.val = self.get_val()
        if self.val is not None:
            if self.user_cb is not None:
                if self.user_cb(self.val):
                    self.print_val()
            else: 
                self.print_val()

    def set_callback(self, user_cb):
        self.user_cb = user_cb

    def start(self):
        self.timer.init(period=self.polling, mode=Timer.PERIODIC, callback=self.timer_cb)
    
    def stop(self):
        self.timer.deinit()

    def get_val(self):
        return {}
    
    def print_val(self):
        pass
