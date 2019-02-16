import configparser as co

config = None


class myconfig(co.ConfigParser):
    def __init__(self, defaults=None):
        co.ConfigParser.__init__(self, defaults=defaults)

    def optionxform(self, optionstr):
        return optionstr


def init():
    global config
    config = myconfig()
    config.read('config.ini')
    chose('default')

def chose(sec):
    global config
    if sec not in config.sections():
        raise Exception('不存在的配置项')
    temp = {}
    for (a, b) in config.items(sec):
        temp[a] = b
    config = temp
