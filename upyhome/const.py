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
TIME_OFFSET=946681200

DEVICE_DIR = 'devices'
BOARD_DIR = 'boards'
NETWORK_DIR = 'networks'
FIRMWARE_DIR = 'firmwares'
GENERATOR_DIR = 'generators'
LIB_DIR = 'micropython'

CONFIG_LIST_DIR = '.config'

CONFIG_NAME = 'name'
CONFIG_PLATFORM = 'platform'
CONFIG_USER_CODE = 'user'
CONFIG_NETWORK = 'network'
CONFIG_LIST_NETWORKS = 'wifi'
CONFIG_DRIVER = 'drivers'
CONFIG_USER = 'user'
CONFIG_FILE = 'config'
CONFIG_REPL = 'repl'

SETTING_SECTION = 'upyhome'
SETTING_PORT = 'port'
SETTING_FLASH = 'flash'
SETTING_FIRMWARE = 'firmware'
SETTING_GENERATOR = 'generator'
SETTING_BOARD_DIR = 'target'
SETTING_UPLOAD = 'upload'


MICROPYTHON_DIR = 'micropython'
MICROPYTHON_FILES = ['boot.py', 'main.py', 'upyhome.py']
MICROPYTHON_LIBS = {
    'common': {
        'all': ['base.py', 'pub.py', 'sub.py', 'proxy.py']
    },
    'network': {
        'all': ['net.py']
    },
    'mdns': {
        'esp8266': ['mdns.py']
    },
    'digital-inputs': {
        'all': ['din.py']
    },

    'digital-outputs': {
        'all': ['dout.py']
    },
    'leds': {
        'all': ['led.py']
    },
    'drivers': {
        'all': ['driver.py']
    }
}