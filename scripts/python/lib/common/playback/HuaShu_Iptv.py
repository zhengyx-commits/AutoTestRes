#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/4/24 14:24
# @Author  : chao.li
# @Site    :
# @File    : HuaShu_Iptv.py
# @Software: PyCharm

import logging
import random
import re
import time

from lib.common.playback.OnlineParent import Online
from lib.common.system.ADB import ADB
from util.Decorators import set_timeout


class HuaShu(ADB, Online):
    '''
    Iptv Huashu apk test lib

    Attributes:
        ALL_CONTENT_PACKAGE_TUPLE : 全部内容 apk package tuple
        PLAY_BUTTON_INFO : play button info
        CONTENT_NAME_REGU : video name regular
        FRAME_LIST : Iptv home UI FrameLayout name list [str]

        serialnumber : adb number
        logdir : log dir
        result : test result
        resolution_list : resolution list
        serialno : iptv serial number
        sn : iptv sn number
        home_level : home level
        cursor_x : ui cursor x index
        cursor_y : ui cursor y index
        play_history : play history

    '''
    ALL_CONTENT_PACKAGE_TUPLE = 'com.bestv.ott.baseservices', 'com.bestv.ott.launcher.allcategory.AllCategoriesActivity'
    PLAY_BUTTON_INFO = 'com.bestv.ott.baseservices:id/btn_play'
    CONTENT_NAME_REGU = r'text="(\S+?)" resource-id="com.bestv.ott.baseservices:id/tv_video_name"'
    FRAME_LIST = ['动画总动员', '精选', '看电视', '金卡会员看奇艺', '推荐', '电影', '电视剧', '少儿动漫', '4K', '综艺', '爱家教育', '博雅课堂', '体育',
                  '纪实', '生活', '云游戏']

    def __init__(self, serialnumber, logdir):
        ADB.__init__(self, serialnumber, 'Hua Shu', logdir=logdir, stayFocus=True)
        Online.__init__(self)
        self.serialnumber = serialnumber
        self.logdir = logdir
        self.home()
        self.root()
        self.result = 'Pass'
        self.resolution_list = []
        self.serialno = self.get_serial()
        self.sn = ':'.join(re.findall(r'.{2}', self.serialno[-12:]))
        self.home_level = 0
        self.cursor_y = 0
        self.cursor_x = 0
        self.play_history = []

    def enter(self):
        '''
        input keyevent 23
        add home level
        @return: None
        '''
        self.keyevent('23')
        self.home_level += 1
        time.sleep(2)

    def exit(self):
        '''
        input keyevent 4
        minus home level
        @return: None
        '''
        self.keyevent('4')
        self.home_level -= 1

    def exit_playback(self):
        '''
        exit playback
        minus home level
        @return: None
        '''
        self.keyevent('4')
        self.keyevent('4')
        self.uiautomator_dump(self.logdir)
        while self.PLAY_BUTTON_INFO not in self.get_dump_info():
            self.keyevent('4')
            self.keyevent('4')
            self.uiautomator_dump(self.logdir)
        self.home_level -= 1

    def get_dump_info(self):
        '''
        get UI dump info
        @return: ui info : str
        '''
        with open(self.logdir + '/window_dump.xml', 'r') as f:
            temp = f.read()
        return temp

    def get_focues(self):
        '''
        get framelayout index
        @return: index : int
        '''
        logging.info('get current channel index')
        self.uiautomator_dump(self.logdir)
        dumpInfo = self.get_dump_info()
        nodeInfo = re.findall(r'node index=(.*?)/>', dumpInfo, re.S)
        text_regu = r'text="(\S+)"'
        for i in range(len(nodeInfo)):
            if 'focused="true"' in nodeInfo[i]:
                name = re.findall(text_regu, nodeInfo[i], re.S)
                if len(list(filter(lambda x: x, name))) == 0:  # deal with Chinese characters framelayout index
                    return self.FRAME_LIST.index(name[0])
                else:  # deal with picture framelayout index
                    temp_index = int(nodeInfo[i][1])  # get current index
                    for j in range(1, temp_index + 1):  # loop list find Chinese characters framelayout index
                        if temp_index < 4:  # increase by degrees when small index
                            temp_name = re.findall(text_regu, nodeInfo[i + j], re.S)
                            if temp_name:
                                compare_index = self.FRAME_LIST.index(temp_name[0])
                                return compare_index - j
                        else:  # discrease by degrees when big index
                            temp_name = re.findall(text_regu, nodeInfo[i - j], re.S)
                            if temp_name:
                                compare_index = self.FRAME_LIST.index(temp_name[0])
                                return compare_index + j

    def switch_to(self, channel):
        '''
        change to target channel
        @param channel: channel index
        @return: None
        '''
        if channel not in self.FRAME_LIST:
            raise ValueError('Channel not exists')
        to_index = self.FRAME_LIST.index(channel)
        cur_index = self.get_focues()
        logging.info(to_index, cur_index)
        if cur_index == to_index:
            return
        move = abs(cur_index - to_index)
        while cur_index != to_index:
            for _ in range(move):
                if cur_index - to_index > 0:
                    self.keyevent('21')
                else:
                    self.keyevent('22')
            cur_index = self.get_focues()
            logging.info(to_index, cur_index)

    def loading_timeout(self):
        logging.warning('Time over!')

    def wait_loading(self):
        '''
        wait for video start playing
        @return: None
        '''
        logcat = self.popen("logcat")
        start = time.time()
        line = ''
        while time.time() - start < 3:
            try:
                line = logcat.stdout.readline()
            except UnicodeDecodeError as e:
                logging.warning(e)
            if not line:
                continue
            line = line.strip()
            if self.LOADING_TAG[1] in line or 'getCurrentPosition' in line:
                logging.info('loading done')
                self.clear_logcat()
                logcat.terminate()
                break
            if self.LOADING_TAG[0] in line:
                logging.info('start loading')
        logcat.terminate()

    def resolution_switch(self):
        '''
        switch resolution
        @return: None
        '''

        def click_enter():
            '''
            invoke resolution menu
            @return: None
            '''
            self.keyevent('23')
            self.uiautomator_dump(self.logdir)
            while "可调整播放清晰度" not in self.get_dump_info():
                self.keyevent('23')
                self.uiautomator_dump(self.logdir)

        # 获取分辨率列表
        logging.info('Switching resolution')
        self.resolution_list = []
        for i in range(3):
            click_enter()
            self.keyevent('20')
            self.uiautomator_dump(self.logdir)
            dump_info = self.get_dump_info()
            self.resolution_list = re.findall(r'text="(\S+?)"', dump_info, re.S)
            if '自动' in self.resolution_list:
                break
        else:
            logging.warning("Can't not find this resolution")
            return
        logging.info(self.resolution_list)
        for i in self.resolution_list:
            logging.info(f'Switch into  - > {i}')
            click_enter()
            self.keyevent('20')
            self.find_and_tap(i, 'text')
            self.wait_loading()

    def episode_switch(self):
        '''
        switch episode
        @return: Nonee
        '''
        logging.info('Switching episode')
        self.keyevent('20')
        for i in range(1, 3):
            if random.randint(0, 1):
                self.keyevent('22')
            else:
                self.keyevent('21')
        self.keyevent('23')
        self.wait_loading()
        time.sleep(3)

    def get_serial(self):
        '''
        get serial number
        @return: serial number : str
        '''
        info = self.run_shell_cmd('getprop |grep serial')[1]
        return re.findall(r'ro.serialno\]:\s*\[(.*?)\]', info, re.S)[0]

    @set_timeout(5, loading_timeout)
    def start_all_content(self):
        '''
        start 全部节目
        @return: None
        '''
        self.start_activity(*self.ALL_CONTENT_PACKAGE_TUPLE)
        self.home_level += 1
        self.wait_element('电视剧', 'text')

    def random_move(self):
        '''
        random move ui cursor
        @return: None
        '''
        for _ in range(random.randint(1, 3)):
            if random.randint(0, 1):
                self.keyevent('20')
                self.cursor_y += 1
            else:
                if self.home_level == 0 and self.cursor_y <= 3:
                    continue
                self.keyevent('19')
        self.keyevent('22')
        self.cursor_x += 1
        for _ in range(random.randint(1, 5)):
            if random.randint(0, 1):
                self.keyevent('22')
                self.cursor_x += 1
            else:
                if self.cursor_x > 0:
                    self.keyevent('21')
                    self.cursor_x -= 1

    def find_content(self):
        '''
        find video content over UI cursor
        @return: None
        '''

        def exit_dianbo():
            '''
            exit dianbo playback
            @return: None
            '''
            while self.PLAY_BUTTON_INFO in self.get_dump_info():
                self.exit()
                self.uiautomator_dump(self.logdir)

        logging.info('find video content able to play')
        for i in ['电影', '电视剧', '少儿', '综艺']:
            logging.info(f'Start playing {i}')
            # if i == '电影':
            #     self.keyevent('23')
            # else:
            self.find_and_tap(i, 'text')
            self.cursor_x = 0
            temp = 0
            while temp < 2:
                self.random_move()
                self.enter()
                self.uiautomator_dump(self.logdir)
                if self.PLAY_BUTTON_INFO in self.get_dump_info():
                    content_name = re.findall(self.CONTENT_NAME_REGU, self.get_dump_info(), re.S)[0]
                    # if content_name in self.play_history:
                    #     exit_dianbo()
                    #     continue
                    logging.info(f'Now playing {content_name}')
                    # 找到了可以播放的内容
                    self.find_and_tap(self.PLAY_BUTTON_INFO, 'resource-id')
                    temp += 1
                    self.play_history.append(content_name)
                    self.wait_loading()
                    # 处理断点续播弹窗
                    time.sleep(6)
                    if i == '电视剧':
                        self.episode_switch()
                    self.resolution_switch()
                    self.exit_playback()
                    self.uiautomator_dump(self.logdir)
                    exit_dianbo()
            self.exit()

    def playback(self):
        '''
        start playback
        @return: None
        '''
        # self.app_stop(self.all_content[0])
        self.start_all_content()
        self.find_content()
        self.app_stop(self.ALL_CONTENT_PACKAGE_TUPLE[0])

    def __repr__(self):
        return f'Serial no : {self.serialno}\nSN no : {self.sn}'
