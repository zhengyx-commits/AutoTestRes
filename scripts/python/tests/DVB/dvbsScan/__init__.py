#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/26 上午9:54
# @Author  : yongbo.shao
# @File    : __init__.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm

from lib.common.system.ADB import ADB
import os
from tools.yamlTool import yamlTool

config_yaml = yamlTool(os.getcwd() + '/config/config_dvb.yaml')

adb = ADB()
APK = "testSuspend2.apk"


def install_suspend_apk():
    adb.res_manager.get_target(f'apk/{APK}')
    adb.install_apk("apk/" + APK)
