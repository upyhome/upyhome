
import uos
import uio
import ubinascii
import utime as time
import upyhome
import gc

dins = upyhome.inputs()
douts = upyhome.outputs()
gc.collect()

def ping( info = False):
    if not info:
        print('#pong')
    gc.collect()

def dout_status():
    for key in douts.keys():
        time.sleep_ms(10)
        douts[key].print_status()
    gc.collect()

def list_dir(directory = '.'):
    res = '#dir:' + directory + '=[null'
    files = uos.ilistdir(directory)
    for file in files:
        #print(file)
        if(file[1] == 32768):
            res += ","
            res += file[0]
    res += ']'
    print(res)
    gc.collect()

def read_file(file):
    fileToRead = uio.open(file)
    content = fileToRead.read()
    res = '#file:' + file + '=['
    res += content.replace('\n', '<BR>')
    res += ']'
    fileToRead.close()
    print(res)
    gc.collect()
