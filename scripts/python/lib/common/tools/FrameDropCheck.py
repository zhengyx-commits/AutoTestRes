#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/5/10 10:11
# @Author  : chao.li
# @Site    :
# @File    : FrameDropCheck.py
# @Software: PyCharm

import logging
import re
import threading
from time import sleep

from lib.common.system.ADB import ADB
from lib.common.tools.LoggingTxt import log


class FrameDropCheck(ADB):
    '''
    playback check framedrop

    Attributes:
        TAG : logcat tag
        FPS_INFO_FOR_IPTV_P_COMMAND : iptv command

        serialnumber : device number
        active :
        drop_count : drop count
        drop_total : drop total
        drop_list : fps info result list
        lock : threading lock

    '''
    TAG = 'AmlogicVideoDecoderAwesome'
    FPS_INFO_FOR_IPTV_P_COMMAND = 'cat /sys/class/video/fps_info'

    def __init__(self, serialnumber, logdir):
        super(FrameDropCheck, self).__init__(serialnumber, 'Frame Drop', logdir=logdir, stayFocus=True)
        self.serialnumber = serialnumber
        self.active = False
        self.drop_count = 0
        self.drop_total = 0
        self.drop_list = []
        self.lock = threading.Lock()

    def open_omxlog(self):
        logging.info('open omx log')
        self.run_shell_cmd("setprop media.omx.log_levels 255")
        self.run_shell_cmd("setprop vendor.media.omx.log_levels 255")

    def catch_logcat(self):
        '''
        catch drm logcat write to omxLogcat.log
        @return: popen
        '''
        logcat = self.popen("logcat -s {} |grep -v 'drm: codec_get_freed_handle' "
                            "> {}/result/omxLogcat.log".format(self.TAG, self.logdir))
        return logcat

    def catch_fps_info(self):
        '''
        catch iptv fps and append to drop_list
        @return: None
        '''
        self.drop_list = []
        while True:
            info = self.run_shell_cmd(self.FPS_INFO_FOR_IPTV_P_COMMAND)[1]
            self.drop_list.append(info)
            sleep(1)

    def run(self):
        '''
        run drop check thread
        @return: thread
        '''
        logging.info('starrt drop check thread')
        t = threading.Thread(target=self.catch_fps_info, name='checkDrop')
        t.setDaemon(True)
        t.start()
        return t

    def count_iptv_drop(self):
        '''
        calculate drop rate
        @return:
        '''
        logging.info('Calculate the drop rate')
        self.drop_count = 0
        self.drop_total = 0
        for i in self.drop_list:
            if 'drop_fps:0x' not in i or 'input_fps:0x' not in i:
                logging.info('drop数据异常')
                return
            count = int(re.findall(r'drop_fps:0x(.*)', i)[0], 16)
            total = int(re.findall(r'input_fps:0x(.*?) ', i)[0], 16)
            self.drop_total += total
            self.drop_count += count
        log.drop_times = '{} / {}'.format(self.drop_count, self.drop_total)
        logging.info(f"IPTV_Drop_Count: {'Pass' if self.drop_count == 0 else 'Fail'}")
