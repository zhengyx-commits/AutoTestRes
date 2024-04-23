#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/4/9 下午2:05
# @Author  : yongbo.shao
# @File    : __init__.py.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
from lib.common.system.Bluetooth import Bluetooth
import logging
import time

btTest = Bluetooth()


def init_test_env():
    if not btTest.check_apk_exist(btTest.BLUETOOTH_PACKAGE):
        btTest.uiautomator_dump()
        logging.info('Apk not exists')
        btTest.res_manager.get_target(btTest.BLUETOOTH_APK_PATH)
        btTest.install_apk(btTest.BLUETOOTH_APK_PATH)
        time.sleep(3)
        btTest.check_permission()
    btTest.init_logcat_config()
    btTest.clear_connected()
    btTest.app_stop(btTest.BLUETOOTH_PACKAGE)
    time.sleep(1)