#this is a test


def test():
    import ujson as json
    cf = open('config.json', 'r')
    config_data = json.load(cf)
    cf.close()
    print(config_data['network']['ssid'])
    print(config_data['network']['wifi_pwd'])
