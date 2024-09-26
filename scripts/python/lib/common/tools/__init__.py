#########################################################
#将根目录加入sys.path中,解决命令行找不到包的问题
import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)
#########################################################

from tools.yamlTool import yamlTool


def config_yaml():
    config_yaml = yamlTool(os.getcwd() + "/config/config_common.yaml")
    return config_yaml