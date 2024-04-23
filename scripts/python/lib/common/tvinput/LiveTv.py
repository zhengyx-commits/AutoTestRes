#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/5/16 08:19
# @Author  : chao.li
# @Site    :
# @File    : LiveTv.py
# @Software: PyCharm

import logging
import re
import threading
import time

from lib.common.checkpoint.PlayerCheck_Base import PlayerCheck_Base
from lib.common.system.ADB import ADB
from util.Decorators import set_timeout

MENU = '82'
DTV_SCAN_BEGIN = "Scan begin"
ATV_SCAN_BEGIN = "Start atv scan"
DTV_SCAN_END = "Scan end"
ATV_SCAN_END = "scan destroy done"


class LiveTv(ADB):
    '''
    truck code tv score base class

    Attributes:
        play_time : playback duration (seconds)
        result : test result
        channel_count : live tv channel number
        store_count : store channel number
        player_check : PlayerCheck instance
        livetv_type : type ATV or DTV
        search_total_time : search channel cost time
        switch_total_time : switch channel cost time
        cost_time : cost time list
        start_scan_tag : start scan tag
        end_scan_tag : end scan tag

    '''
    FRAME_CHECK = 'cat /sys/module/amvideo/parameters/display_frame_count'
    STATUS_CHECK = "logcat -s DroidLogicTvInputService"
    DISPLAY_CHECK = "cat /sys/class/video/disable_video"
    def __init__(self):
        super(LiveTv, self).__init__('Live Tv', unlock_code="", stayFocus=False)
        self.play_time = 10
        self.result = 'Pass'
        self.channel_count = 0
        self.store_count = 0
        self.player_check = PlayerCheck_Base()
        self.player_check.sourceType = "tvpath"
        self.player_check.DISPLAYER_FRAME_COMMAND = 'cat /sys/class/video_composer/receive_count'
        self.livetv_type = ''
        self.search_total_time = 0
        self.switch_total_time = 0
        self.cost_time = []
        self.start_scan_tag = ''
        self.end_scan_tag = ''

    def timeout(self):
        self.result = 'Fail'
        logging.info("can't catch dependent logcat,time out")

    @set_timeout(250)
    def search_channel(self):
        '''
        search live tv channel
        @return: None
        '''
        self.keyevent(MENU)
        self.u2.wait('Channel')
        self.u2.wait('Search Channel')
        self.u2.wait('Auto Scan')
        self.clear_logcat()
        if self.livetv_type == 'ATV':
            logcat_tag = "AM_DEBUG"
            self.start_scan_tag = ATV_SCAN_BEGIN
            self.end_scan_tag = ATV_SCAN_END
        elif self.livetv_type == 'DTV':
            logcat_tag = "TvStoreManager"
            self.start_scan_tag = DTV_SCAN_BEGIN
            self.end_scan_tag = DTV_SCAN_END
        else:
            logcat_tag = ''
        log, logfile = self.save_logcat('CountCheck.log', tag=logcat_tag)
        while True:
            if self.u2.wait_not_exist('Pause Scan'):
                self.stop_save_logcat(log, logfile)
                self.screenshot('Pause_Scan', layer="osd+video")
                break

    def setup(self):
        '''
        set up test attr
        @return:
        '''
        self.home()
        self.result = 'Pass'
        self.popen('root')
        self.clear_logcat()

    def pushsh(self, testsh):
        '''
        check DTV_Search_Channel_CountCheck.sh or ATV_Search_Channel_CountCheck.sh is or not in device
        @param testsh: test sh
        @return: None
        '''
        result = self.popen(f'shell ls /data/local/{testsh} 2>&1').stdout.readlines()[0]
        if 'No such file or directory' in result:
            logging.info('Not exists , create it ')
            self.res_manager.get_target('sh/' + testsh)
            self.root()
            self.push(f"res/sh/{testsh}", '/data/local/')
        self.run_shell_cmd(f'chmod a+x /data/local/{testsh}')

    def check_channel_count(self, search_count_sh, search_store_sh):
        '''
        run shell script check channel count
        @param search_count_sh:
        @param search_store_sh:
        @return: check status : boolean
        '''
        cmd = self.logdir + '/CountCheck.log'
        self.push(cmd, '/data/local/')
        log = self.run_shell_cmd(f'sh /data/local/{search_count_sh}')[1]
        if "CountCheck correct" in log:
            self.channel_count = re.findall(r'CountCheck correct (\d)', log, re.S)[0]
            log = self.run_shell_cmd(f'sh /data/local/{search_store_sh}')[1]
            if "StoreCheck correct" in log:
                self.store_count = re.findall(r'StoreCheck correct (\d)', log, re.S)[0]
                if self.channel_count == self.store_count:
                    logging.info('search and store channel is correct')
                    return True
        else:
            logging.info('channel count is 0')

    @set_timeout(5, timeout)
    def check_display(self):
        '''
        check video display
        @return: check status : boolean
        '''
        count = []
        while '000' not in ''.join(count):
            result = self.run_shell_cmd(self.DISPLAY_CHECK)[1]
            count.append(result)
            time.sleep(0.2)
        logging.info('Display Catched')
        return True

    @set_timeout(5, timeout)
    def check_status(self, channel):
        '''
        check display status
        @param channel: hdmi channel name
        @return: channel name
        '''
        # from logcat get channel info
        server = 'register Input:com.droidlogic.tvinput/.services.'
        logcat = self.popen(self.STATUS_CHECK)
        while True:
            line = logcat.stdout.readline()
            logging.debug(line)
            if server + channel in line:
                logging.info(line)
                logging.info('Show {} channel'.format(channel))
                logcat.terminate()
                return channel

    def check_display_vfm(self, source):
        '''
        check vfm map
        @param source: display source
        @return: None
        '''
        time.sleep(3)
        try:
            mapInfo = self.run_shell_cmd('cat /sys/class/vfm/map | grep (1)')[1]
            logging.info(mapInfo)
            module_count = self.run_shell_cmd('cat /sys/class/vfm/map | grep -o (1) | wc -l')[1]
            if mapInfo:  # if check tvpath passed and NOT provider args
                logging.info('MapInfo: [ {} ]; Count: [ {} ]'.format(mapInfo, module_count)), time.sleep(0.5)
                if source == 'tvpath' not in mapInfo or (source == 'vdec' and ('vdec' and 'dvbl') not in mapInfo):
                    logging.warning('Map\'s not correct, current path is [ {} ]'.format(source))
                return True
            else:
                logging.debug('No map was generated!')
                return False
        except Exception as err:
            logging.error('Unable to check vfm/map info, {}'.format(err))

    @set_timeout(500)
    def switch_programs_check(self):
        '''
        switch program and check status
        @return: None
        '''
        start_channelId, start_time = self.get_channelid()
        # for i in range(int(self.channel_count)):
        while True:
            switchId, switch_time = self.switch_programs()
            if self.play_check():
                logging.warning('Playback not current')
                self.result = 'Fail'
            else:
                logging.info('Playback current')
            self.screenshot('check_playback' + str(switchId))
            if switchId == start_channelId:
                logging.info(f"switch programs 1 round")
                self.switch_total_time = round((switch_time - start_time), 3)
                logging.info(f"switch programs total time is {self.switch_total_time}s")
                break

    def play_check(self):
        '''
        check playback status
        @return: None
        '''
        self.clear_logcat()
        log, logfile = self.save_logcat('logcat.log', tag='tvserver libdvr')
        res_flag = self.player_check.run_check_main_thread(10)
        assert res_flag, 'playback error'
        self.keyevent(23)
        time.sleep(2)
        self.keyevent(23)
        if self.find_element(str(self.channel_count), "text"):
            self.screenshot('program_info', layer='osd+video')
        self.back()
        self.stop_save_logcat(log, logfile)

    def count_timecost(self, time):
        '''
        append time to cost_time
        @param time: time
        @return: cost_time
        '''
        if time:
            self.cost_time.append(time)
            logging.info(self.cost_time)
            return self.cost_time
        else:
            return False

    def avg_time(self, cost_time):
        '''
        calc cost time list
        @param cost_time: cost time
        @return: average of cost time
        '''
        if cost_time:
            avg_costTime = float(sum(cost_time)) / int(len(cost_time))
            logging.info(f'avg_costTime is: {avg_costTime} s')
            return avg_costTime
        logging.info('please check count time')

    def get_channelid(self):
        self.clear_logcat()
        time.sleep(2)
        info = self.run_shell_cmd('logcat -s -d DTVInputService | grep channel')[1]
        if info:
            logging.debug(info)
            channelId = info.split(':')[-1]
            h, m, s = info.split()[1].split(':')
            count_time = float(h) * 3600 + float(m) * 60 + float(s)
            return channelId, count_time
        self.result = 'Fail'

    def get_searchtime(self):
        count_times = []
        with open(self.logdir + '/' + 'CountCheck.log', "r") as f:
            info = f.readlines()
            for i in info:
                if self.start_scan_tag in i or self.end_scan_tag in i:
                    h, m, s = i.split()[1].split(":")
                    count_time = float(h) * 3600 + float(m) * 60 + float(s)
                    count_times.append(count_time)
                    if len(count_times) == 2:
                        self.search_total_time = round((count_times[1] - count_times[0]), 3)
                        break
            logging.info(f"search channel total time is {self.search_total_time} s")
            return self.search_total_time

    def switch_programs(self):
        tempId, _ = self.get_channelid()
        screen_record = threading.Thread(target=self.video_record, args=(str(tempId), 28, 30, 10), name='screen_record')
        screen_record.setDaemon(True)
        screen_record.start()
        time.sleep(2)
        self.keyevent('KEYCODE_DPAD_DOWN')
        screen_record.join()
        time.sleep(3)
        switchId, switch_time = self.get_channelid()
        if switchId == tempId:
            self.result = 'Fail'
            logging.warning(f"switch programs {switchId} failed")
        return switchId, switch_time
