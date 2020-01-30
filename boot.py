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

import micropython
import gc

def connect():
    import network
    import machine
    import ujson
    import webrepl
    cf = open('config/credentials.json', 'r')
    cred = ujson.load(cf)
    cf.close()
    print(cred)
    wlan = network.WLAN(network.STA_IF)

    if not cred["use_dhcp"]:
        wlan.ifconfig((cred["ip"], cred["subnet"], cred["gateway"], cred["dns"]))
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(cred["ssid"], cred["wifi_pwd"])
        while not wlan.isconnected():
            machine.idle()
    print('network config:', wlan.ifconfig())
    if(cred["repl_pwd"]):
        webrepl.start(cred["repl_pwd"])    
    else:
        webrepl.start()

gc.enable()
micropython.alloc_emergency_exception_buf(100)
connect()
gc.collect()


