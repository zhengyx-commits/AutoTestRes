#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/8/4
# @Author  : kejun.chen
# @Site    :
# @File    : __init__.py.PY
# @Email   : kejun.chen@amlogic.com
# @Software: PyCharm
import os
from tools.yamlTool import yamlTool

config_yaml = yamlTool(os.getcwd() + '/config/config_dvb.yaml')