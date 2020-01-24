from machine import Pin
from machine import Timer


"""
Input helper.
It manages two kinds of signal
    - When it's pressed, trigger is when it's releases
    - When it's long pressed, trigger along press 
"""

class DigitalInputPin:

    """
    Construct an input
    """
    def __init__(self, h_pin, name, inverted=False, debounce=100, long=1000):

        self.name = name
        self.inv = inverted
        self.dbc_t = debounce
        self.long_t = long
        self.pin = Pin(h_pin, Pin.IN, Pin.PULL_UP)
        self.dbc_tim = Timer(-1)
        self.user_cb = None;
        self.i_val = self.pin.value()
        self.pressed = False
        self.supp = False
        self.pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.irq_cb)

    def set_callback(self, user_cb):
        self.user_cb = user_cb;

    """
    This callback is call when the hardware input interrupts
    This is where the debounce timer is handled
    """
    def irq_cb(self, pin):
        # Once it comes we can cancel every timers previously launched
        self.dbc_tim.deinit()
        # Set the initial value
        self.i_val = pin.value()
        # Pressed or released according if input is inverted
        self.pressed = (self.inv and not self.i_val) or (not self.inv and self.i_val)
        # The debounce timer is launched here...
        self.dbc_tim.init(period=self.dbc_t, mode=Timer.ONE_SHOT, callback=self.dbc_cb)

    def long_cb(self, tim):

        if self.pin.value() == self.i_val:
            self.supp = True
            print('#di:{}=[L]'.format(self.name))
            if self.user_cb is not None:
                self.user_cb('L')

    def dbc_cb(self, tim):

        if self.pressed:
            if self.pin.value() == self.i_val:
                if not self.supp:
                    print('#di:{}=[C]'.format(self.name))
                    if self.user_cb is not None:
                        self.user_cb('C')
        else:
            if self.pin.value() == self.i_val:
                print('#di:{}=[P]'.format(self.name))
                if self.user_cb is not None:
                    self.user_cb('P')
                self.dbc_tim.init(period=self.long_t, mode=Timer.ONE_SHOT, callback=self.long_cb)
        self.supp = False
