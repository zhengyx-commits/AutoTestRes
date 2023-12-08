#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/11/8
# @Author  : kejun.chen
# @File    : __init__.py.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import pytest
import os
from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.checkpoint.PlayerCheck_Base import PlayerCheck_Base
from tools.yamlTool import yamlTool

dvb_stream = DVBStreamProvider()
dvb = DVB()
dvb_check = DvbCheck()
playerCheck = PlayerCheck_Base()
config_yaml = yamlTool(os.getcwd() + '/config/config_dvb.yaml')