

class SampleGenerator:
    def __init__(self, args=None):
        self.base_name = args['base_name']
        self._named_values=['%s_%02d'%(args['name'], n) for n in range(args['count']) ]
    
    def file_name(self, index, item):
        return self._named_values[index]

    def device_name(self, index, item):
        return '{0}-{1}'.format(index, self.base_name)

    def get_ip(self, index, item):
        return '192.168.0.%d'%(100 - index)

    def get_gateway_dns(self, index, item):
        return '192.168.0.1'

    def get_led_topics(self, index, item):
        return ['btn', 'sun', 'all_topics']

    def get_wifi_name(self, index, item):
        return 'generated-wifi'