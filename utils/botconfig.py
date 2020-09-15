import configparser
import os

config_file = 'settings.ini'


def init_config():
    config = configparser.ConfigParser()
    if not os.path.isfile(config_file):
        config['Settings'] = {'TargetFolder': './',
                              'TempFolder': './temp',
                              'FilePermissions': '744',
                              'TokenFile': 'token.cfg'}
        config['Repos'] = {}
        with open(config_file, 'w') as configfile:
            config.write(configfile)
    else:
        config.read(config_file)

    return config
