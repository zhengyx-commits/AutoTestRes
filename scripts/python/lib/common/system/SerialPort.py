#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/25 13:43
# @Author  : chao.li
# @Site    : SH #5-389
# @File    : SerialPort.py
# @Email   : chao.li@amlogic.com
# @Software: PyCharm

'''
测试通用方法模块,
包含
adb交互封装类
串口交互封装类
'''

import logging
import re
import signal
import time
from time import sleep

import pytest
import serial

from util.Decorators import set_timeout


class SerialPort:
    '''
    serial command control

    Attributes:
        serial_port : serial port
        baud : baud
        ser : serial.Serial instance
        ethernet_ip : ip address
        status : serial statuc

    '''

    def __init__(self, serial_port='', baud=''):
        self.serial_port = serial_port or pytest.config['serial_port']
        self.baud = baud or pytest.config['baudrate']
        logging.info(f"self.serial_port: {self.serial_port},self.baud: {self.baud}")
        self.ser = ''
        self.ethernet_ip = ''
        try:
            self.ser = serial.Serial(self.serial_port, self.baud, timeout=0.25)
            logging.info('the serial port %s-%s is opened' % (self.serial_port, self.baud))
            self.write('su')
            assert self.recv_until_pattern(b'#'), 'The serial port cannot to communicate to device'
            self.write('setprop persist.sys.usb.debugging y')
            self.write('setprop service.adb.tcp.port 5555')
        except serial.serialutil.SerialException as e:
            logging.info(f'not found serial:{e}')
        if isinstance(self.ser, serial.Serial):
            self.status = self.ser.isOpen()
        else:
            self.status = False
        if self.ethernet_ip:
            logging.info('get ip ：%s' % self.ethernet_ip)
        logging.info('the status of serial port is {}'.format(self.status))

    def get_ip_address(self, inet='ipv4'):
        '''
        get ip address
        @param inet: inet type ipv4 or ipv6
        @return:
        '''
        ip, eth0Ip, wlanIp, ppp0Ip = '', '', '', ''
        logging.info('getting ip info through the serial port')
        self.write('ifconfig')
        time.sleep(2)
        ipInfo = ''.join([i.decode('utf-8') for i in self.ser.readlines()]).split('TX bytes:')
        logging.info(ipInfo)
        if ipInfo == ['']:
            logging.info('no ip')
            return None
        for i in ipInfo:
            if 'eth0' in i:
                if inet == 'ipv4':
                    eth0Ip = re.findall(r'inet addr:(.*?)  Bcast', i, re.S)
                if inet == 'ipv6':
                    eth0Ip = re.findall(r'inet6 addr:(.*?)  Bcast', i, re.S)
                return eth0Ip[0]
            if 'wlan0' in i:
                wlanIp = re.findall(r'inet addr:(.*?)  Bcast', i, re.S)
                return wlanIp[0]
            if 'ppp0' in i:
                ppp0Ip = re.findall(r'inet addr:(.*?)  P-t-P', i, re.S)
                return ppp0Ip[0]
        logging.info('Devices no ip info')
        return None

    def write_pipe(self, command):
        '''
        execute the command , get feecback
        @param command: command
        @return: feedback
        '''
        self.ser.write(bytes(command + '\r', encoding='utf-8'))
        logging.info(f'=> {command}')
        sleep(0.1)
        data = self.recv()
        logging.info(data.strip())
        return data

    def enter_uboot(self):
        '''
        enter in uboot
        @return: uboot status : boolean
        '''
        self.write('reboot')
        start = time.time()
        info = ''
        while time.time() - start < 30:
            logging.debug(f'uboot {self.ser.read(100)}')

            try:
                info = self.ser.read(100).decode('utf-8')
                logging.info(info)
            except UnicodeDecodeError as e:
                logging.warning(e)
            if 'gxl_p211_v1#' in info:
                logging.info('the device is in uboot')
                # self.write('reset')
                return True
            if 'sc2_ah212#' in info:
                logging.info('OTT is in uboot')
                return True
            else:
                self.write('\n\n')
        logging.info('no uboot info printed,please confirm manually')

    def enter_kernel(self):
        '''
        enter in kernel
        @return: kernel status : boolean
        '''
        self.write('reset')
        self.ser.readlines()
        sleep(2)
        start = time.time()
        info = ''
        while time.time() - start < 60:
            try:
                info = self.ser.read(10000).decode('utf-8')
                logging.info(info)
            except UnicodeDecodeError as e:
                logging.warning(e)
            if 'Starting kernel ...' in info:
                self.write('\n\n')
            if 'console:/ $' in info:
                logging.info('now is in kernel')
                return True

        logging.info('no kernel message captured,please confirm manually')

    def write(self, command):
        '''
        enter in kernel
        @param command: command
        @return:
        '''
        self.ser.write(bytes(command + '\r', encoding='utf-8'))
        logging.info(f'=> {command}')
        sleep(0.1)

    def recv(self):
        '''
        get feedback from buffer
        @return: feedback
        '''
        while True:
            data = self.ser.read_all()
            if data == '':
                continue
            else:
                break
        return data.decode('utf-8')

    def recv_until_pattern(self, pattern=b'', timeout=60):
        '''
        keep get feedback from buffer until pattern has been catched
        @param pattern: pattern
        @param timeout: timeout
        @return: contains the printing of keywords
        '''
        start = time.time()
        result = []
        while True:
            if time.time() - start > timeout:
                if pattern:
                    raise TimeoutError('Time Out')
                return result
            log = self.ser.readline()
            if not log:
                continue
            logging.info(log)
            result.append(log)
            if pattern and pattern in log:
                return result

    def __del__(self):
        try:
            self.ser.close()
            logging.info('close serial port %s' % self.ser)
        except AttributeError as e:
            logging.info('failed to open serial port,not need to close')
