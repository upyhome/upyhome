
#import yaml
#import json
import os

import time
now = time.localtime(time.time())
t_tuple = now.__reduce__()[1][0]
print(t_tuple)

print([ i for i in range(2) ])

ip = '{0}.{1}.{2}.{3}'.format(*tuple([255 for i in range(4)]))
print(ip)