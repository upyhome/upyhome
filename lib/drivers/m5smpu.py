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

from driver import Driver
from mpu6500 import MPU6500

class M5SMPU(Driver, MPU6500): 
    def __init__(self, name, tid, polling=1000, i2c=None, address=None, user_cb=None, **kwargs):
        Driver.__init__(self, name, tid, polling=polling, user_cb=user_cb)
        MPU6500.__init__(self, i2c = i2c, address=address, **kwargs)
        
    def get_val(self):
        return self.acceleration

    def print_val(self):
        if self.val is not None:
            print("#drv:{}=[{}]".format(self.name, self.val))
