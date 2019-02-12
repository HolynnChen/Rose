import configparser as co
import toml

config = None


class myconfig(co.ConfigParser):
    def __init__(self, defaults=None):
        co.ConfigParser.__init__(self, defaults=defaults)

    def optionxform(self, optionstr):
        return optionstr


def init():
    global raw_config,config
    with open('config.ini') as f:
        raw_config=toml.load(f)
        config=raw_config['default']


