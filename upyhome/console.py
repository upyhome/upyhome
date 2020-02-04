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

from upyhome.const import SETTING_SECTION, SETTING_PORT, SETTING_FLASH
from upyhome.const import SETTING_FIRMWARE, SETTING_GENERATOR
from upyhome.const import DEVICE_DIR, BOARD_DIR, NETWORK_DIR, FIRMWARE_DIR
from upyhome.config import is_setting_val, get_setting_val, set_setting_val
from upyhome.config import save_config_obj, write_network_conf, get_generator_names

def ask_port():
    ports = []
    detected = False
    for port in list_ports.comports():
        if port.interface is not None:
            detected = True
            ports.append(port)
    if not detected:
        print('No serial devices detected')
        return None
    click.secho("Detected ports", fg="green")
    for i, port in enumerate(ports):
        #print(port.interface)
        click.secho('[%d]: %s (%s)' %(i+1, port.device, port.interface), fg="magenta")
    selection = "0"
    while not (selection.isdigit() and 0 < int(selection) <= len(ports)):
        selection = click.prompt("Select Port (enter row number)").strip()
    sel_port = ports[int(selection) - 1]
    return sel_port.device

def check_port(conf):
    if not is_setting_val(conf, SETTING_PORT):
        selected_port = ask_port()
        if selected_port is None:
            click.secho('The port is not configured! Exit', fg='red')
            return False
        else:
            set_setting_val(conf, SETTING_PORT, selected_port)
            save_config_obj(conf)
            return True
    else:
        return True
    


def ask_firmware(platform):
    click.secho("Available firmwares:", fg="green")
    firm_dir = os.path.join('.', FIRMWARE_DIR, '%s*.bin'%(platform))
    firm_list = glob.glob(firm_dir)
    for i, firm in enumerate(firm_list):
        name = os.path.basename(firm)
        click.echo('[%d]: %s' %(i+1, os.path.splitext(name)[0]))
    selection = "0"
    while not (selection.isdigit() and 0 < int(selection) <= len(firm_list)):
        selection = click.prompt("Select Firmware (enter row number)").strip()
    return firm_list[int(selection) - 1] 

def ask_device(platform, filter=""):
    click.secho("Available devices for %s platform")
    device_dir = os.path.join(BOARD_DIR, platform, '%s*.yaml'%(filter))
    device_list = [os.path.splitext(os.path.basename(f))[0] for f in glob.glob(device_dir)] 
    for i, device in enumerate(device_list):
        click.echo('[%d]: %s' %(i+1, device))
    selection = "0"
    while not (selection.isdigit() and 0 < int(selection) <= len(device_list)):
        selection = click.prompt("Select a device (enter row number)").strip()
    return device_list[int(selection) - 1] 

def get_networks():
    net_conf_dir = os.path.join('.', NETWORK_DIR, '*.yaml')
    return [os.path.splitext(os.path.basename(f))[0] for f in glob.glob(net_conf_dir)] 

def ask_network():
    click.secho("Available Networks:")
    network_list = get_networks()
    for i, network in enumerate(network_list):
        click.echo('[%d]: %s' %(i+1, network))
    selection = "0"
    while not (selection.isdigit() and 0 < int(selection) <= len(network_list)):
        selection = click.prompt("Select a device (enter row number)").strip()
    return network_list[int(selection) - 1] 

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

def ask_generator(config):
    if not is_setting_val(config, SETTING_GENERATOR):
        return -1
    name_list = get_generator_names(config)
    for i, name in enumerate(name_list):
        click.echo('[%d]: %s' %(i+1, name))
    selection = "0"
    while not (selection.isdigit() and 0 < int(selection) <= len(name_list)):
        selection = click.prompt("Select a config (enter row number)").strip()
    return int(selection) - 1 