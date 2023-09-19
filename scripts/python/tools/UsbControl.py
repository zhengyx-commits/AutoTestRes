#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2023/2/7 10:01
# @Author  : chao.li
# @Site    :
# @File    : UsbControl.py
# @Software: PyCharm
import logging

import usb.core
import usb.util


class UsbControl:

    def __init__(self, idVendor, idProduct):
        '''
        try to find usb device
        raise error when can't find
        @param idVendor: usb vendor
        @param idProduct: usb product
        '''
        self.usbControl = usb.core.find(idVendor=idVendor, idProduct=idProduct)
        if self.usbControl is None:
            raise EnvironmentError("Can't find this usb device")
        for configuration in self.usbControl:
            for interface in configuration:
                ifnum = interface.bInterfaceNumber
                if not self.usbControl.is_kernel_driver_active(ifnum):
                    continue
                try:
                    self.usbControl.detach_kernel_driver(ifnum)
                except usb.core.USBError as e:
                    pass

        self.usbControl.set_configuration()

    def write(self, command, address=''):
        '''
        execute command
        @param command:
        @return:
        '''
        if address:
            self.usbControl.write(address, command)
        else:
            self.usbControl.write(command)

    def read(self):
        '''
        read feedback
        @return: feedback (str)
        '''
        info = ''
        i = 1
        sn = self.usbControl.read(0x81, 64)
        while (sn[i] < 255 and sn[i] > 0):
            info = info + chr(sn[i])
            i = i + 1
        return info

    def execute_rf_cmd(self, value):
        '''
        set rf value
        @param value:
        @return:
        '''
        if isinstance(value, int):
            value = str(value)
        if int(value) < 0 or int(value) > 95:
            assert 0, 'value must be in range 1-95'
        usb.write(f"*:CHAN:1:2:3:4:SETATT:{value};", address=1)
        logging.debug(f"rf command : {self.read()}")

    def get_rf_current_value(self):
        '''
        get all channel value
        @return:
        '''
        usb.write("*:ATT?", address=1)
        return usb.read()

# usb = UsbControl(idVendor=0x20ce, idProduct=0x0023)
# usb.write("*:CHAN:1:2:3:4:SETATT:20;", address=1)
# print(usb.read())
# usb.write("*:ATT?", address=1)
# print(usb.read())
