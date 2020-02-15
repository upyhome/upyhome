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

# TODO Make a conf class

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
    if CONFIG_NAME not in config_obj:
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

class Generator:
    def __init__(self, obj: dict, base_name: str):
        try:
            self._iterator = [None]
            self._functions = {}
            if obj is not None:
                iterator = obj['list']
                if isinstance(iterator, str):
                    self._iterator = eval(iterator)
                elif isinstance(iterator, list):
                    self._iterator = iterator
                else:
                    raise Exception('Malformed generator list {0}'.format(iterator))
                if 'module' in obj:
                    self._module = obj['module']
                    self._args = { 'base_name': base_name }
                    if 'args' in obj:
                        self._args.update(obj['args'])
                    class_name = stringcase.pascalcase(self._module)
                    module = __import__(self._module)
                    _class = getattr(module, class_name)
                    self._instance = _class(self._args)                
                    class_objs = dir(self._instance)
                    self._functions = {}
                    for c_obj in class_objs:
                        attr = getattr(self._instance, c_obj)
                        if not c_obj.startswith('_') and callable(attr):
                            self._functions[c_obj] = attr
        except Exception as ex:
            pass

    def iterator(self) -> list:
        return self._iterator
    
    def file_name(self, index, item, prefix='config'):
        n_func = self._functions['file_name'] if 'file_name' in self._functions else None
        return n_func(index, item) if n_func is not None else '{0}-{1}'.format(prefix, index)

    def value(self, index, item, expr: str) -> str:
        if expr in self._functions:
            return self._functions[expr](index, item)
        else:
            return eval(expr, { 'index':index, 'item': item})

    def is_generated(self, val: str) -> bool:
        return val in self._functions

class Config:
    def __init__(self, name):
        self._name = name
        self._conf = handle_conf(name)

    def set_setting_val(self, key, val):
        """
        Set the config key value
        """
        if SETTING_SECTION not in self._conf:
            self._conf[SETTING_SECTION] = {}
        self._conf[SETTING_SECTION][key] = val

    def is_setting_val(self, key):
        """
        Check if the key is in the config part
        The conf can be the config name or the config object
        """
        if SETTING_SECTION in self._conf and key in self._conf[SETTING_SECTION]:
            return self._conf[SETTING_SECTION][key] is not None 
        return False

    def get_setting_val(self, key):
        """
        Get the config key value
        """
        if SETTING_SECTION in self._conf and key in self._conf[SETTING_SECTION]:
            return self._conf[SETTING_SECTION][key]
        return None

    def set_config_val(self, key, val):
        """
        Set the config key value
        """
        self._conf[key] = val

    def is_config_val(self, key):
        """
        Check if the key is in the config part
        The conf can be the config name or the config object
        """
        return key in self._conf

    def get_config_val(self, key):
        """
        Get the config key value
        """
        if key in self._conf:
            return self._conf[key]
        return None

    def parse_value(self, v, index, item, generator: Generator):
        if v.startswith('$$'):
            return generator.value(index, item, v[2:])
        else: 
            return v

    def traverse_keys(self, obj, index, item, gen_instance : Generator = None):
        """
        Traverse all dict and link values or generate values
        The config have to be traversed two times.
        First for linked values, second for generated values.
        So we can link generated values
        """
        append = {}
        delete = []
        for k, v in obj.items():
            if isinstance(v, (list, set)):
                for i, e in enumerate(v):
                    if isinstance(e, dict):
                        self.traverse_keys(e, index, gen_instance, item)
                    elif isinstance(e, str):
                        v[i] = self.parse_value(e, index, item, gen_instance)
            elif isinstance(v, (dict)):
                self.traverse_keys(v, index, gen_instance, item)
            elif isinstance(v, str):
                if v.startswith('$') and not v.startswith('$$'):
                    # First iteration, lookup for linked values
                    # check if the link is a generated value
                    link = v[1:]
                    if gen_instance.is_generated(link):
                        link = gen_instance.value(index, item, link)
                    # look for the linked file in network or generator dir
                    link_file = None
                    for dir in [NETWORK_DIR, GENERATOR_DIR]:
                        f = path_join(dir, '%s.yaml'%(link))
                        if os.path.exists(f):
                            link_file = f
                    if link_file is None:
                        raise Exception('The linked config does not exists %s'%(v))
                    pass
                    #load the file and add to modif list
                    append.update(yaml.load(Path(link_file)))
                    delete.append(k)
                else:
                    new_val = self.parse_value(v, index, item, gen_instance)
                    obj[k] = new_val
        if len(append)>0:
            obj.update(append)
            for k in delete:
                del obj[k]
            self.traverse_keys(obj, index, item, gen_instance)

    def compile_conf_files(self) -> dict:
        """
        """ 
        res = {}
        generator = Generator(self.get_setting_val(SETTING_GENERATOR), self._name)
        for i, item in enumerate(generator.iterator()):
            copy_conf = copy.deepcopy(self._conf)
            del copy_conf[SETTING_SECTION]
            self.traverse_keys(copy_conf, i, item, generator)
            res[generator.file_name(i, item)] = copy_conf            
        return res

    def get_generated_path(self):
        return path_join(DEVICE_DIR, '.'+self._name)

    def write_json_conf(self)->list:
        """
        Write conf to json, return the list of generated files
        """
        conf_dir = self.get_generated_path()
        rm_dir(conf_dir)
        os.makedirs(conf_dir, exist_ok=True)
        generated = self.compile_conf_files()
        for f_name, conf in generated.items():
            file_name = path_join(conf_dir, '%s.json'%(f_name))
            with open(file_name, 'w') as f:
                json.dump(conf, f, indent=2)
        return list(generated.keys())

    def save(self):
        confile_path = Path(get_config_file(self._name ))
        return yaml.dump(self._conf, confile_path)

    def create_lib_list(self, save=False):
        """
        create the list of files to copy
        """
        platform = self.get_config_val(CONFIG_PLATFORM)
        files = MICROPYTHON_FILES
        files += [ path_join('lib', name) for name in MICROPYTHON_LIBS['common']['all'] ]

        for key, val in MICROPYTHON_LIBS.items():
            if key=='common':
                continue
            if not val:
                continue
            if key in  self._conf and  self._conf[key]:
                if 'all' in val:
                    files += [ path_join('lib', name)  for name in val['all'] ]
                if platform in val:
                    files += [ path_join('lib', name)  for name in val[platform] ]
        
        # Driver specific
        drivers = self.get_config_val(CONFIG_DRIVER)
        if drivers:
            for drv in drivers:
                if drv[CONFIG_NAME]:
                    files += [ path_join('drivers', name+'.py')  for name in drv[CONFIG_NAME] ]
        if save:
            self.set_setting_val(SETTING_UPLOAD, files)
            save_config_obj(self._conf)
        return files

    def get_repl_config(self):
        """
        """
        net = self.get_config_val(CONFIG_NETWORK)
        if net is None:
            return None
        return self.get_config_val(CONFIG_REPL)



if __name__ == '__main__':
    """
    Test
    """
    print(os.getcwd())
    name = 'sample'
    conf = Config(name)
    files = conf.write_json_conf()
    print(files)
