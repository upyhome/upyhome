
#import yaml
#import json
import os

#os.symlink('./devices/test.yaml', 'test-sym.yaml')
#
#import yaml
#
#def yaml_include(loader, node):
#    with file(node.value) as inputfile:
#        return yaml.load(inputfile)
#
#yaml.add_constructor("!include", yaml_include)
#
#print(os.getcwd())
#with open("test.yaml", 'r') as yaml_in, open("test.json", "w") as json_out:
#    yaml_object = yaml.safe_load(yaml_in) # yaml_object will be a list or a dict
#    json.dump(yaml_object, json_out)

#import re
#for string in ["aaa", "dsd-dwdw", "dsd dwdwdwd"]:
#    print(re.match("^[a-zA-Z0-9-_.]{3,}$", string) is not None)

#import rshell.main as rshell_main
#
#import sys
#print(sys.argv)
#sys.argv.clear()
#print(sys.argv)
#sys.argv.extend(['rshell', '--port', '/dev/cu.usbserial-AH030NYK', 'ls /pyboard'])
#print(sys.argv)
#res = rshell_main.main()
#print(sys.argv)
#print(res)

import time
now = time.localtime(time.time())
t_tuple = now.__reduce__()[1][0]
print(t_tuple)