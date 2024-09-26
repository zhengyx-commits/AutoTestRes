#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2021/7/15 15:44
# @Author  : chao.li
# @Site    :
# @File    : GooglePlayMovies.py
# @Software: PyCharm
import logging

from lib.common.checkpoint.PlayerCheck_GooglePlayMovies import PlayerCheck_GooglePlayMovies
import os
import time
import re
import signal

from util.Decorators import set_timeout

from .OnlineParent import Online

PLAYER_CHECK = PlayerCheck_GooglePlayMovies()


class GooglePlayMovies(Online):
    '''
    GooglePlayer apk test lib

    Attributes:
        PLAYER_PACKAGE_TUPLE : googleplaymovies apk package
        PLAYTYPE : playback type
        DECODE_TAG : decode tag
    '''

    PLAYER_PACKAGE_TUPLE = 'com.google.android.videos', '.tv.presenter.activity.TvLauncherActivity'
    PLAYTYPE = 'GoogleMovies'
    DECODE_TAG = 'VDA'

    def __init__(self, name=''):
        super(GooglePlayMovies, self).__init__(name or 'GooglePlayMovies')

    def time_out(self):
        logging.warning('Time over! playback not success!')

    @set_timeout(300, time_out)
    def check_playback_status(self):
        '''
        check playback status
        @return: status : boolean
        '''
        return True
        # logging.info('Start check playback status')
        # self.clear_logcat()
        # self.logcat = self.popen("logcat -s %s" % self.DECODE_TAG)
        # temp, count = 0, 0
        # while True:
        #     line = self.logcat.stdout.readline()
        #     if 'ServiceDeviceTask' not in line:
        #         continue
        #     number = re.findall(r'IN\[(\d+),\d+\]', line, re.S)[0]
        #     logging.debug(f'buffer count {number}')
        #     if int(number) > temp:
        #         count += 1
        #     if count > 30:
        #         logging.info('Video is playing')
        #         os.kill(self.logcat.pid, signal.SIGTERM)
        #         self.logcat.terminate()
        #         self.clear_logcat()
        #         return True
        #     temp = int(number)

    def get_movies_list(self):
        '''
        get movies list
        @return: movies list : list ['str']
        '''
        movies_list = re.findall(
            r'text="([\u4E00-\u9FA5A-Za-z1-9: ]+)"\s+resource-id="com.google.android.videos:id/title_text"',
            self.get_dump_info(), re.S)
        if 'Movies' in movies_list:
            movies_list.remove('Movies')
        logging.info(f'play list {movies_list}')
        if not movies_list:
            raise ValueError('play list is empty')
        return movies_list

    def run_googleplaymovies(self, playback_type, seek_able=False, home_able=False):
        '''
        run googleplaymovies apk over ui
        @return:
        '''
        count = 0
        for i in self.get_movies_list():
            PLAYER_CHECK.reset()
            self.keyevent(21)
            self.keyevent(21)
            self.keyevent(20)
            logging.info(f'Playing - {i}')
            self.find_and_tap(i, 'text')
            # time.sleep(5)
            self.enter()
            time.sleep(5)
            if playback_type == "trailer":
                self.uiautomator_dump()
                self.find_and_tap("PLAY TRAILER", 'text')
                self.enter()
                time.sleep(5)
            elif playback_type == "full version":
                self.uiautomator_dump()
                self.find_and_tap("PLAY FROM BEGINNING", 'text')
                self.enter()
                time.sleep(5)
            elif playback_type == "switch_video":
                count = count + 1
            elif seek_able:
                self.uiautomator_dump()
                self.find_and_tap("PLAY FROM BEGINNING", 'text')
                self.enter()
                time.sleep(5)
                assert self.check_playback_status()
                self.keyevent(22)
                time.sleep(5)
                assert PLAYER_CHECK.check_seek()[0]
                break
            elif home_able:
                self.uiautomator_dump()
                self.find_and_tap("PLAY FROM BEGINNING", 'text')
                self.enter()
                time.sleep(5)
                assert self.check_playback_status()
                time.sleep(5)
                logging.info("push home")
                self.keyevent("KEYCODE_HOME")
                time.sleep(5)
                self.start_activity(*self.PLAYER_PACKAGE_TUPLE)
                time.sleep(5)
                self.enter()
                time.sleep(2)
                assert PLAYER_CHECK.check_home_play()[0]
                assert self.check_playback_status()
                break
            # elif playback_type == "switch_video":
            #     self.enter()
            #     time.sleep(15)
            else:
                pass
            self.uiautomator_dump()
            if 'PLAY MOVIE' in self.get_dump_info():
                self.find_and_tap('PLAY MOVIE', 'text')
                self.enter()
                time.sleep(10)
            elif 'PLAY FROM BEGINNING' in self.get_dump_info():
                self.find_and_tap('PLAY FROM BEGINNING', 'text')
                self.enter()
                time.sleep(10)
            assert self.check_playback_status(), self.app_stop(self.PLAYER_PACKAGE_TUPLE[0])
            # if i == 'Green Book':
            #     assert self.playerCheck.check_display_mode() == '2160', 'playback not 4k'
            assert PLAYER_CHECK.run_check_main_thread(30), self.app_stop(self.PLAYER_PACKAGE_TUPLE[0])
            if playback_type == "trailer" or playback_type == "full version" or seek_able:
                break
            if count == 2:
                break
            for _ in range(2):
                # self.uiautomator_dump()
                # if 'Movies' in self.get_dump_info():
                #     break
                self.keyevent(4)
                time.sleep(1)
