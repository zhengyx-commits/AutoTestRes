#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/9/5 09:56
# @Author  : chao.li
# @Site    :
# @File    : Bluetooth.py
# @Software: PyCharm
import logging
import os
import re
import time

import serial

from lib.common.system.ADB import ADB
from tools.yamlTool import yamlTool
from util.Decorators import set_timeout


class Bluetooth(ADB):
    OPEN_BLUETOOTH_COMMAND = 'svc bluetooth enable'
    CLOSE_BLUETOOTH_COMMAND = 'svc bluetooth disable'
    BLUETOOEH_APK = 'btConnect.apk'
    BLUETOOTH_PACKAGE = 'com.example.btconnect'
    BLUETOOTH_APK_PATH = 'apk/btConnect.apk'
    BLUETOOTH_ACTIVITY = 'am start -n com.example.btconnect/.MainActivity'
    BLUETOOTH_ACTIVITY_REGU = 'am start -n com.example.btconnect/.MainActivity {} {}'
    PARE_REGU = '-e pair'
    UNPARE_REGU = '-e unpair'
    LOGCAT_RELEATE_PATH = '/system/etc/bluetooth'
    DUMP_MANAGER_COMMAND = 'dumpsys bluetooth_manager'
    DUMP_STATUS_COMMAND = DUMP_MANAGER_COMMAND + ' |head -8'
    REMOTE_NAME = 'remote'
    SPEAKER_NAME = 'speaker'
    MOUSE_NAME = 'mouse'

    TARGET_INFO = {
        'remote': '54:03:84:2A:83:71',
        'speaker': 'D4:5E:EC:06:F0:D6',
        'mouse': 'F0:1D:BC:E5:28:08'
    }

    def __init__(self):
        ADB.__init__(self, 'Bluetooth')
        self.config_yaml = yamlTool(os.getcwd() + '/config/config_bluetooth.yaml')
        self.logcat_releate_file = self.res_manager.get_target('/bt/bt_stack.conf')

    def check_permission(self):
        '''
        check btConnect permission status,if not request it
        @return:
        '''
        self.checkoutput(self.BLUETOOTH_ACTIVITY)
        time.sleep(3)
        self.wait_and_tap('While using the app', 'text')
        self.wait_and_tap('Allow', 'text')
        time.sleep(1)
        self.app_stop(self.BLUETOOTH_PACKAGE)

    def init_logcat_config(self):
        '''
        push logcat releate config into target
        @return:
        '''
        self.root()
        self.remount()
        self.push(self.logcat_releate_file, self.LOGCAT_RELEATE_PATH)
        self.checkoutput(self.CLOSE_BLUETOOTH_COMMAND)
        time.sleep(5)
        self.checkoutput(self.OPEN_BLUETOOTH_COMMAND)
        time.sleep(5)
        logging.info('blue status after init')
        for i in range(5):
            if self.get_bluetooth_status():
                return
            self.checkoutput(self.OPEN_BLUETOOTH_COMMAND)
            time.sleep(10)
            logging.info('wait for bluetooth server on')
        raise Exception("bluetooth server disable !!")

    def _get_serial(self, name):
        if not hasattr(self, '_' + name):
            serial_name = self.config_yaml.get_note('remote_control')[name]
            band = self.config_yaml.get_note('remote_control')['band']
            serial_temp = serial.Serial(serial_name, band)
            self.__setattr__('_' + name, serial_temp)
        return self.__dict__['_' + name]

    @property
    def remote_back(self):
        return self._get_serial('remote_back')

    @property
    def remote_home(self):
        return self._get_serial('remote_home')

    @property
    def remote_power(self):
        return self._get_serial('remote_power')

    @property
    def speaker_power(self):
        return self._get_serial('speaker_power')

    @property
    def mouse_pair(self):
        return self._get_serial('mouse_pair')

    @property
    def remote_battery(self):
        return self._get_serial('remote_battery')

    def remote_enter_pair(self):
        '''
        put remote enter pair mode
        @return:
        '''
        try:
            logging.info("Press remote")
            self.remote_back.write(b'\xA0\x01\x01\xA2')  # 通路
            self.remote_home.write(b'\xA0\x01\x01\xA2')
            time.sleep(3)
            self.remote_back.write(b'\xA0\x01\x00\xA1')  # 断路
            self.remote_home.write(b'\xA0\x01\x00\xA1')
            time.sleep(1)

        except KeyboardInterrupt:
            self.remote_back.close()
            self.remote_home.close()

    def serial_on(self, serial_port):
        if not isinstance(serial_port, serial.serialposix.Serial):
            raise TypeError('Not serial port ')
        serial_port.write(b'\xA0\x01\x01\xA2')  # 通路

    def serial_off(self, serial_port):
        if not isinstance(serial_port, serial.serialposix.Serial):
            raise TypeError('Not serial port ')
        serial_port.write(b'\xA0\x01\x00\xA1')  # 断路

    def long_press(self, hold_time, *args):
        '''
        long press button
        @param hold_time:
        @param args:
        @return:
        '''
        for i in args:
            if not isinstance(i, serial.serialposix.Serial):
                raise TypeError('Not serial port ')
            self.serial_on(i)
        time.sleep(hold_time)
        for i in args:
            self.serial_off(i)

    @set_timeout(60)
    def check_connect_status_over_logcat(self):
        '''
        check connect status
        @return:
        '''
        start_time = time.time()
        logcat = self.popen('logcat -s AdapterProperties')
        while time.time() - start_time < 120:
            line = logcat.stdout.readline()
            if not line:
                continue
            print(line)
            if 'PROFILE_CONNECTION_STATE_CHANGE' in line:
                return True
        else:
            return False

    def get_bluetooth_status(self):
        '''
        get bt status
        @return:
        '''
        info = self.checkoutput(self.DUMP_STATUS_COMMAND)
        logging.info(info)
        result = re.findall(r'enabled: (\w+)', info, re.S)[0]
        return eval(
            result.title())

    def clear_connected(self):
        '''
        clear connected target devices
        @return:
        '''
        info = self.checkoutput(self.DUMP_MANAGER_COMMAND)
        try:
            metadata_info = re.findall(r'Metadata:(.*?)Profile: GattService', info, re.S)[0]
            connected_list = [i for i in
                              filter(lambda x: self.TARGET_INFO[x] in metadata_info, self.TARGET_INFO.keys())]
        except Exception as e:
            logging.info('no info in bluetooth manager')
            connected_list = []
        logging.info(f'connected {connected_list}')
        for i in connected_list:
            self.app_stop(self.BLUETOOTH_PACKAGE)
            self.checkoutput(self.BLUETOOTH_ACTIVITY_REGU.format(self.UNPARE_REGU, i))
            time.sleep(3)
