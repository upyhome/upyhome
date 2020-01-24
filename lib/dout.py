from machine import Pin

class DigitalOutputPin:

    def __init__(self, h_pin, name, inverted=False):
        self.name = name
        self.pin = Pin(h_pin, Pin.OUT)
        self.inverted = inverted

    def on(self):
        if self.inverted:
            self.pin.off()
        else:
            self.pin.on()
        print('#do:{}=[1]'.format(self.name))

    def off(self):
        if self.inverted:
            self.pin.on()
        else:
            self.pin.off()
        print('#do:{}=[0]'.format(self.name))

    def state(self):
        if self.inverted:
            return True if self.pin.value() == 0 else False
        else:
            return True if self.pin.value() == 1 else False

    def toggle(self):
        if self.state():
            self.off()
        else:
            self.on()

    def print_status(self):
        print('#do:{}=[{}]'.format(self.name, int(self.state())))