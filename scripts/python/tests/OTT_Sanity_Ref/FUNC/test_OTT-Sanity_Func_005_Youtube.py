# !/usr/bin python3
# -*- coding: utf-8 -*-
# @author     : chao.li
# @software   : PyCharm
# @file       : test_OTT-Sanity_Func_071-074_Youtube.py
# @Time       : 2021/7/8 上午8:44
import logging

from lib.common.playback.Youtube import Youtube
# from lib.OTT.S905X4.PlayerCheck import AH212PlayerCheck
import pytest
import time
from tests.OTT_Sanity_Ref import config_yaml

youtube = Youtube()
# playerCheck = AH212PlayerCheck()
apk_exist = youtube.check_apk_exist()
config_seek_press_event = config_yaml.get_note('conf_seek_press_event')
p_conf_seek_check = config_seek_press_event['seek_enable']


@pytest.fixture(scope='module', autouse=True)
def setup_teardown():
    # 开启omx 打印
    youtube.open_omx_info()
    yield
    youtube.close_omx_info()


@pytest.mark.skipif(condition=(1 - apk_exist), reason='apk not exist')
def test_online_video():
    # init youtube
    youtube.checkoutput(f'monkey -p {youtube.GOOGLE_YOUTUBE_PACKAGENAME} 1')
    time.sleep(20)
    youtube.uiautomator_dump()
    if 'Choose an account' in youtube.get_dump_info():
        logging.info('first time playback youtube ')
        youtube.enter()
        time.sleep(20)
    youtube.youtube_playback(seekcheck=p_conf_seek_check)
    youtube.home()
