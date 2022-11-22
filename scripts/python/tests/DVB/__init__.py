#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/6/28
# @Author  : kejun.chen
# @File    : __init__.py
# @Email   : kejun.chen@amlogic.com
# @Software: PyCharm

import os
from tools.yamlTool import yamlTool

config_yaml = yamlTool(os.getcwd() + '/config/config_dvb.yaml')
