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

import sys
sys.path.append('/lib/drivers')
this = sys.modules[__name__]
this.timer_index = 1

def print_logo():
    logo = """
                 __ __               
 __ _____  __ __/ // /__  __ _  ___ 
/ // / _ \/ // / _  / _ \/  ' \/ -_)
\_,_/ .__/\_, /_//_/\___/_/_/_/\__/ 
   /_/   /___/                      
"""
    print(logo)
 
def print_error(domain, msg):
    pass

def load_config():
    import ujson
    cf = open('config/config.json', 'r')
    config = ujson.load(cf)
    cf.close()
    return config

def check_config():
    return True

def inputs(config):
    import din
    res = {}
    for conf in config["digital-inputs"]:
        if "pin" in conf and "name" in conf:
            pin = conf["pin"]
            name = conf["name"]
            del conf["pin"]
            del conf["name"]
            res[name] = din.DigitalInputPin(*(pin, name, this.timer_index), **conf)
            this.timer_index += 1
        else:
            print_error('conf', 'Invalid input config')
    return res

def outputs(config):
    import dout
    res = {}
    for output in config["digital-outputs"]:
        print(output)
        res[output["name"]] = dout.DigitalOutputPin(output["pin"], output["name"], output["inverted"])
    return res

def i2cs(config):
    from machine import I2C
    from machine import Pin
    res = {}
    for conf in config["i2c"]:
        if "hard" in conf and "name" in conf:
            hard = conf["hard"]
            name = conf["name"]
            num = conf["num"]
            del conf["hard"]
            del conf["name"]
            del conf["num"]
            conf["sda"] = Pin(conf["sda"])
            conf["scl"] = Pin(conf["scl"])
            if hard:
                res[name] = I2C(num, **conf) 
            else:
                res[name] = I2C(**conf)
    return res

def spis(config):
    res = {}
    return res

def drivers(config, i2cs=None, spis=None):
    res = {}
    import driver
    for conf in config["drivers"]:
        if "name" in conf:
            if "i2c" in conf and i2cs is not None and conf["i2c"] in i2cs:
                i2c_port = _get_config_key(conf, "i2c", True)
                driver = _get_config_key(conf, "driver", True)
                name = _get_config_key(conf, "name", True)
                address = int(_get_config_key(conf, "address", True), 16)
                polling = _get_config_key(conf, "polling", True)
                if address in i2cs[i2c_port].scan():
                    module = __import__(driver)
                    class_ = getattr(module, driver.upper())
                    i2c_port = i2cs[i2c_port]
                    res[name] = class_(name, this.timer_index, i2c=i2c_port, address=address, polling=polling, **conf)
                    this.timer_index += 1
                else:
                    print("address {} not found in the i2c network {}".format(address, i2c_port))
    return res

def _get_config_key(config, key, suppress=False):
    val = config[key] if key in config else None
    if val is not None and suppress:
        del config[key]
    return val
