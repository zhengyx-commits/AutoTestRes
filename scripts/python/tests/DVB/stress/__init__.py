#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/18 下午5:00
# @Author  : yongbo.shao
# @File    : __init__.py.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
import os
from tools.yamlTool import yamlTool

config_yaml = yamlTool(os.getcwd() + '/config/config_dvb.yaml')