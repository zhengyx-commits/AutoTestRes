#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/5/12 10:04
# @Author  : chao.li
# @Site    :
# @File    : YUV.py
# @Software: PyCharm

import logging
import time

from lib.common.system.ADB import ADB
from util.Decorators import set_timeout


class YUV(ADB):
    '''
    yuv data handle class

    Attributes:
        GET_CHECK_SUM_COMMAND : get sum command
        VOLUME_COMMAND : get sum index command

        active : active flag
        yuv_index : yuv index
    '''

    GET_CHECK_SUM_COMMAND = "tail -n 1 /data/local/tmp/checksum.txt |awk -F ' ' '{print $6}'"
    GET_CHECK_SUM_INDEX_COMMAND = "tail -n 1 /data/local/tmp/checksum.txt |awk -F ' ' '{print $1}'"

    def __init__(self):
        super(YUV, self).__init__('YUV', unlock_code="", stayFocus=True)
        self.active = False
        self.root()
        self.yuv_index = ''

    def open_yuv(self):
        '''
        open yuv func
        @return: None
        '''
        logging.info('Open yuv')
        self.run_shell_cmd("chmod 777 /data/local/tmp")
        self.run_shell_cmd("setenforce 0")
        self.run_shell_cmd("echo 0 1 > /sys/class/vdec/frame_check")
        self.run_shell_cmd("echo 0x30 > /sys/module/decoder_common/parameters/fc_debug")
        self.run_shell_cmd("echo 1 > /sys/module/decoder_common/parameters/checksum_enable")

    def close_yuv(self):
        '''
        close yuv func
        @return: None
        '''
        logging.info('Close yuv')
        self.run_shell_cmd("echo 0 0 > /sys/class/vdec/frame_check")
        self.run_shell_cmd("echo 0 > /sys/module/decoder_common/parameters/fc_debug")
        self.run_shell_cmd("echo 0 > /sys/module/decoder_common/parameters/checksum_enable")

    @set_timeout(10)
    def get_yuv_result(self):
        '''
        get yuv data
        @return: yuv data
        '''
        while True:
            if 1 == self.run_shell_cmd('ls /data/local/tmp/checksum.txt')[0]:
                print('wait')
                time.sleep(1)
            else:
                break
        logging.debug(self.yuv_index)
        logging.debug(self.run_shell_cmd(self.GET_CHECK_SUM_INDEX_COMMAND)[1])
        if self.yuv_index:
            for _ in range(10):
                if self.yuv_index != self.run_shell_cmd(self.GET_CHECK_SUM_INDEX_COMMAND)[1]:
                    break
                time.sleep(0.5)
                logging.info('Same index')
            else:
                logging.warning('yuv has not been updated')
                return 'Yuv Not Update'
        resultInfo = self.run_shell_cmd(self.GET_CHECK_SUM_COMMAND)[1]
        index = self.run_shell_cmd(self.GET_CHECK_SUM_INDEX_COMMAND)[1]
        self.yuv_index = index
        logging.debug(f'resultInfo {resultInfo}')
        # logging.info(self.run_shell_cmd('tail -n 1 /data/local/tmp/checksum.txt')[1])
        return resultInfo[:-1]
