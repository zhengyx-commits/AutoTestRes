#!/usr/bin/env python
#
# Copyright 2020 Amlogic.com, Inc. or its affiliates. All rights reserved.
#
# AMLOGIC PROPRIETARY/CONFIDENTIAL
#
# You may not use this file except in compliance with the terms and conditions
# set forth in the accompanying LICENSE.TXT file.
#
# THESE MATERIALS ARE PROVIDED ON AN "AS IS" BASIS. AMLOGIC SPECIFICALLY
# DISCLAIMS, WITH RESPECT TO THESE MATERIALS, ALL WARRANTIES, EXPRESS,
# IMPLIED, OR STATUTORY, INCLUDING THE IMPLIED WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.
#

import logging
import os
import time

import pytest

from lib.common import config_yaml
from lib.common.system.ADB import ADB
from lib.common.system.NetworkAuxiliary import getIfconfig
from lib.common.system.Permission import Permission
from lib.common.system.SignApk import SignApk, SignatureType
from tools.resManager import ResManager
from lib.common.playback import Environment_Detection


TIME_SLEEP = 2
TIMEOUT = 4
DEVICE_NAME = None
MULTIMEDIAPLAYER_TEST_APP_NAME = 'com.amlogic.multimediaplayer'
API_LEVEL_PROP = 'ro.build.version.sdk'
MANUFACTURER_PROP = 'ro.product.manufacturer'
SIGNED_APK = 'MultiMediaPlayer_inside_1.0_signed.apk'
CHECK_LOG = 'logcat -s AmlMultiPlayer'
ERROR_KEYWORDS = ["newStatus=Error"]
MULTI_APK = 'MultiMediaPlayer.apk'

# player_check = PlayerCheck


class MultiPlayer(Environment_Detection, ADB, SignApk):
    def __init__(self, device):
        # self.sn = MULTI.get_note('Multiplayer')['device_id']
        # print(self.sn)
        ADB.__init__(self, "MultiPlayerTestApp", unlock_code="", logdir=pytest.result_dir, stayFocus=True)
        SignApk.__init__(self)
        self.device = device
        self.resManager = ResManager()
        self._out_path = self.resManager.get_target("signed/")
        self._debug_apk_name = self.resManager.get_target(
            "debug/MultiMediaPlayer_inside_1.0_c1b1707_debug_202108021508.apk")
        self._signType = SignatureType.PLATFORM.value
        self.permission = Permission()
        # self.android_s_so_check()
        self.multi_setup()
        self.expand_logcat_capacity()
        # logging.debug(self._path)

        # MultiMediaPlayer APK command
        self.PAUSE_CMD = 'am broadcast -a multimediaplayer.test --ei instance_id 0 --es command pause'
        self.RESUME_CMD = 'am broadcast -a multimediaplayer.test --ei instance_id 0 --es command resume'
        self.STOP_CMD = 'am broadcast -a multimediaplayer.test --ei instance_id 0 --es command stop'
        self.SWITCH_CHANNEL = 'am broadcast -a multimediaplayer.test --ei instance_id 0 --es command switch_channel --ez is_play_next true'
        self.SWITCH_CHANNEL1 = 'am broadcast -a multimediaplayer.test --ei instance_id 1 --es command switch_channel --ez is_play_next true'
        self.SWITCH_WINDOW = 'am broadcast -a multimediaplayer.test --es command switch_window --ei source_window_id 0 --ei target_window_id 1'
        self.SEEK_CMD = 'am broadcast -a multimediaplayer.test --ei instance_id 0 --es command seek_offset --el seek_pos 20000'
        self.FF_CMD_1 = 'am broadcast -a multimediaplayer.test --ei instance_id 0 --es command setspeed --ef speed 1.5'
        self.FF_CMD_2 = 'am broadcast -a multimediaplayer.test --ei instance_id 0 --es command setspeed --ef speed 2.0'
        self.FB_CMD = 'am broadcast -a multimediaplayer.test --ei instance_id 0 --es command setspeed --ef speed 0.5'
        self.STANDARD_SPEED = 'am broadcast -a multimediaplayer.test --ei instance_id 0 --es command setspeed --ef speed 2.0'

    def get_url_dict(self):
        URL_DICT = {}
        iplist = getIfconfig()
        print(iplist)
        device_ip_sz = '192.168.1.246'
        if device_ip_sz in iplist:
            stream_ip = '192.168.1.247:8554'
            URL_DICT = {
                'http_TS_H264_1080': f'http://{device_ip_sz}/res/video/H264_1080P_PhilipsColorsofMiami_25M_25fps_5.5min.ts',
                'http_TS_H265_1080': f'http://{device_ip_sz}/res/video/[1080PH265_1764Kbps_8bit]1_aodaliya_24fps_1920x1080_h265shijun.ts',
                'http_TS_H265_1080_1': f"http://{device_ip_sz}/res/video/[1080PH265_1623Kbps_8bit]chengshizhiguang_1.5M_1920x1080_h265shijun.ts",
                'http_TS_1080i': f'http://{device_ip_sz}/res/video/MPEG2-1080I-30fps.ts',
                'http_TS_MPEG2_1080': f'http://{device_ip_sz}/res/video/MPEG2-1080I-30fps.ts',
                'http_TS_H264_4K': f'http://{device_ip_sz}/res/video/H264_UHD_PQ_Lovely_Swiss_HP_20M_60fps_3min40_logo.ts',
                'http_TS_H265_4K': f'http://{device_ip_sz}/res/video/H265_UHD_2015Hisense_28M_29.97fps_3min25s_logo.ts',
                'http_TS_H265_4K_P60': f'http://{device_ip_sz}/res/video/[4KH265_21.1Mbps_59.940fps_8bit]worldcup2014_8bit_19m_60p.ts',
                'hlsV3_TS_H264_1080': f'http://{device_ip_sz}/res/HLS_V3/H264/1080-HLSV3/index.m3u8',
                'hlsV3_TS_H265_1080': f'http://{device_ip_sz}/res/HLS_V3/H265/Chinese_Partners-1080P-H265-HLS/Chinese_Partners-1080P.m3u8',
                'hlsV3_TS_MPEG2_1080': f'http://{device_ip_sz}/res/HLS_V3/H265/...',
                'hlsV3_TS_H264_4K': f'http://{device_ip_sz}/res/HLS_V3/H265/...',
                'hlsV3_TS_H265_4K': f'http://{device_ip_sz}/res/HLS_V3/H265/4K-HLS-V3-H265-EAC3-TS/index.m3u8',
                'udp': "udp://239.1.2.1:1234",
                'udp1': "udp://239.1.2.2:1235",
                'rtsp_TS_H264_1080': f"rtsp://{stream_ip}/video/1080PH264_AC3.ts",
                'rtsp_TS_H265_1080': f"rtsp://{stream_ip}/video/H265_TEN_BA2_SAMSUNG_1080p_50P_20M_3min_cbr.ts",
                'rtsp_TS_MPEG2_1080': f"rtsp://{stream_ip}/video/MPEG2-1080I-30fps.ts",
                'rtsp_TS_H264_4K': f"rtsp://{stream_ip}/video/H264_Butterfly_4k_High@L5.1_AAC_30M_30fps_3min.ts",
                'rtsp_TS_H265_4K': f"rtsp://{stream_ip}/video/H265_UHD_2015Hisense_28M_29.97fps_3min25s_logo.ts",
                'rtp': "rtp://239.1.1.1:5004",
                'dynamic_pmt': f'http://{device_ip_sz}/res/video/video_pid_change_201_to_202.ts'
            }
        else:
            device_ip_sh = '192.168.1.100'
            stream_ip = '192.168.1.102:8554'
            URL_DICT = {
                'http_TS_H264_1080': f'http://{device_ip_sh}/res/video/H264_1080P_PhilipsColorsofMiami_25M_25fps_5.5min.ts',
                'http_TS_H265_1080': f'http://{device_ip_sh}/res/video/[1080PH265_1764Kbps_8bit]1_aodaliya_24fps_1920x1080_h265shijun.ts',
                'http_TS_H265_1080_1': f"http://{device_ip_sh}/res/video/[1080PH265_1623Kbps_8bit]chengshizhiguang_1.5M_1920x1080_h265shijun.ts",
                'http_TS_1080i': f'http://{device_ip_sh}/res/video/MPEG2-1080I-30fps.ts',
                'http_TS_MPEG2_1080': f'http://{device_ip_sh}/res/video/MPEG2-1080I-30fps.ts',
                'http_TS_H264_4K': f'http://{device_ip_sh}/res/video/H264_UHD_PQ_Lovely_Swiss_HP_20M_60fps_3min40_logo.ts',
                'http_TS_H265_4K': f'http://{device_ip_sh}/res/video/H265_UHD_2015Hisense_28M_29.97fps_3min25s_logo.ts',
                'http_TS_H265_4K_P60': f'http://{device_ip_sh}/res/video/[4KH265_21.1Mbps_59.940fps_8bit]worldcup2014_8bit_19m_60p.ts',
                'hlsV3_TS_H264_1080': f'http://{device_ip_sh}/res/HLS_V3/H264/1080-HLSV3/index.m3u8',
                'hlsV3_TS_H265_1080': f'http://{device_ip_sh}/res/HLS_V3/H265/Chinese_Partners-1080P-H265-HLS/Chinese_Partners-1080P.m3u8',
                'hlsV3_TS_MPEG2_1080': f'http://{device_ip_sh}/res/HLS_V3/H265/...',
                'hlsV3_TS_H264_4K': f'http://{device_ip_sh}/res/HLS_V3/H265/...',
                'hlsV3_TS_H265_4K': f'http://{device_ip_sh}/res/HLS_V3/H265/4K-HLS-V3-H265-EAC3-TS/index.m3u8',
                'udp': "udp://239.1.2.1:1234",
                'udp1': "udp://239.1.2.2:1235",
                'rtsp_TS_H264_1080': f"rtsp://{stream_ip}/video/1080PH264_AC3.ts",
                'rtsp_TS_H265_1080': f"rtsp://{stream_ip}/video/H265_TEN_BA2_SAMSUNG_1080p_50P_20M_3min_cbr.ts",
                'rtsp_TS_MPEG2_1080': f"rtsp://{stream_ip}/video/MPEG2-1080I-30fps.ts",
                'rtsp_TS_H264_4K': f"rtsp://{stream_ip}/video/H264_Butterfly_4k_High@L5.1_AAC_30M_30fps_3min.ts",
                'rtsp_TS_H265_4K': f"rtsp://{stream_ip}/video/H265_UHD_2015Hisense_28M_29.97fps_3min25s_logo.ts",
                'rtp': "rtp://239.1.1.1:5004",
                'dynamic_pmt': f'http://{device_ip_sh}/res/video/video_pid_change_201_to_202.ts'
            }
        return URL_DICT

    def check_multi_exist(self):
        return True if MULTIMEDIAPLAYER_TEST_APP_NAME in self.checkoutput('pm list packages') else False

    def multi_setup(self):
        if not self.check_multi_exist():
            assert self.install_apk("apk/" + MULTI_APK)
            self.start_multiPlayer_apk()
            time.sleep(5)
            self.get_permission()
        self.clear_logcat()

    def install_apk(self, apk_path):
        apk_path = self.resManager.get_target(apk_path)
        cmd = ['install', '-r', '-t', apk_path]
        logging.info(cmd)
        output = self.run_adb_cmd_specific_device(cmd)[1].decode().strip().split('\n')
        time.sleep(5)
        logging.info(output)
        if 'Success' in output:
            logging.info('APK install successful')
            return True
        else:
            logging.info('APK install failed')
            return False

    def app_install(self, apk_name):
        cmd = ['install', '-t', apk_name]
        logging.info(cmd)
        self.run_adb_cmd_specific_device(cmd, TIMEOUT)

    def app_uninstall(self, apk_name):
        cmd = ['uninstall', apk_name]
        logging.info(cmd)
        self.run_adb_cmd_specific_device(cmd, TIMEOUT)

    def get_permission(self):
        self.permission.permission_check()

    def check_multiplayer_apk_exist(self):
        rc, out = self.run_shell_cmd('pm list packages', TIMEOUT)
        packagelist = out.split()
        if len(packagelist) > 0:
            for item in packagelist:
                logging.debug(item)
                if MULTIMEDIAPLAYER_TEST_APP_NAME in item:
                    return True
            return False
        else:
            return False

    def start_multiPlayer_apk(self, start_flag=True):
        flag = 'true' if start_flag else 'false'
        cmd = 'am start -n ' + MULTIMEDIAPLAYER_TEST_APP_NAME + '/.MainActivity ' + '--ez start ' + flag
        logging.debug(cmd)
        self.shell(cmd)

    def stop_multiPlayer_apk(self):
        cmd = 'am force-stop ' + MULTIMEDIAPLAYER_TEST_APP_NAME
        logging.debug(cmd)
        self.shell(cmd)
        self.kill_logcat_pid()

    def startMultiPlayerTest(self, src_path=None):
        if src_path is None:
            raise ValueError('Param src_path is None.')
        else:
            if not os.path.exists(src_path):
                raise ValueError("src_path don't exists.")
        # self.hasDeviceToTest()
        self.device.root()
        manufacturer = self.getprop(MANUFACTURER_PROP, TIMEOUT)
        api_level = self.getprop(API_LEVEL_PROP, TIMEOUT)
        # self.adb_mount()
        signedApk = self.sign_apk(self._signType, manufacturer, api_level,
                                  self._debug_apk_name, self._out_path, SIGNED_APK)
        logging.info(signedApk)
        if self.check_multiplayer_apk_exist():
            self.app_uninstall(MULTIMEDIAPLAYER_TEST_APP_NAME)
            time.sleep(TIME_SLEEP)
            self.app_install(signedApk)
            time.sleep(TIME_SLEEP)
        else:
            self.app_install(signedApk)
            time.sleep(TIME_SLEEP)
        dest_path = '/sdcard/'
        self.push(src_path, dest_path)
        time.sleep(TIME_SLEEP)
        self.start_multiPlayer_apk()

    def get_startplay_params(self):
        p_conf_multi = config_yaml.get_note('conf_multiplayer')
        p_conf_is_loopplay = p_conf_multi['is_loopplay']
        p_conf_is_amumediaplayer = p_conf_multi['is_amumediaplayer']
        p_conf_is_ts_mode = p_conf_multi['is_ts_mode']
        p_conf_is_prefer_tunerhal = p_conf_multi['is_prefer_tunerhal']
        logging.debug(f"is_loopplay: {p_conf_is_loopplay}, is_amumediaplayer: {p_conf_is_amumediaplayer}, "
                      f"is_ts_mode: {p_conf_is_ts_mode}, is_prefer_tunerhal: {p_conf_is_prefer_tunerhal}")
        return p_conf_is_loopplay, p_conf_is_amumediaplayer, p_conf_is_ts_mode, p_conf_is_prefer_tunerhal

    def get_start_cmd(self, url_list, **kwargs):
        p_conf_is_loopplay, p_conf_is_amumediaplayer, p_conf_is_ts_mode, p_conf_is_prefer_tunerhal = self.get_startplay_params()
        urllist = ""
        if isinstance(url_list, list):
            if "2" in kwargs.values():
                urllist = str(';'.join(i for i in url_list))
            else:
                urllist = str(','.join(i for i in url_list))
        else:
            urllist = url_list
        print(urllist)
        start_cmd = (f'am start -n com.amlogic.multimediaplayer/.multiplay.MultiPlayActivity '
                     f'--esal url_list "{urllist}" --ez is_loopplay {p_conf_is_loopplay} '
                     f'--ez is_amumediaplayer {p_conf_is_amumediaplayer} --ez is_ts_mode {p_conf_is_ts_mode} '
                     f'--ez IS_prefer_tunerhal {p_conf_is_prefer_tunerhal}')
        print(start_cmd)
        return start_cmd

    def start_play_cmd(self, channel_num, *args):
        URL_DICT = self.get_url_dict()
        if channel_num == 1:
            url_list = str(','.join([URL_DICT[i] for i in list(args)]))
        else:
            url_list = str(';'.join([URL_DICT[i] for i in list(args)]))
        # url_list = str(','.join([self.url_dict[i] for i in list(args)]))
        start_cmd = self.get_start_cmd(url_list)
        return start_cmd

    def send_cmd(self, cmd):
        self.clear_logcat()
        self.run_shell_cmd(cmd)

    def check_multi_play(self):
        self.clear_logcat()
        p = self.popen(CHECK_LOG)
        start_time = time.time()
        p_conf_multi = config_yaml.get_note('conf_multiplayer')
        p_conf_check_play_time = p_conf_multi['check_play_time']
        logging.info(p_conf_check_play_time)
        while time.time() - start_time < p_conf_check_play_time:
            res = p.stdout.readline()
            logging.debug(f"res: {res}")
            for keyword in ERROR_KEYWORDS:
                if keyword in res:
                    logging.info(f"error keyword: {keyword}")
                    self.stop_multiPlayer_apk()
                    return False

