#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/4/13 16:37
# @Author  : chao.li
# @Site    :
# @File    : __init__.py
# @Software: PyCharm


import logging
import os
import re

from tools.yamlTool import yamlTool


class Check:
    '''
    Check point Base class

    Attributes:
    '''

    def callback(self, prefix, name, *args):
        method = getattr(self, prefix + name, None)
        if callable(method):
            return method(*args)
        else:
            logging.warning('no such func')
            logging.info('Please select one of the following options')
            logging.info(list(filter(lambda x: prefix in x, dir(self))))

    def print_info(self, name):
        '''
        get print_* func
        @param name: func name
        @return:
        '''
        return self.callback('print_', name)

    def get_info(self, name):
        '''
        get get_* func
        @param name: func name
        @return:
        '''
        return self.callback('get_', name)

    def find_key_value(self, regix, info):
        '''
        get regix feedback
        @param regix: re
        @param info: target string
        @return: first value that match : str
        '''
        info = re.findall(regix, info, re.S)
        if info:
            return info[0]
        else:
            return "Value Not found"
