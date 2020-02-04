

class SampleGen:
    def __init__(self, args=None):
        print('Sample generator demo')
        print('constructor args: %s'%(args))
        self.named_values=['first', 'second', 'third' ]
    
    def get_name(self, item):
        i = int(item)
        if i < len(self.named_values):
            return self.named_values[i]
        else:
            return 'out_of_range'

    def get_ip(self, item):
        return '192.168.0.%d'%(int(item+10))