from ili9341 import ili9341

class M5ili9341(ili9341):
    def __init__(
            self, mosi=23, miso=19, clk=18, cs=14, dc=27, rst=33, backlight=32,
            backlight_on=1, hybrid=True, width=320, height=240,
            colormode=0x08, rot=0x10, invert=True, **kwargs):
        super().__init__(
            mosi=mosi, miso=miso, clk=clk, cs=cs, dc=dc, rst=rst,
            backlight=backlight, backlight_on=backlight_on, hybrid=hybrid,
            width=width, height=height, colormode=colormode, rot=rot,
            invert=False, **kwargs)
        if invert:
            # Invert colors (work around issue with `invert` kwarg in stock
            # class).
            self.send_cmd(0x21)
