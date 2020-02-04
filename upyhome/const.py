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

DEVICE_DIR = 'devices'
BOARD_DIR = 'boards'
NETWORK_DIR = 'networks'
FIRMWARE_DIR = 'firmwares'
GENERATOR_DIR = 'generators'

CONFIG_LIST_DIR = '.config'

CONFIG_NAME = 'name'
CONFIG_PLATFORM = 'platform'
CONFIG_USER_CODE = 'user'
CONFIG_NETWORK = 'network'
CONFIG_LIST_NETWORKS = NETWORK_DIR
CONFIG_DRIVER = 'drivers'
CONFIG_USER = 'user'

SETTING_SECTION = 'upyhome'
SETTING_PORT = 'port'
SETTING_FLASH = 'flash'
SETTING_FIRMWARE = 'firmware'
SETTING_GENERATOR = 'generator'
SETTING_BOARD_DIR = 'target'


MICROPYTHON_DIR = 'libraries'
MICROPYTHON_FILES = ['boot.py', 'main.py', 'upyhome.py']
MICROPYTHON_LIBS = {
    "networks": 'netz.py',
    "digital-inputs": "din.py",
    "digital-outputs": "dout.py",
    "leds": "led.py",
    "drivers": "driver.py"
}