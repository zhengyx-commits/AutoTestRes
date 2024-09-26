#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/7/13 10:32
# @Author  : chao.li
# @Site    :
# @File    : test_DVB_Func30_DVB-C_recording_playback_with_hotplug.py
# @Software: PyCharm


import time
import logging
import os
from ..PVR import pytest, dvb_stream, dvb, dvb_check
from tools.yamlTool import yamlTool
from lib.common.tools.Subtitle import Subtitle

subtitle = Subtitle()
video_name = 'BBC_MUX_UH'

SUSPENG = "am broadcast -n com.droidlogic.suspend/.SuspendReceiver -a suspend.test --es command suspend"
WAKEUP = "am broadcast -n com.droidlogic.suspend/.SuspendReceiver -a suspend.test --es command wakeup"

config_yaml = yamlTool(os.getcwd() + '/config/config_dvb.yaml')
p_conf_dvb = config_yaml.get_note('conf_stress')
p_conf_repeat_count = p_conf_dvb['30_pvr_basic_function_count']


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    dvb_stream.start_dvbc_stream(video_name)
    dvb.start_livetv_apk_and_manual_scan()
    if not dvb.check_apk_exist("com.droidlogic.suspend"):
        android_version = dvb.getprop(key="ro.build.version.release")
        logging.debug(f"android version: {android_version}")
        if android_version == '14':
            apk_name = "testSuspend2_U.apk"
        else:
            apk_name = "testSuspend2.apk"
        logging.info('installing')
        dvb.install_apk('apk/' + apk_name)
    time.sleep(1)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.flaky(reruns=3)
def test_hotplug_rf():
    assert dvb.getUUID() != 'emulated', "Doesn't get u-disk"
    dvb.start_pvr_recording()
    assert dvb_check.check_start_pvr_recording()
    # subtitle.check_subtitle_thread('Dvb', 'LiveTv')
    time.sleep(90)
    # dvb_stream.pause_dvb()
    # dvb_stream.resume_dvbc_stream(video_name)
    # time.sleep(60)
    dvb.stop_pvr_recording()
    assert dvb_check.check_stop_pvr_recording()
    dvb.pvr_start_play()
    logging.info('Pvr start')
    assert dvb_check.check_pvr_start_play()
    time.sleep(5)
    dvb_check.check_play_status_sub_thread()
    for i in range(p_conf_repeat_count):
        logging.info(f'------The {i + 1} times------')
        dvb.pvr_current_seek(seek_time=5)
        logging.info('Pvr seek')
        assert dvb_check.check_pvr_current_seek(5)
        dvb.pvr_current_seek(seek_time=-5)
        logging.info('Pvr seek')
        assert dvb_check.check_pvr_current_seek(-5)
        dvb.pvr_pause()
        time.sleep(3)
        logging.info('Pvr pause')
        assert dvb_check.check_pvr_pause()
        time.sleep(3)
        dvb.pvr_resume()
        logging.info('Pvr resume')
        assert dvb_check.check_pvr_resume()
        # dvb_check.check_play_status_main_thread(timeout=10)
    # dvb.pvr_stop()
    # logging.info('Pvr stop')
    # assert dvb_check.check_pvr_stop()
