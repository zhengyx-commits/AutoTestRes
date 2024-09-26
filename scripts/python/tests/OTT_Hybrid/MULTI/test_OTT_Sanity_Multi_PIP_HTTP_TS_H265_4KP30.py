#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/4/22
# @Author  : jianhua.huang
import itertools

import numpy

from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

common_case = Common_Playcontrol_Case(playerNum=2)


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.multi_setup()
    multi.stop_multiPlayer_apk()
    yield
    multi.stop_multiPlayer_apk()


# @pytest.mark.skip
def test_Multi_PIP_HTTP_TS_H265_4KP30():
    # final_urllist = get_conf_url("conf_http_url", "http_TS_H265_4K")
    if p_conf_single_stream:
        final_urllist = get_conf_url("conf_http_url", "http_TS_H265_4K")
        for item in final_urllist:
            start_cmd = multi.get_start_cmd([item, item])
            multi.send_cmd(start_cmd)
            assert common_case.player_check.check_startPlay()[0], "start play failed"
            common_case.switch_pip_2_window()
            common_case.pause_resume_seek_stop()
            multi.stop_multiPlayer_apk()
    else:
        # urls = list(itertools.product(final_urllist, final_urllist))
        # urls = numpy.stack([final_urllist, sorted(final_urllist, reverse=True)], 1).tolist()
        H265_4K_P60_url = get_conf_url("conf_http_url", "http_TS_H265_4K_P60")
        H265_1080_P60_url = get_conf_url("conf_http_url", "http_TS_H265_1080_P60")
        H265_4K_P60_url.extend(H265_4K_P60_url)
        H265_1080_P60_url.extend(H265_1080_P60_url)
        urls = numpy.stack([H265_4K_P60_url, sorted(H265_1080_P60_url, reverse=True)], 1).tolist()
        for url in urls:
            # url = list(url)
            # print(f"url[0]:{url[0]}")
            # print(f"url[1]:{url[1]}")
            p_start_cmd = multi.get_start_cmd([url[0], url[1]])
            multi.send_cmd(p_start_cmd)
            assert common_case.player_check.check_startPlay()[0], "start play failed"
            common_case.switch_pip_2_window()
            # common_case.pause_resume_seek_stop()
            multi.stop_multiPlayer_apk()

# class PIP(PlayerCheck):
#     MULTIMEDIAPLAYER_TEST_APP_NAME = 'com.amlogic.multimediaplayer'
#     APP_TEST = 'am broadcast -a multimediaplayer.test '
#     APP_TEST_WINDOW = '--ei instance_id '
#     APP_TEST_ACTION = '--es command '
#
#     def video_pause(self, play_num, window_base):
#         if play_num == 0:
#             logging.info(f"player number is {play_num} , please check !")
#             assert False
#         elif play_num != 1:
#             if window_base >= play_num:
#                 logging.info(f"play number is {play_num} , the starting window is {window_base} please check !")
#                 assert False
#         elif play_num == 1:
#             if window_base != play_num:
#                 logging.info(f"play number is {play_num} , the starting window is {window_base} please check !")
#                 assert False
#
#         video_num = window_base - 2
#         while video_num < play_num - 1:
#             video_num += 1
#             logging.info(f"action_window:{video_num}")
#             video_cmd = self.video_cmd(video_num, action='pause')
#             if video_num > 0:
#                 self.__playerNum = 2
#             else:
#                 self.__playerNum = 1
#             self.check_pause(cmd=video_cmd,
#                              keywords=[f"[MediaPlayerBase_{video_num}] changeStatus: prevStatus=Playing, "
#                                        f"newStatus=Pausing"],
#                              logFilter='logcat -s AmlMultiPlayer')
#
#     def video_resume(self, play_num, window_base):
#         if play_num == 0:
#             logging.info(f"player number is {play_num} , please check !")
#             assert False
#         elif play_num != 1:
#             if window_base >= play_num:
#                 logging.info(f"play number is {play_num} , the starting window is {window_base} please check !")
#                 assert False
#         elif play_num == 1:
#             if window_base != play_num:
#                 logging.info(f"play number is {play_num} , the starting window is {window_base} please check !")
#                 assert False
#
#         video_num = window_base - 2
#         while video_num < play_num - 1:
#             video_num += 1
#             logging.info(f"action_window:{video_num}")
#             video_cmd = self.video_cmd(video_num, action='resume')
#             if video_num > 0:
#                 self.__playerNum = 2
#                 self.resume_playerNum = 2
#             else:
#                 self.__playerNum = 1
#             self.check_resume(cmd=video_cmd,
#                               keywords=[f"[MediaPlayerBase_{video_num}] changeStatus: prevStatus=Pausing, "
#                                         f"newStatus=Playing"],
#                               logFilter='logcat -s AmlMultiPlayer')
#
#     def check_SwitchWindow(self, window_base, window_target):
#         t1 = 15
#         action = 'switch_window'
#         cmd = self.APP_TEST + self.APP_TEST_ACTION + f'{action}' + ' --ei source_window_id ' + f'{window_base} ' + '--ei target_window_id ' + f'{window_target} '
#         keywords = [f"[MediaPlayerProxy_{window_target}] surfaceChanged: SurfaceHolder",
#                     f"[MediaPlayerProxy_{window_base}] surfaceChanged: SurfaceHolder"]
#         logFilter = "logcat -s AmlMultiPlayer"
#         player_check.check_switchWindow(cmd, keywords=keywords, logFilter=logFilter, focused_playerNum=window_target)
#         self.run_check_main_thread(t1)
#         self.__playerNum = 2
#         self.resume_playerNum = 2
#         self.run_check_main_thread(t1)
#         keywords = [f"[MediaPlayerProxy_{window_base}] surfaceChanged: SurfaceHolder",
#                     f"[MediaPlayerProxy_{window_target}] surfaceChanged: SurfaceHolder"]
#         player_check.check_switchWindow(cmd, keywords=keywords, logFilter=logFilter, focused_playerNum=window_target)
#         self.__playerNum = 2
#         self.resume_playerNum = 2
#         self.run_check_main_thread(t1)
#         self.__playerNum = 1
#         self.run_check_main_thread(t1)
#
#     def video_stop_play(self, play_num, window_base):
#         if play_num == 0:
#             logging.info(f"player number is {play_num} , please check !")
#             assert False
#         elif play_num != 1:
#             if window_base >= play_num:
#                 logging.info(f"play number is {play_num} , the starting window is {window_base} please check !")
#                 assert False
#         elif play_num == 1:
#             if window_base != play_num:
#                 logging.info(f"play number is {play_num} , the starting window is {window_base} please check !")
#                 assert False
#
#         video_num = window_base - 2
#         while video_num < play_num - 1:
#             video_num += 1
#             video_cmd = self.video_cmd(video_num, action='stop')
#             if video_num > 0:
#                 self.__playerNum = 2
#             else:
#                 self.__playerNum = 1
#             self.check_stopPlay(cmd=video_cmd,
#                                 keywords=[f"[MediaPlayerBase_{video_num}] changeStatus: prevStatus=Playing, "
#                                           f"newStatus=Stopped"],
#                                 logFilter='logcat -s AmlMultiPlayer')
#
#     def video_Switch_Channel(self, play_num, window_base):
#         if play_num == 0:
#             logging.info(f"player number is {play_num} , please check !")
#             assert False
#         elif play_num != 1:
#             if window_base >= play_num:
#                 logging.info(f"play number is {play_num} , the starting window is {window_base} please check !")
#                 assert False
#         elif play_num == 1:
#             if window_base != play_num:
#                 logging.info(f"play number is {play_num} , the starting window is {window_base} please check !")
#                 assert False
#
#         video_num = window_base - 2
#         action = 'switch_channel'
#         while video_num < play_num - 1:
#             video_num += 1
#             video_cmd = self.APP_TEST + self.APP_TEST_WINDOW + f'{video_num} ' + self.APP_TEST_ACTION + f'{action}' + ' --ez is_play_next true'
#             if video_num < 1:
#                 self.__playerNum = 1
#             else:
#                 self.__playerNum = 2
#                 self.resume_playerNum = 2
#             self.check_switchChannel(cmd=video_cmd,
#                                      keywords=[
#                                          f"[MediaPlayerBase_{video_num}] changeStatus: prevStatus=Stopped, newStatus=Idle",
#                                          f"[MediaPlayerBase_{video_num}] changeStatus: prevStatus=Idle, newStatus=Init",
#                                          f"[MediaPlayerBase_{video_num}] changeStatus: prevStatus=Init, newStatus=Preparing",
#                                          f"[MediaPlayerBase_{video_num}] changeStatus: prevStatus=Preparing, "
#                                          f"newStatus=Prepared",
#                                          f"[MediaPlayerBase_{video_num}] changeStatus: prevStatus=Prepared, "
#                                          f"newStatus=Playing"],
#                                      logFilter='logcat -s AmlMultiPlayer')
#
#     def video_Seek(self, play_num, window_base, seek_play_time):
#         if play_num == 0:
#             logging.info(f"player number is {play_num} , please check !")
#             assert False
#         elif play_num != 1:
#             if window_base >= play_num:
#                 logging.info(f"play number is {play_num} , the starting window is {window_base} please check !")
#                 assert False
#         elif play_num == 1:
#             if window_base != play_num:
#                 logging.info(f"play number is {play_num} , the starting window is {window_base} please check !")
#                 assert False
#         play_time = seek_play_time
#         checked_log_play_duration = self.run_shell_cmd('logcat -s amlsource -e duration: -m 1 | grep "duration:"')[1]
#         play_duration = (checked_log_play_duration[-4:-1])
#         seek_time = p_config_multplayer['seek_time']
#         if seek_time is None:
#             logging.info("random seek")
#             play_duration = int(play_duration)
#             seek_time = random.randint(0, play_duration - play_time)
#             seek_time = seek_time * 1000
#         # seek
#         else:
#             seek_time = int(seek_time)
#         logging.info(f"seek time: {seek_time}")
#         video_num = window_base - 2
#         action = 'seek'
#         while video_num < play_num - 1:
#             video_num += 1
#             video_cmd = self.APP_TEST + self.APP_TEST_WINDOW + f'{video_num} ' + self.APP_TEST_ACTION + f'{action}' + f' --el seek_pos {seek_time}'
#             keywords = [f"[MediaPlayerBase_{video_num}] changeStatus: prevStatus=Playing, newStatus=Seeking",
#                         f"[MediaPlayerBase_{video_num}] changeStatus: prevStatus=Seeking, newStatus=Playing"]
#             logFilter = "logcat -s AmlMultiPlayer"
#             if video_num < 1:
#                 self.__playerNum = 1
#             else:
#                 self.__playerNum = 2
#                 self.resume_playerNum = 2
#             self.check_resume(video_cmd, keywords, logFilter, resume_playerNum=self.__playerNum)
#
#     def video_Speed(self, play_num, window_base):
#         if play_num == 0:
#             logging.info(f"player number is {play_num} , please check !")
#             assert False
#         elif play_num != 1:
#             if window_base >= play_num:
#                 logging.info(f"play number is {play_num} , the starting window is {window_base} please check !")
#                 assert False
#         elif play_num == 1:
#             if window_base != play_num:
#                 logging.info(f"play number is {play_num} , the starting window is {window_base} please check !")
#                 assert False
#         speed = p_config_multplayer['speed']
#         logging.info(f"speed:{speed}")
#
#         video_num = window_base - 2
#         action = 'setspeed '
#         while video_num < play_num - 1:
#             video_num += 1
#             video_cmd = self.APP_TEST + self.APP_TEST_WINDOW + f'{video_num} ' + self.APP_TEST_ACTION + f'{action}' + '--ef speed ' + f'{speed}'
#             if video_num < 1:
#                 self.__playerNum = 1
#             else:
#                 self.__playerNum = 2
#                 self.resume_playerNum = 2
#             keywords = ["[AUT]videoAction:setPlaybackRate"]
#             logging.info(keywords)
#             logFilter = 'logcat -s AmMediaSync'
#             logging.info(logFilter)
#             self.check_resume(video_cmd, keywords, logFilter, resume_playerNum=self.__playerNum)
#
#     def video_cmd(self, windows_num, action):
#         cmd = self.APP_TEST + self.APP_TEST_WINDOW + f'{windows_num} ' + self.APP_TEST_ACTION + f'{action}'
#         return cmd
