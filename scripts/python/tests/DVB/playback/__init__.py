#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/26 上午9:54
# @Author  : yongbo.shao
# @File    : __init__.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
import logging
from lib.common.system.ADB import ADB
import os
from tools.yamlTool import yamlTool

config_yaml = yamlTool(os.getcwd() + '/config/config_dvb.yaml')

adb = ADB()
android_version = adb.getprop(key="ro.build.version.release")
logging.debug(f"android version: {android_version}")
if android_version == '14':
    APK = "testSuspend2_U.apk"
else:
    APK = "testSuspend2.apk"


def install_suspend_apk():
    adb.res_manager.get_target(f'apk/{APK}')
    adb.install_apk("apk/" + APK)
