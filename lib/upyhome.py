

def connect():

    import ujson
    import network
    import machine

    cf = open('config/credentials.json', 'r')
    cred = ujson.load(cf)
    cf.close()
    print(cred)
    wlan = network.WLAN(network.STA_IF)

    if not cred["use_dhcp"]:
        wlan.ifconfig((cred["ip"], cred["subnet"], cred["gateway"], cred["dns"]))
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(cred["ssid"], cred["wifi_pwd"])
        while not wlan.isconnected():
            machine.idle()
    print('network config:', wlan.ifconfig())

def inputs():
    import ujson
    import din
    res = {}
    cf = open('config/config.json', 'r')
    config = ujson.load(cf)
    cf.close()
    for input in config["digital-inputs"]:
        print(input)
        res[input["name"]] = din.DigitalInputPin(input["pin"], input["name"], input["inverted"])
    return res;

def outputs():
    import ujson
    import dout
    res = {}
    cf = open('config/config.json', 'r')
    config = ujson.load(cf)
    cf.close()
    for output in config["digital-outputs"]:
        print(output)
        res[output["name"]] = dout.DigitalOutputPin(output["pin"], output["name"], output["inverted"])
    return res;
