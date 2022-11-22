#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/7/11 14:25
# @Author  : chao.li
# @Site    :
# @File    : __init__.py
# @Software: PyCharm

import pytest
import os
from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.checkpoint.PlayerCheck import PlayerCheck
from tools.yamlTool import yamlTool

dvb_stream = DVBStreamProvider()
dvb = DVB()
dvb_check = DvbCheck()
playerCheck = PlayerCheck()
config_yaml = yamlTool(os.getcwd() + '/config/config_dvb.yaml')