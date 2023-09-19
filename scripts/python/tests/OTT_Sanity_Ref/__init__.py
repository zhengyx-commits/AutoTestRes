import os

from lib.common.system.NetworkAuxiliary import getIfconfig
from tools.yamlTool import yamlTool

config_yaml = yamlTool(os.getcwd() + '/config/config_ott_sanity.yaml')


def is_sz_server():
    device_ip_sz = "10.28.9.62"
    iplist = getIfconfig()
    if device_ip_sz in iplist:
        return True
    else:
        return False
