#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/8/1 10:18
# @Author  : chao.li
# @Site    :
# @File    : test_DVB_Func19_DVB-C_play_multi_subtitle_program.py
# @Software: PyCharm


import time
import logging

from ..PVR import pytest, dvb_stream, dvb, dvb_check, playerCheck
from lib.common.tools.Subtitle import Subtitle

video_name = 'hbo'
subtitle = Subtitle()


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    dvb_stream.start_dvbc_stream(video_name)
    dvb.start_livetv_apk()
    time.sleep(3)
    for i in range(20):
        number = dvb.get_subtitle_list()
        logging.info(f'number {number}')
        if number != 0:
            break
        dvb.keyevent(19)
        time.sleep(3)
    else:
        raise EnvironmentError('Not subtitle found!')
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.flaky(reruns=3)
def test_play_multi_language_program():
    assert dvb.getUUID() != 'emulated', "Doesn't get u-disk"
    # subtitle_type = dvb_check.get_subtitle_mode('ts')
    dvb.start_pvr_recording()
    assert dvb_check.check_start_pvr_recording()
    time.sleep(30)
    dvb.switch_subtitle_type(0)
    subtitle.start_subtitle_datathread('Teletext', 'LiveTv')
    time.sleep(15)
    logging.info(
        f'subtitle.error : {subtitle.error}  ;subtitle.got_spu : {subtitle.got_spu}; subtitle.show_spu : {subtitle.show_spu}')
    assert (subtitle.error == 0) & (subtitle.got_spu != '') & (
            subtitle.show_spu != ''), 'There are some problems with the subtitle shows'
    time.sleep(15)
    dvb.stop_pvr_recording()
    assert dvb_check.check_stop_pvr_recording()
    dvb.pvr_start_play()
    assert dvb_check.check_pvr_start_play()
    dvb_check.check_play_status_main_thread(timeout=30)
    dvb.pvr_stop()
    assert dvb_check.check_pvr_stop()
