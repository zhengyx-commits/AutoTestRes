#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/6/28
# @Author  : kejun.chen
# @File    : __init__.py
# @Email   : kejun.chen@amlogic.com
# @Software: PyCharm
import logging
import os
import time
from lib.common.system.ADB import ADB
from lib import get_device
from tools.resManager import ResManager

repeat_count = int()


class PreOperation:

    def setprop(self, device_id):
        logging.info('set prop.')
        # adb.run_shell_cmd("setprop vendor.tv.dtvkit.time.trace.flag true")
        # adb.run_shell_cmd("echo 1 > /proc/sys/kernel/printk")
        os.system('adb -s ' + device_id + " shell " + 'setprop vendor.tv.dtvkit.time.trace.flag true')
        os.system('adb -s ' + device_id + " shell " + 'echo 1 > /proc/sys/kernel/printk')

    def push_patch(self, device_id):
        android_version = adb.getprop(key="ro.build.version.release")
        logging.info(f"android version: {android_version}")
        if android_version == '14':
            logging.info('Android U does not need to push patch.')
        else:
            logging.info('start push patch.')
            os.system('adb -s ' + device_id + " root")
            os.system('adb -s ' + device_id + " remount")
            res.get_target('DVBKPI/dtvkitserver')
            # adb.push(f"{os.getcwd()}/res/DVBKPI/dtvkitserver",
            #          PATCH_PATH)
            os.system('adb -s ' + device_id +
                      " push " + f"{os.getcwd()}/res/DVBKPI/dtvkitserver" + " " + PATCH_PATH)
            # adb.reboot()
            os.system('adb -s ' + device_id + " reboot")
            time.sleep(60)
            # adb.root()
            # adb.remount()
            os.system('adb -s ' + device_id + " root")
            os.system('adb -s ' + device_id + " remount")


preOperation = PreOperation()
res = ResManager()
adb = ADB()

PATCH_PATH = '/vendor/bin/hw'
for serialnumber in get_device():
    preOperation.push_patch(serialnumber)
    preOperation.setprop(serialnumber)

