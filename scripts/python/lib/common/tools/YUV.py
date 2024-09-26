#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/5/12 10:04
# @Author  : chao.li
# @Site    :
# @File    : YUV.py
# @Software: PyCharm

import logging
import re
import pytest
import time
import os
import signal
from util.Decorators import set_timeout, stop_thread
from lib.common.system.ADB import ADB
from util.Decorators import set_timeout


class YUV(ADB):
    """
    yuv data handle class

    Attributes:
        GET_CHECK_SUM_COMMAND : get sum command
        VOLUME_COMMAND : get sum index command

        active : active flag
        yuv_index : yuv index
    """
    # yuv abnormal type
    YUV_CHKSUM_NONE = ""
    YUV_CHKSUM_ERR = "yuvsum:error"
    YUV_CHKSUM_SW_DECODE = "yuvsum:soft-decode"
    GET_CHECK_SUM_COMMAND = "tail -n 1 /data/local/tmp/checksum.txt |awk -F ' ' '{print $6}'"
    GET_CHECK_SUM_INDEX_COMMAND = "tail -n 1 /data/local/tmp/checksum.txt |awk -F ' ' '{print $1}'"

    def __init__(self):
        super(YUV, self).__init__('YUV', unlock_code="", stayFocus=True)
        self.active = False
        self.root()
        self.yuv_index = ''
        self.local_logcat_opened = False
        self.local_logcat = ""
        self.yuvEnable = True
        if self.yuvEnable:
            self.yuvChkSum = self.YUV_CHKSUM_NONE

    def open_yuv(self):
        """
        open yuv func
        @return: None
        """
        logging.info('Open yuv')
        self.run_shell_cmd("chmod 777 /data/local/tmp")
        self.run_shell_cmd("setenforce 0")
        self.run_shell_cmd("echo 0 1 > /sys/class/vdec/frame_check")
        self.run_shell_cmd("echo 0x30 > /sys/module/decoder_common/parameters/fc_debug")
        self.run_shell_cmd("echo 1 > /sys/module/decoder_common/parameters/checksum_enable")

    def close_yuv(self):
        """
        close yuv func
        @return: None
        """
        logging.info('Close yuv')
        self.run_shell_cmd("echo 0 0 > /sys/class/vdec/frame_check")
        self.run_shell_cmd("echo 0 > /sys/module/decoder_common/parameters/fc_debug")
        self.run_shell_cmd("echo 0 > /sys/module/decoder_common/parameters/checksum_enable")

    def setYUVChkSum(self, chkSum):
        if self.yuvEnable:
            self.yuvChkSum = chkSum

    def getYUVChkSum(self):
        if self.yuvEnable:
            return self.yuvChkSum

    @set_timeout(10)
    def get_yuv_result(self):
        """
        get yuv data
        @return: yuv data
        """
        if pytest.target.get("prj") == "ott_hybrid_t_yuv":
            decoder_summary = self.run_shell_cmd("dmesg | grep -i  Decoder-Summary")[1]
            logging.info(decoder_summary)
            yuv_sum = re.findall(r"yuvsum.*", decoder_summary)[0]
            logging.info(yuv_sum)
            return yuv_sum[:-1]
        else:
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
            result_info = self.run_shell_cmd(self.GET_CHECK_SUM_COMMAND)[1]
            index = self.run_shell_cmd(self.GET_CHECK_SUM_INDEX_COMMAND)[1]
            self.yuv_index = index
            logging.debug(f'resultInfo {result_info}')
            # logging.info(self.run_shell_cmd('tail -n 1 /data/local/tmp/checksum.txt')[1])
            return result_info[:-1]

    def local_logcat_start(self):
        """
        get VideoPlayer's logcat popen
        @return: None
        """
        self.clear_logcat()
        self.local_logcat = self.popen('logcat -s VideoPlayer')
        self.local_logcat_opened = True

    # def local_logcat_stop(self):
    #     """
    #     close VideoPlayer's logcat popen
    #     @return: None
    #     """
    #     if self.local_logcat and self.local_logcat_opened:
    #         self.local_logcat.terminate()
    #         os.kill(self.local_logcat.pid, signal.SIGTERM)
    #         logging.info('logcat.terminate()')
    #         self.local_logcat_opened = False
    #     else:
    #         logging.info("logcat popen does not exist")
    #
    # def get_logcat_run_timer_error(self):
    #     raise Exception('get logcat run time error')
    #
    # @set_timeout(50, get_logcat_run_timer_error)
    # def logcat_read_line(self):
    #     """
    #     read each line of VideoPlayer's log
    #     @return: VideoPlayer's log
    #     """
    #     while True:
    #         if self.local_logcat and self.local_logcat_opened:
    #             log = self.local_logcat.stdout.readline()
    #             if log:
    #                 return log.strip()
    #             else:
    #                 logging.info("No log output")
    #         else:
    #             logging.info("logcat popen does not exist")
