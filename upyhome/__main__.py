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
import esptool
import json
import re

from upyhome.console import *
from upyhome.config import Config, get_config_file, get_config_list
from upyhome.const import CONFIG_NAME, CONFIG_PLATFORM, CONFIG_NETWORK
from upyhome.const import SETTING_PORT, SETTING_FLASH
from upyhome.const import SETTING_FIRMWARE, SETTING_GENERATOR
from upyhome.const import DEVICE_DIR, BOARD_DIR, NETWORK_DIR, FIRMWARE_DIR, CONFIG_LIST_DIR, SETTING_BOARD_DIR
from upyhome.esputil import get_esp, erase_flash, write_firmware
from upyhome.shell import Shell

from upyhome.console import COLOR_INFO, COLOR_ACTION,COLOR_ADVERT,COLOR_RESULT,COLOR_ERROR,COLOR_COMMENT,COLOR_SRC

yaml=YAML()
yaml.indent(sequence=4, offset=2) 

def print_sep():
    click.secho('>================================================<', fg=COLOR_INFO)

@click.group()
def cli():
    """
    Command line utility for managing a upyhome device.
    For further informations type 'upyhome YOUR_COMMAND --help'
    """
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
    """
    Create a config file.
    """
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
    """
    Select the serial port for a config.
    """
    conf = Config(config)
    if port is None:
        selected_port = ask_port()
    else:
        selected_port  = port
    if selected_port is None:
        click.secho('The port is not configured! Exit', fg='red')
        return
    conf.set_setting_val(SETTING_PORT, selected_port)
    conf.save()
    click.secho('The port "%s" is set for config "%s"'%(selected_port, config), fg='green')

@cli.command()
@click.option('--config', type=click.STRING, prompt="Enter device config", required=True, callback=check_config)
def erase(config):
    """
    Erase flash, data will be lost.
    """
    click.secho('Erase flash, you will loose all data on the device!', fg='magenta')
    click.secho('Ensure the device is in boot mode!', fg='yellow')
    if not click.confirm('Continue'):
        return
    _conf = Config(config)
    if not check_port(_conf):
        return
    esp = get_esp(_conf)
    erase_flash(esp)
    esp._port.close()
    click.secho('Disconnect/Reconnect the device to continue', fg='green')
    
@cli.command()
@click.option('--config', type=click.STRING, prompt="Enter device config", required=True, callback=check_config)
@click.option('--file', required=False)
def flash(config, file):
    """
    Load micropython firmware.
    """
    click.secho('Flashing micropython, be sure choosing the right firmware!', fg='magenta')
    click.secho('Ensure the device is in boot mode!', fg='yellow')
    if not click.confirm('Continue'):
        return
    _conf = Config(config)
    if not check_port(_conf):
        return
    platform = _conf.get_config_val(CONFIG_PLATFORM)
    if platform is None:
        click.secho('Config platform not found', fg='red')
    if file is None:
        firmware = ask_firmware(platform)  
    else:
        firmware = firmware
    _conf.set_setting_val(SETTING_FIRMWARE, firmware)
    flash_size = _conf.get_setting_val(SETTING_FLASH)
    esp = get_esp(_conf)
    write_firmware(esp, platform, firmware, flash_size)
    esp._port.close()
    _conf.save()
    click.secho('Disconnect/Reconnect the device to continue', fg='green')

@cli.command()
@click.option('--config', type=click.STRING, prompt="Enter device config", required=True, callback=check_config)
def files(config):
    """
    List devices files.
    """
    click.secho('List files', fg='magenta')
    _conf = Config(config)
    check_port(_conf)
    shell = Shell(_conf, stop=True)
    files = shell.list_files(pretty_print=True)
    print_sep()
    click.secho(tabulate(files, ['file', 'date'], 'github'), fg='bright_cyan')
    print_sep()
    if stop:
        click.secho('Restart upyHome', fg='yellow')
        if shell.upyhone_exec('start'):
            click.secho('Upyhonme is started', fg='green')
    shell.end()

@cli.command()
@click.option('--config', type=click.STRING, prompt="Enter device config", required=True, callback=check_config)
@click.option('--skip/--no-skip', default=False, required=False)
def sync(config, skip):
    """
    Upload the upyhome files.
    """
    click.secho('Sync files', fg='magenta')
    _conf = Config(config)
    check_port(_conf)
    shell = Shell(_conf, stop=True)
    error = shell.sync_time()
    if error:
        click.secho('Failed to sync time, abort!', fg='red')
        return
    click.secho('Sync time done! checking file system', fg='green')
    shell.mkdirs()
    click.secho('Compute file operations', fg=COLOR_ACTION)
    files = shell.sync_files(_conf)
    if skip:
        files = list(filter(lambda file: file[0] not in ['config.json', 'webrepl_cfg.py'] , files))
    print_sep()
    click.secho(tabulate(files, ['file', 'operatiom', 'date'], 'github'), fg='bright_cyan')
    print_sep()
    
    if click.confirm('Continue'):
        for file in files:
            if(file[1] == 'update' or file[1] == 'add'):
                click.secho('Copy file %s'%(file[0]), fg=COLOR_ACTION)
                shell.copy_file(file[0])
            elif(file[1] == 'delete'):
                click.secho('Delete file %s'%(file[0]), fg=COLOR_ACTION)
                shell.rm_file(file[0])
        if not skip:
            click.secho('Compile config', fg=COLOR_ACTION)
            conf_files = _conf.write_json_conf()
            multiple = len(conf_files) > 1
            selected_conf = None
            if multiple:
                selected_conf = ask_sync(conf_files)
            else:
                selected_conf = conf_files[0]
            shell.copy_file(selected_conf+'.json', src_dir=_conf.get_generated_path(), dest_name="config.json")
            #repl
            repl = _conf.get_repl_config()
            if repl is not None:
                click.secho('Copy REPL config', fg=COLOR_ACTION)
                data = 'PASS = "%s"\n'%(repl)
                shell.copy_data(data, 'webrepl_cfg.py')
            


    if click.confirm('Soft reset'):
        shell.soft_reset()
    elif stop:
        click.secho('Restart upyHome', fg=COLOR_ADVERT)
        if shell.upyhone_exec('start'):
            click.secho('Upyhonme is started', fg=COLOR_INFO)
    else:
        shell.end()
    click.secho('Sync done!', fg=COLOR_INFO)

@cli.command()
@click.option('--config', type=click.STRING, prompt="Enter device config", required=True, callback=check_config)
def stop(config):
    """
    Stop upyhome on the device.
    """
    click.secho('Stop upyhome', fg=COLOR_INFO)
    _conf = Config(config)
    shell = Shell(_conf, stop=True)
    shell.end()

@cli.command()
@click.option('--config', type=click.STRING, prompt="Enter device config", required=True, callback=check_config)
def start(config):
    """
    Start upyhome on the device.
    """
    click.secho('Start upyhome', fg=COLOR_INFO)
    _conf = Config(config)
    shell = Shell(_conf)
    if shell.is_upyhone():
        click.secho('Upyhonme detected... start', fg=COLOR_ACTION)
        if shell.upyhone_exec('start'):
            click.secho('Upyhonme is started', fg=COLOR_RESULT)
    else:
        click.secho('Upyhonme not detected, nothing to do', fg=COLOR_ADVERT)
    shell.end()

@cli.command()
@click.option('--config', type=click.STRING, prompt="Enter device", required=True, callback=check_config)
@click.option('--function', type=click.STRING, prompt="Enter function", required=True)
@click.option('--topic', type=click.STRING, prompt="Enter topic", required=False, default=None)
def exec(config, function, topic):
    """
    Execute a task on the device.
    """
    click.secho('Execute a command', fg='magenta')
    _conf = Config(config)
    shell = Shell(_conf)
    had_stopped = False

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
    """
    Display a file in the device.
    """
    click.secho('Open file', fg=COLOR_INFO)
    _conf = Config(config)
    shell = Shell(_conf, stop=True)
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
    print_sep()
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
    print_sep()
    if had_stopped:
        click.secho('Restart upyHome', fg=COLOR_ACTION)
        if shell.upyhone_exec('start'):
            click.secho('Upyhonme is started', fg=COLOR_RESULT)
    shell.end()

@cli.command()
@click.option('--config', type=click.STRING, prompt="Enter device config", required=True, callback=check_config)
def restart(config):
    """
    Monitor upyhome on the device.
    """
    click.secho('Restart upyhome', fg=COLOR_INFO)
    _conf = Config(config)
    shell = Shell(_conf)
    click.secho('Soft reset', fg=COLOR_ACTION) 
    shell.soft_reset()

@cli.command()
@click.option('--config', type=click.STRING, prompt="Enter device config", required=True, callback=check_config)
def monitor(config):
    """
    Monitor upyhome on the device.
    """

    click.secho('Restart upyhome', fg=COLOR_INFO)
    _conf = Config(config)
    shell = Shell(_conf)
    shell.upyhone_exec('mute', data=False)
    click.secho("Start monitoring, press CTRL-C to quit", fg=COLOR_ADVERT)
    p = re.compile('^#(.*)=\\[(.*)\\]')
    print_sep()
    while True:
        try:
            data = shell.pyboard.serial.readline().decode('utf8')
            m = p.match(data)
            if m:
                grps = m.groups()
                if(len(grps) == 2):
                    click.secho('Topic:', fg=COLOR_SRC, nl=False)
                    click.secho('%06s'%(grps[0]), fg=COLOR_COMMENT, nl=False)
                    click.secho(' -> ', fg=COLOR_INFO, nl=False)
                    click.secho(grps[1], fg=COLOR_ACTION)
        except KeyboardInterrupt:
            break
    print_sep()
    shell.end()

@cli.command()
@click.option('--config', type=click.STRING, prompt="Enter device config", required=True, callback=check_config)
def test(config):
    """
    Test
    """
    click.secho('Start upyhome', fg=COLOR_INFO)
    click.get_current_context()
    _conf = Config(config)
    shell = Shell(_conf)
    if not shell.is_upyhone():
        click.secho('Upyhonme not detected, nothing to do', fg=COLOR_ERROR)
    else:
        click.secho('Upyhonme not detected, nothing to do', fg=COLOR_ACTION)
    shell.end()

if __name__ == '__main__':
    cli()