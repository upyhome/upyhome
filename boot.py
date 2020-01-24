import webrepl
import upyhome
import micropython
import gc

gc.enable()
micropython.alloc_emergency_exception_buf(100)
upyhome.connect()
gc.collect()
webrepl.start()
gc.collect()


