#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/4/28 09:28
# @Author  : chao.li
# @Site    :
# @File    : Emmc.py
# @Software: PyCharm

import logging

import pytest

from lib.common.system.SerialPort import SerialPort


class Emmc(SerialPort):
    '''
    emmc info test lib ，inherited from serialcommand

    Attributes:
        TYPE_200 : hs200
        TYPE_200 : hs400

        result : result
        type : type

    '''
    TYPE_200 = b'HS200'
    TYPE_400 = b'HS400'

    def __init__(self):
        super(Emmc, self).__init__()
        self.result = 'Pass'
        self.type = ''

    def catch(self, pattern=b''):
        logging.info('start test emmc')
        self.write('reboot')
        result = self.recv_until_pattern(pattern)
        log = []
        for i in result:
            try:
                i = i.decode('utf-8')
                log.append(i)
            except Exception:
                logging.warning(f"Can't decode {i}")
        return ''.join(log)
