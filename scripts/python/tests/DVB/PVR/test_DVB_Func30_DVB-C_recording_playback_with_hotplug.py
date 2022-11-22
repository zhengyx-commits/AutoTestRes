#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/7/13 10:32
# @Author  : chao.li
# @Site    :
# @File    : test_DVB_Func30_DVB-C_recording_playback_with_hotplug.py
# @Software: PyCharm


import time
import logging

from ..PVR import pytest, dvb_stream, dvb, dvb_check, playerCheck

video_name = 'gr1'

SUSPENG = "am broadcast -n com.droidlogic.suspend/.SuspendReceiver -a suspend.test --es command suspend"
WAKEUP = "am broadcast -n com.droidlogic.suspend/.SuspendReceiver -a suspend.test --es command wakeup"


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    dvb_stream.start_dvbc_stream(video_name)
    dvb.start_livetv_apk()
    if not dvb.check_apk_exist("com.droidlogic.suspend"):
        logging.info('installing')
        dvb.install_apk('apk/testSuspend2.apk')
    time.sleep(1)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


@pytest.mark.skip
def test_hotplug_u_disk():
    dvb.pvr_start_play()
    # Todo @chao.li hotplug u-disk
    dvb.pvr_start_play()
    dvb_check.check_play_status_main_thread(timeout=30)
    dvb.keyevent(19)
    dvb_check.check_play_status_main_thread(timeout=30)
    dvb.pvr_seek(0)
    dvb_check.check_play_status_main_thread(timeout=30)
    dvb.pvr_pause()
    # Todo @chao.li make sure playback is pause


# @pytest.mark.flaky(reruns=3)
def test_hotplug_rf():
    assert dvb.getUUID() != 'emulated', "Doesn't get u-disk"
    dvb.start_pvr_recording()
    dvb_check.check_start_pvr_recording()
    time.sleep(120)
    dvb.stop_pvr_recording()
    dvb_check.check_stop_pvr_recording()
    dvb.pvr_start_play()
    logging.info('Pvr start')
    assert dvb_check.check_pvr_start_play()
    time.sleep(5)
    dvb_stream.stop_dvb()
    dvb_stream.start_dvbc_stream(video_name)
    time.sleep(3)
    dvb.pvr_seek(seek_time=3)
    logging.info('Pvr seek')
    assert dvb_check.check_pvr_seek(3)
    dvb.pvr_pause()
    time.sleep(3)
    logging.info('Pvr pause')
    assert dvb_check.check_pvr_pause()
    time.sleep(3)
    dvb.pvr_resume()
    logging.info('Pvr resume')
    assert dvb_check.check_pvr_resume()
    dvb_check.check_play_status_main_thread(timeout=30)
    dvb.pvr_stop()
    logging.info('Pvr stop')
    assert dvb_check.check_pvr_stop()


# @pytest.mark.flaky(reruns=3)
def test_hotplug_dc():
    assert dvb.getUUID() != 'emulated', "Doesn't get u-disk"
    dvb.pvr_start_play()
    assert dvb_check.check_pvr_start_play()
    time.sleep(10)
    dvb.checkoutput(SUSPENG)
    time.sleep(10)
    dvb.checkoutput(WAKEUP)
    time.sleep(3)
    dvb.pvr_replay()
    assert dvb_check.check_pvr_start_play()
    dvb_check.check_play_status_main_thread(timeout=30)
    dvb.pvr_seek(seek_time=5)
    assert dvb_check.check_pvr_seek(5)
    time.sleep(3)
    dvb.pvr_seek(seek_time=-5)
    assert dvb_check.check_pvr_seek(-1)
    time.sleep(3)
    dvb.pvr_pause()
    assert dvb_check.check_pvr_pause()
    time.sleep(3)
    dvb.pvr_resume()
    assert dvb_check.check_pvr_resume()
    dvb.pvr_stop()
    assert dvb_check.check_pvr_stop()
