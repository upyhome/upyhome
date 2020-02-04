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
from datetime import datetime

import shutil
import glob
import os
import datetime
import click
from pathlib import Path
from ruamel.yaml import YAML
from serial.tools import list_ports
from rshell.main import is_micropython_usb_device, extra_info
from rshell.main import Shell
import esptool
import json
import re
import upyhome.console as console
from upyhome.console import ask_port, check_port, ask_firmware, ask_device, ask_generator
from upyhome.console import get_networks, ask_create_network, ask_network, ask_network_config

from upyhome.config import get_config_file, get_config_list, get_config_obj, set_config_val
from upyhome.config import save_config_obj, get_config_dir
from upyhome.config import is_setting_val, get_setting_val, set_setting_val
from upyhome.config import write_network_conf, get_generator_list, write_conf_files

from upyhome.const import CONFIG_NAME, CONFIG_PLATFORM, CONFIG_NETWORK
from upyhome.const import SETTING_PORT, SETTING_FLASH
from upyhome.const import SETTING_FIRMWARE, SETTING_GENERATOR
from upyhome.const import DEVICE_DIR, BOARD_DIR, NETWORK_DIR, FIRMWARE_DIR, CONFIG_LIST_DIR, SETTING_BOARD_DIR
from upyhome.esputil import get_esp, erase_flash, write_firmware

from upyhome.shell import Shell



yaml=YAML()
yaml.indent(sequence=4, offset=2) 
@click.group()
def cli():
    pass

def validate_name(ctx, param, value):
    if re.match("^[a-zA-Z0-9-_.]{3,}$", value) is not None:
        return value
    else:
        click.secho('Incorrect name, retry', fg="red")
        value = click.prompt(param.prompt)
        return validate_name(ctx, param, value)

@cli.command()
@click.option('--name', type=click.STRING, prompt="Config name (minimum 3 letters or digits or . - _)", required=True, callback=validate_name)
@click.option('--platform', prompt="ESP platform", type=click.Choice(['esp8266', 'esp32'], case_sensitive=True))
@click.option('--force/--no-force', default=False, required=False)
@click.option('--device-filter', default="", required=False)
def create(name, platform, force, device_filter):
    click.secho('Init upyhome: platform %s with name %s' %(platform, name), fg="green")
    config_file = get_config_file(name)
    if os.path.exists(config_file):
        click.secho('!!! Device %s already exists !!!' %(name), err=not force, fg="yellow")
        if force and click.confirm('Delete and recreate the device?'):
            os.remove(config_file)
        else:
            return
    # choose the model
    device_model = 'generic-%s.yaml'%(platform)
    if click.confirm('Look for a predefined device?'):
        device_model = '%s.yaml'%(ask_device(platform, device_filter))
    # net work creation
    ask_create_network()
    # net work configuration
    device_file = os.path.join(BOARD_DIR, platform, device_model)
    with open(device_file, 'r') as device_in:
        
        device_obj = yaml.load(device_in)
        #if 'networks' not in device_obj:
        device_obj['networks'] = []
        while click.confirm('Add netwok to device config?'):
            net_name = ask_network()
            net_config = {CONFIG_NETWORK: net_name}
            net_config.update(ask_network_config())
            device_obj['networks'].append(net_config)
        with open(get_config_file(name), 'w') as out:
            yaml.dump(device_obj, out)

def check_config(ctx, param, value):
    device_list = get_config_list()
    if value in device_list:
        return value
    else:
        click.secho('Incorrect config, retry', fg="red")
        click.secho('Available configs: %s' %((', ').join(device_list)), fg="red")
        value = click.prompt(param.prompt)
        return validate_name(ctx, param, value)

@cli.command()
@click.option('--config', type=click.STRING, prompt="Enter device config" ,required=True, callback=check_config)
@click.option('--port', type=click.Path(exists=True), required=False)
def serial(config, port):
    if port is None:
        selected_port = ask_port()
    else:
        selected_port  = port
    if selected_port is None:
        click.secho('The port is not configured! Exit', fg='red')
        return
    set_config_val(config, SETTING_PORT, selected_port)
    click.secho('The port "%s" is set for config "%s"'%(selected_port, config), fg='green')

@cli.command()
@click.option('--config', type=click.STRING, prompt="Enter device config", required=True, callback=check_config)
def erase(config):
    click.secho('Erase flash, you will loose all data on the device!', fg='magenta')
    click.secho('Ensure the device is in boot mode!', fg='yellow')
    if not click.confirm('Continue'):
        return
    conf_obj = get_config_obj(config)
    if not check_port(conf_obj):
        return
    esp = get_esp(conf_obj)
    erase_flash(esp)
    esp._port.close()
    click.secho('Disconnect/Reconnect the device to continue', fg='green')
    
@cli.command()
@click.option('--config', type=click.STRING, prompt="Enter device config", required=True, callback=check_config)
@click.option('--file', required=False)
def flash(config, file):
    click.secho('Flashing micropython, be sure choosing the right firmware!', fg='magenta')
    click.secho('Ensure the device is in boot mode!', fg='yellow')
    if not click.confirm('Continue'):
        return
    conf_obj = get_config_obj(config)
    if not check_port(conf_obj):
        return
    platform = conf_obj[CONFIG_PLATFORM] if CONFIG_PLATFORM in conf_obj else None
    if platform is None:
        click.secho('Config platform not found', fg='red')
    if file is None:
        firmware = ask_firmware(platform)  
    else:
        firmware = firmware
    set_setting_val(conf_obj, SETTING_FIRMWARE, firmware)
    flash_size = get_setting_val(conf_obj, SETTING_FLASH)
    esp = get_esp(conf_obj)
    write_firmware(esp, platform, firmware, flash_size)
    esp._port.close()
    save_config_obj(conf_obj)
    click.secho('Disconnect/Reconnect the device to continue', fg='green')

@cli.command()
@click.option('--config', type=click.STRING, prompt="Enter device config", required=True, callback=check_config)
@click.option('--remove', default=False, required=False)
def deploy(config, remove):
    click.secho('Deploy upyhome, it will update newest file on the device!', fg='magenta')
    if not click.confirm('Continue'):
        return
    args = '-n' if remove else ''
    conf_obj = get_config_obj(config)
    if not check_port(conf_obj):
        return
    port = get_setting_val(conf_obj, SETTING_PORT)
    src_dir = get_config_dir(conf_obj)
    board_dir = get_setting_val(config, SETTING_BOARD_DIR)
    write_conf_files(conf_obj)
    selected_conf = ask_generator(conf_obj)
    if selected_conf >= 0:
        src = os.path.join(get_config_dir(conf_obj), CONFIG_LIST_DIR, '%d.json'%(selected_conf))
        dest = os.path.join(get_config_dir(conf_obj), 'config.json')
        shutil.copy2(src, dest)
    #sync(port, src_dir, dest_dir=board_dir, opts=args)    
    click.secho('Deploy done!', fg='green')

@cli.command()
@click.option('--config', type=click.STRING, prompt="Enter device config", required=True, callback=check_config)
def test(config):
    click.secho('Test', fg='magenta')
    conf_obj = get_config_obj(config)
    shell = Shell(conf_obj)
    shell.begin()
    uph = shell.is_upyhone()
    if uph:
        click.secho('Upyhonme is running, try to stop it', fg='yellow')
    else:
        click.secho('Upyhonme is not running', fg='green')
    error = shell.sync_time()
    if error:
        click.secho('Failed to sync time, abort!', fg='red')
    click.secho('Sync time done!', fg='green')
    click.secho('List files', fg='magenta')
    files = shell.list_files()
    for file in files:
        click.secho('file: %s'%(str(file)), fg='yellow')
    shell.end()
if __name__ == '__main__':
    cli()