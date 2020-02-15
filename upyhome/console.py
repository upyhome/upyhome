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

import click
from serial.tools import list_ports
import shutil
import glob
import os
from pathlib import Path

from upyhome.const import *
from upyhome.config import Config, write_network_conf
from upyhome.shell import Shell

COLOR_INFO = "magenta"
COLOR_ASK = "blue"
COLOR_ACTION = "green"
COLOR_ADVERT = "yellow"
COLOR_RESULT = "white"
COLOR_ERROR = "red"
COLOR_COMMENT = "blue"
COLOR_SRC = "bright_black"

default_formater = lambda val: '{0}'.format(val)
file_formatter = lambda file: get_file_name(file)

def get_file_name(file):
    bn = os.path.basename(file)
    return os.path.splitext(bn)[0]

def ask_for(values: list, prompt: str, formater=default_formater):
    for i, val in enumerate(values):
        #print(port.interface)
        click.secho('[%d]: %s'%( i+1, formater(val)), fg=COLOR_ASK)
    selection = "0"
    while not (selection.isdigit() and 0 < int(selection) <= len(values)):
        selection = click.prompt('Select %s (enter row number)'%(prompt)).strip()
    return values[int(selection) - 1]

def ask_port():
    ports = []
    detected = False
    port_list = list_ports.comports()
    for port in port_list:
        #if port.interface is not None:
        detected = True
        ports.append(port)
    if not detected:
        click.secho('No serial devices detected', fg=COLOR_ERROR)
        return None
    port_format = lambda port: '%s (%s)'%(port.device, port.interface)
    sel_port = ask_for(port_list, 'serial port', port_format)
    return sel_port.device

def check_port(conf: Config):
    if not  conf.is_setting_val(SETTING_PORT):
        selected_port = ask_port()
        if selected_port is None:
            click.secho('The port is not configured! Exit', fg='red')
            return False
        else:
            conf.set_setting_val(SETTING_PORT, selected_port)
            conf.save()
            return True
    else:
        return True

def ask_firmware(platform):
    click.secho("Available firmwares:", fg=COLOR_ASK)
    firm_dir = os.path.join('.', FIRMWARE_DIR, '%s*.bin'%(platform))
    firm_list = glob.glob(firm_dir)
    return ask_for(firm_list, 'firmware', file_formatter)

def ask_device(platform, filter=""):
    click.secho("Available devices for %s platform")
    device_dir = os.path.join(BOARD_DIR, platform, '%s*.yaml'%(filter))
    device_list = [os.path.splitext(os.path.basename(f))[0] for f in glob.glob(device_dir)]
    return ask_for(device_list, 'device') 

def ask_network():
    net_conf_dir = os.path.join('.', NETWORK_DIR, '*.yaml')
    network_list = [os.path.splitext(os.path.basename(f))[0] for f in glob.glob(net_conf_dir)] 
    return ask_for(network_list, 'device') 

def ask_create_network():
    if click.confirm('New network setup?'):
        net_name = click.prompt("Network config name").strip()
        net_ssid = click.prompt("Network ssid").strip()
        net_pwd = click.prompt("Network password").strip()
        write_network_conf(net_name, net_ssid, net_pwd)
        ask_create_network()
    else:
        return

def ask_network_config():
    conf = {}
    if click.confirm('Use dhcp?'):
        conf['dhcp'] = True
    else:
        conf['ip'] = click.prompt("ip").strip()
        conf['mask'] = click.prompt("mask").strip()
        conf['gateway'] = click.prompt("gateway").strip()
        conf['dns'] = click.prompt("dns").strip()
    conf['repl_pwd'] = click.prompt("REPL password").strip()
    return conf

def ask_sync(conf_files):
    click.secho("Available configs:", fg=COLOR_ASK)
    return ask_for(conf_files, 'config', file_formatter)
