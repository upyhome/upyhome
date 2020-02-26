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

import esptool
import click
import time
from collections import namedtuple
from configparser import ConfigParser
from upyhome.const import *
from upyhome.config import Config

FLASH_PARAMS = namedtuple('Params', 'compress encrypt no_stub flash_size flash_mode flash_freq erase_all verify addr_filename')
DEFAULT_FLASH_SIZE = {
    'esp8266': '1MB',
    'esp32': '4MB',
}

"""
Get flash parameters according the platform
"""
def get_flash_params(platform, flash, file):
    compress = False
    flash_mode = "dout"
    start = 0x0
    if platform == 'esp32':
        compress = False
        flash_mode = "keep"
        start = 0x1000
    return FLASH_PARAMS(compress, False, False, flash, flash_mode, "keep", False, True, [(start, file)])


"""
Instantiate the esp class, run stub
"""
def get_esp(config: Config, baud=esptool.ESPLoader.ESP_ROM_BAUD):
    platform = config.get_config_val(CONFIG_PLATFORM)
    port = config.get_setting_val(SETTING_PORT)
    chip_class = {
        'esp8266': esptool.ESP8266ROM,
        'esp32': esptool.ESP32ROM
    }[platform]
    
    esp = chip_class(port, baud)
    esp.connect()
    click.secho("Chip is %s" % (esp.get_chip_description()), fg="magenta")
    click.secho("Features: %s" % ", ".join(esp.get_chip_features()), fg="magenta")
    click.secho("Crystal is %dMHz" % esp.get_crystal_freq(), fg="magenta")
    esp = esp.run_stub()
    return esp

"""
Flash the ESP
"""
def erase_flash(esp):    
    click.secho('Erasing flash (Please wait)...', fg="green")
    t = time.time()
    esp.erase_flash()
    click.secho('Hard reset...', fg="green")
    esp.hard_reset()
    click.secho('Chip erase completed successfully in %.1fs' % (time.time() - t), fg="green")

"""
Write the firmware, try to autodetect the flash size 
for sonoff: esptool.py --port /dev/cu.usbserial-AH030NYK --baud 115200 write_flash -fs 1MB -fm dout 0x0 ./firmwares/esp8266-v1.12.bin
"""
def write_firmware(esp, platform, firmware, flash=None):
    t = time.time()
    click.secho('Flashing firmware (Please wait)...', fg="green")
    # Detect flash size
    if flash is None:
        click.secho('Auto dectect flash size', fg="yellow")
        flash_id = esp.flash_id()
        flid_lowbyte = (flash_id >> 16) & 0xFF
        flash_size = esptool.DETECTED_FLASH_SIZES.get(flid_lowbyte)
        if flash_size is None:
            flash_size = DEFAULT_FLASH_SIZE[platform]
            click.secho('Size detection failed, set to default: %s'%(flash_size), fg="yellow")
        else:
            click.secho('Size detection successfull: %s'%(flash_size), fg="green")  
    else:
        flash_size = flash      
    # Set flash paraneters
    esp.flash_set_parameters(esptool.flash_size_bytes(flash_size))
    # Write
    with open(firmware, 'rb') as file:
        esptool.write_flash(esp, get_flash_params(platform, flash_size, file))
    click.secho('Hard reset...', fg="green")
    # Rest
    esp.hard_reset()
    click.secho('Flash completed successfully in %.1fs' % (time.time() - t), fg="green")

