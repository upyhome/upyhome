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
import copy
import click
import json
from serial.tools import list_ports
import shutil
import glob
import os
from pathlib import Path
import json
from ruamel.yaml import YAML
import stringcase
yaml=YAML()
yaml.indent(sequence=4, offset=2) 
from upyhome.const import CONFIG_NAME, CONFIG_PLATFORM, CONFIG_DRIVER, CONFIG_USER
from upyhome.const import CONFIG_NETWORK, CONFIG_LIST_NETWORKS, CONFIG_FILE
from upyhome.const import SETTING_PORT, SETTING_SECTION, SETTING_FIRMWARE, SETTING_GENERATOR, SETTING_UPLOAD
from upyhome.const import CONFIG_USER_CODE, CONFIG_REPL
from upyhome.const import DEVICE_DIR, BOARD_DIR, NETWORK_DIR, GENERATOR_DIR, CONFIG_LIST_DIR, LIB_DIR
from upyhome.const import MICROPYTHON_DIR, MICROPYTHON_FILES, MICROPYTHON_LIBS

path_join = os.path.join
sys.path.append(path_join('.', GENERATOR_DIR))

def write_network_conf(name, ssid, pwd):
    net_conf_dir = path_join('.', NETWORK_DIR)
    if not os.path.exists(net_conf_dir):
        os.mkdir(net_conf_dir)
    data = {'ssid': ssid, 'pwd': pwd}
    with open(path_join(net_conf_dir, '%s.yaml'%(name)), 'w') as outfile:
        yaml.dump(data, outfile)

def ensure_paths():
    for path in [DEVICE_DIR, NETWORK_DIR]:
        dir = path_join('.', path)
        if not os.path.exists(dir):
            os.mkdir(dir)

def get_config_file(name):
    return path_join('.', DEVICE_DIR, '%s.yaml'%(name))

def get_config_list():
    config_blob = path_join('.', DEVICE_DIR, '*.yaml')
    return [os.path.splitext(os.path.basename(f))[0] for f in glob.glob(config_blob)] 


def get_config_obj(name):
    """
    Load the config object
    """
    confile_path = Path(get_config_file(name))
    config_obj = yaml.load(confile_path)
    config_obj[CONFIG_NAME] = name
    return config_obj

def save_config_obj(conf_obj):
    """
    Save the config object
    """
    confile_path = Path(get_config_file(conf_obj[CONFIG_NAME] ))
    return yaml.dump(conf_obj, confile_path)

def handle_conf(conf):
    """
    The conf can be the config name or the config object
    """
    is_obj = type(conf) is not str
    if not is_obj:
        return get_config_obj(conf)
    else:
        return conf

def get_config_dir(conf):
    """
    """
    config_obj = handle_conf(conf)
    return path_join('.', DEVICE_DIR, config_obj[CONFIG_NAME] )

def set_setting_val(conf, key, val):
    """
    Set the config key value
    """
    config_obj = handle_conf(conf)
    if SETTING_SECTION not in config_obj:
        config_obj[SETTING_SECTION] = {}
    config_obj[SETTING_SECTION][key] = val

def is_setting_val(conf, key):
    """
    Check if the key is in the config part
    The conf can be the config name or the config object
    """
    config_obj = handle_conf(conf)
    if SETTING_SECTION in config_obj and key in config_obj[SETTING_SECTION]:
        return config_obj[SETTING_SECTION][key] is not None 
    return False

def get_setting_val(config_obj, key):
    """
    Get the config key value
    """
    if SETTING_SECTION in config_obj and key in config_obj[SETTING_SECTION]:
        return config_obj[SETTING_SECTION][key]
    return None

def set_config_val(conf, key, val):
    """
    Set the config key value
    """
    config_obj = handle_conf(conf)
    config_obj[key] = val

def is_config_val(conf, key):
    """
    Check if the key is in the config part
    The conf can be the config name or the config object
    """
    config_obj = handle_conf(conf)
    return key in config_obj

def get_config_val(config_obj, key):
    """
    Get the config key value
    """
    if key in config_obj:
        return config_obj[key]
    return None


def get_net_conf(net_conf):
    """
    Attach the network in the config obj
    """
    # TODO: check instance, handle errors
    #if not isinstance(object, ):
    #    return
    if net_conf[CONFIG_LIST_NETWORKS]:
        wifis = net_conf[CONFIG_LIST_NETWORKS]
    else:
        return
    for net in wifis:
        if CONFIG_FILE in net:
            if net[CONFIG_FILE].startswith('$'):
                net_file = path_join('.', NETWORK_DIR,'%s.yaml'%(net[CONFIG_FILE][1:]))
                if os.path.exists(net_file):
                    net_obj = yaml.load(Path(net_file))
                    for k, v in net_obj.items():
                        net[k] = v
            del net[CONFIG_FILE]
        
def get_user_file(user_conf):
    """
    Attach the network to config obj
    """
    user_file = path_join('.', DEVICE_DIR, '%s.py'%(user_conf))
    if os.path.exists(user_file):
        with open(user_file, 'r') as file_in:
            data = file_in.read()
        return data
    return None

def attach_conf_links(conf):
    """
    Attach links to the conf
    networks, user defined
    """
    config_obj = handle_conf(conf)
    # networks
    if is_config_val(conf, CONFIG_NETWORK):
        get_net_conf(config_obj[CONFIG_NETWORK])
    # user code
    if is_config_val(conf, CONFIG_USER):
        user_conf = get_config_val(conf, CONFIG_USER)
        if(user_conf.startswith('$')):
            config_obj[CONFIG_USER] = get_user_file(user_conf[1:])
        if config_obj[CONFIG_USER] is None:
            del config_obj[CONFIG_USER]
    # supress upyhome section
    if config_obj[SETTING_SECTION] is not None:
        del config_obj[SETTING_SECTION]
    return conf

def traverse_keys(obj, gen_instance, item):
    """
    Traverse all dict and generate values
    """
    for k, v in obj.items():
        if isinstance(v, (list, set)):
            for e in v:
                traverse_keys(e, gen_instance, item)
        elif isinstance(v, (dict)):
            traverse_keys(v, gen_instance, item)
        elif isinstance(v, str):
            if v.startswith('$$') and hasattr(gen_instance, v[2:]):
                func = getattr(gen_instance, v[2:])
                computed = func(item)
                obj[k] = computed
                print('changed val')    

def create_sub_conf(conf, gen_instance, item):
    """
    create a conf with a generator instance
    """
    conf_copy = copy.deepcopy(conf)
    traverse_keys(conf_copy, gen_instance, item)
    return conf_copy

def get_config_set(conf, module, list, opts= None):
    """
    get generated class list
    """
    configs = []
    class_name = stringcase.pascalcase(module)
    module = __import__(module)
    class_ = getattr(module, class_name)
    instance = class_(opts)
    for item in list:
        configs.append(create_sub_conf(conf, instance, item))
    return configs

def rm_dir(path):
    """
    Remove recursively a dir with symlinks
    """
    if os.path.exists(path) and os.path.isdir(path):
        for f in os.listdir(path):
            child = path_join(path, f)
            if os.path.isdir(child):
                rm_dir(child)
            elif os.path.islink(child):
                os.unlink(child)
            elif os.path.isfile(child):
                os.remove(child)
        os.rmdir(path)

def copy_base(conf, libs, drivers=[]):
    """
    Copy base dir
    """
    #all dirs, remove
    # TODO Must raise errors
    if(isinstance(conf, list)):
        if len(conf) > 0:
            name = conf[0][CONFIG_NAME]
        else:
            return
    else:
        name = conf[CONFIG_NAME]
    base_dir = path_join('.', DEVICE_DIR, name)
    rm_dir(base_dir)

    lib_dir = path_join(base_dir, 'lib')
    driver_dir = path_join(base_dir, 'driver')
    conf_dir = path_join(base_dir, CONFIG_LIST_DIR)
    # create
    for target_dir in [lib_dir, driver_dir, conf_dir]:
        os.makedirs(target_dir)
    # copy micropython files    
    for m_file in MICROPYTHON_FILES:
        src = path_join(MICROPYTHON_DIR, m_file)
        dest = path_join(base_dir, m_file)
        shutil.copy2(src, dest)
        #os.symlink(src, dest)
    for lib in libs:
        src = path_join(MICROPYTHON_DIR, 'lib', lib)
        dest = path_join(lib_dir, lib)
        shutil.copy2(src, dest)
        #os.symlink(src, dest)
    for driver in drivers:
        # get in the appropriate dir
        src = path_join(MICROPYTHON_DIR, 'drivers', driver)
        dest = path_join(driver_dir, driver)
        if not os.path.exists(src):
            src = path_join(DEVICE_DIR, 'drivers', driver)
        if os.path.exists(src):
            shutil.copy2(src, dest)
            #os.symlink(src, dest)
    if isinstance(conf, dict):
        conf_path = path_join(base_dir, 'config.json')
        write_json_conf(conf, conf_path)
    else:
        for i, c in enumerate(conf):
            conf_path = path_join(conf_dir, 'config-%d.json'%(i))
            write_json_conf(c, conf_path)

def get_generator_list(val):
    """
    TODO Raise Exception
    """
    if isinstance(val, str):
        g_list = eval(val)
        #if not isinstance(val, list):
        #    return None
    elif isinstance(val, list):
        g_list = val
    return g_list

def get_generator_names(conf):
    """
    """
    names = []
    generator = get_setting_val(conf, SETTING_GENERATOR)
    g_iter = generator['list']
    g_list = get_generator_list(g_iter)
    g_class = generator['module']
    g_opts = None
    if 'opts' in generator:
        g_opts = generator['opts']
    class_name = stringcase.pascalcase(g_class)
    module = __import__(g_class)
    class_ = getattr(module, class_name)
    instance = class_(g_opts)
    for item in g_list:
        func = getattr(instance, 'get_name')
        names.append(func(item))
    return names

def compile_conf_files(conf):
    """
    """ 
    if is_setting_val(conf, SETTING_GENERATOR):
        generator = get_setting_val(conf, SETTING_GENERATOR)
        g_iter = generator['list']
        g_list = get_generator_list(g_iter)
        g_class = generator['module']
        g_opts = None
        if 'opts' in generator:
            g_opts = generator['opts']
        g_res = get_config_set(conf, g_class, g_list, g_opts)
        generated = []
        for g in g_res:
            generated.append(attach_conf_links(g))
    else:
        generated = attach_conf_links(conf)
    return generated

def create_lib_list(conf, save=False):
    """
    create the list of files to copy
    """
    platform = get_config_val(conf, CONFIG_PLATFORM)
    files = MICROPYTHON_FILES
    files += [ path_join('lib', name) for name in MICROPYTHON_LIBS['common']['all'] ]

    for key, val in MICROPYTHON_LIBS.items():
        if key=='common':
            continue
        if not val:
            continue
        if key in conf and conf[key]:
            if 'all' in val:
                files += [ path_join('lib', name)  for name in val['all'] ]
            if platform in val:
                files += [ path_join('lib', name)  for name in val[platform] ]
    
    # Driver specific
    drivers = get_config_val(conf, CONFIG_DRIVER)
    if drivers:
        for drv in drivers:
            if drv[CONFIG_NAME]:
                files += [ path_join('drivers', name+'.py')  for name in drv[CONFIG_NAME] ]
    if save:
        set_setting_val(conf, SETTING_UPLOAD, files)
        save_config_obj(conf)
    return files

def get_repl_config(conf):
    """
    """
    net = get_config_val(conf, CONFIG_NETWORK)
    if net is None:
        return None
    return get_config_val(net, CONFIG_REPL)

def write_json_conf(conf, file):
    """
    write conf to json
    """
    with open(file, 'w') as f:
        json.dump(conf, f)
"""
Test
"""
if __name__ == '__main__':
    print(os.getcwd())
    name = 'd1'
    conf_obj = get_config_obj(name)
    conf_file = compile_conf_files(conf_obj)
    write_json_conf(conf_file, os.path.join(DEVICE_DIR, 'config.json'))
