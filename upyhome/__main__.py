# TODO use color variable everywhere
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
from tabulate import tabulate
import time
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

from upyhome.console import ask_port, check_port, ask_firmware, ask_device, ask_generator, ask_sync
from upyhome.console import get_networks, ask_create_network, ask_network, ask_network_config
from upyhome.config import get_config_file, get_config_list, get_config_obj, set_config_val
from upyhome.config import save_config_obj, get_config_dir, get_repl_config
from upyhome.config import is_setting_val, get_setting_val, set_setting_val
from upyhome.config import write_network_conf, get_generator_list, compile_conf_files, write_json_conf
from upyhome.const import CONFIG_NAME, CONFIG_PLATFORM, CONFIG_NETWORK
from upyhome.const import SETTING_PORT, SETTING_FLASH
from upyhome.const import SETTING_FIRMWARE, SETTING_GENERATOR
from upyhome.const import DEVICE_DIR, BOARD_DIR, NETWORK_DIR, FIRMWARE_DIR, CONFIG_LIST_DIR, SETTING_BOARD_DIR
from upyhome.esputil import get_esp, erase_flash, write_firmware
from upyhome.shell import Shell

from upyhome.console import COLOR_INFO, COLOR_ACTION,COLOR_ADVERT,COLOR_RESULT,COLOR_ERROR,COLOR_COMMENT,COLOR_SRC

yaml=YAML()
yaml.indent(sequence=4, offset=2) 
@click.group()
def cli():
    pass

def validate_name(ctx, param, value):
    if re.match("^[a-zA-Z0-9-_.]{2,}$", value) is not None:
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
    click.secho('Init upyhome: platform %s with name %s' %(platform, name), fg=COLOR_INFO)
    config_file = get_config_file(name)
    if os.path.exists(config_file):
        click.secho('!!! Device %s already exists !!!' %(name), err=not force, fg=COLOR_ADVERT)
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
        return check_config(ctx, param, value)

@cli.command()
@click.option('--config', type=click.STRING, prompt="Enter device config" ,required=True, callback=check_config)
@click.option('--port', type=click.Path(exists=True), required=False)
def serial(config, port):
    conf_obj = get_config_obj(config)
    if port is None:
        selected_port = ask_port()
    else:
        selected_port  = port
    if selected_port is None:
        click.secho('The port is not configured! Exit', fg='red')
        return
    set_setting_val(conf_obj, SETTING_PORT, selected_port)
    save_config_obj(conf_obj)
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


# TODO Deploy multi config
@cli.command()
@click.option('--config', type=click.STRING, prompt="Enter device config", required=True, callback=check_config)
@click.option('--skip/--no-skip', default=False, required=False)
def sync(config, skip):
    click.secho('Sync files', fg='magenta')
    conf_obj = get_config_obj(config)
    shell = Shell(conf_obj)
    shell.begin()
    had_stopped = False
    if shell.is_upyhone():
        click.secho('Upyhonme is running, try to stop it', fg='yellow')
        if shell.upyhone_exec('stop'):
            had_stopped = True
            click.secho('Upyhonme is stopped', fg='green')
    else:
        click.secho('Upyhonme is not running', fg='green')
    time.sleep(0.5)
    error = shell.sync_time()
    if error:
        click.secho('Failed to sync time, abort!', fg='red')
        return
    click.secho('Sync time done! checking file system', fg='green')
    shell.mkdirs()
    click.secho('Compute file operations', fg='magenta')
    click.echo()
    files = shell.sync_files(conf_obj)
    
    if skip:
        files = list(filter(lambda file: file[0] not in ['config.json', 'webrepl_cfg.py'] , files))

    click.secho(tabulate(files, ['file', 'operatiom', 'date'], 'github'), fg='bright_cyan')
    click.echo()
    
    if click.confirm('Continue'):
        for file in files:
            if(file[1] == 'update' or file[1] == 'add'):
                click.secho('Copy file %s'%(file[0]), fg='magenta')
                shell.copy_file(file[0])
            elif(file[1] == 'delete'):
                click.secho('Delete file %s'%(file[0]), fg='magenta')
                shell.rm_file(file[0])
        if not skip:
            click.secho('Compile config', fg='magenta')
            conf_dir = os.path.join(DEVICE_DIR, '.'+config)
            os.makedirs(conf_dir, exist_ok=True)
            conf_file = compile_conf_files(conf_obj)
            multiple = isinstance(conf_file, list)
            if multiple:
                for i, cf in enumerate(conf_file):
                    write_json_conf(cf, os.path.join(conf_dir, '%03d-config.json'%(i)))  
                    select = ask_sync(conf_file)
                    shell.copy_file('config.json', conf_dir, index=select)
            else: 
                write_json_conf(conf_file, os.path.join(conf_dir, 'config.json'))
                click.secho('Copy main config', fg='magenta')
                shell.copy_file('config.json', conf_dir)
            #repl
            repl = get_repl_config(conf_obj)
            if repl is not None:
                click.secho('Copy REPL config', fg='magenta')
                data = 'PASS = "%s"\n'%(repl)
                shell.copy_data(data, 'webrepl_cfg.py')

    if had_stopped:
        click.secho('Restart upyHome', fg='yellow')
        if shell.upyhone_exec('start'):
            click.secho('Upyhonme is started', fg='green')
    if click.confirm('Soft reset'):
        shell.soft_reset()
    else:
        shell.end()
    click.secho('Sync finished', fg='magenta')

@cli.command()
@click.option('--config', type=click.STRING, prompt="Enter device config", required=True, callback=check_config)
def stop(config):
    click.secho('Stop upyhome', fg='magenta')
    conf_obj = get_config_obj(config)
    shell = Shell(conf_obj)
    shell.begin()
    if shell.is_upyhone():
        click.secho('Upyhonme is running, try to stop it', fg='yellow')
        if shell.upyhone_exec('stop'):
            click.secho('Upyhonme is stopped', fg='green')
    else:
        click.secho('Upyhonme is not running, nothing to do', fg='yellow')
    shell.end()

@cli.command()
@click.option('--config', type=click.STRING, prompt="Enter device", required=True, callback=check_config)
@click.option('--function', type=click.STRING, prompt="Enter function", required=True)
@click.option('--topic', type=click.STRING, prompt="Enter topic", required=False, default=None)
def exec(config, function, topic):
    click.secho('Execute a command', fg='magenta')
    conf_obj = get_config_obj(config)
    shell = Shell(conf_obj)
    shell.begin()
    had_stopped = False
    if shell.is_upyhone():
        click.secho('Upyhonme is running, try to stop it', fg='yellow')
        if shell.upyhone_exec('stop'):
            had_stopped = True
            click.secho('Upyhonme is stopped', fg='green')
    click.secho('Execute %s for topic %s'%(function, topic if topic is not None else "all"), fg='green')
    res = shell.upyhone_exec(func=function, comp=topic)
    click.secho('Result: %s'%(re), fg='yellow')
    if had_stopped:
        click.secho('Restart upyHome', fg='yellow')
        if shell.upyhone_exec('start'):
            click.secho('Upyhonme is started', fg='green')
    shell.end()

@cli.command()
@click.option('--config', type=click.STRING, prompt="Enter device config", required=True, callback=check_config)
@click.option('--file', type=click.STRING, prompt="Enter file", required=True)
def view(config, file):
    click.secho('Open file', fg=COLOR_INFO)
    conf_obj = get_config_obj(config)
    shell = Shell(conf_obj)
    shell.begin()
    had_stopped = False
    if shell.is_upyhone():
        click.secho('Upyhonme is running, try to stop it', fg=COLOR_ACTION)
        if shell.upyhone_exec('stop'):
            had_stopped = True
        else:
            click.secho('Upyhonme not stopped', fg=COLOR_ERROR)
    res = shell.tail(file)
    content = res.split('\n')
    p1 = re.compile('^[ ]*#.*$')
    p2 = re.compile('^.*""".*$')
    click.secho('>================================================<', fg=COLOR_INFO)
    com1 = com2 = False
    for line in content:
        m1 = p1.match(line)
        m2 = p2.match(line)
        if m1:
            com1 = True
        elif m2:
            com2 = not com2
        click.secho(line, fg=COLOR_COMMENT if com1 or com2 or m2 else COLOR_SRC)
        com1 = False
    click.secho('>================================================<', fg=COLOR_INFO)
    if had_stopped:
        click.secho('Restart upyHome', fg=COLOR_ACTION)
        if shell.upyhone_exec('start'):
            click.secho('Upyhonme is started', fg=COLOR_RESULT)
    shell.end()

if __name__ == '__main__':
    cli()