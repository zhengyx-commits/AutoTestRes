# !/usr/bin python3
# -*- coding: utf-8 -*-
# @author     : chao.li
# @software   : PyCharm
# @file       : test_OTT-Sanity_Func_071-074_Youtube.py
# @Time       : 2021/7/8 上午8:44
import logging
from lib.common.playback.Youtube import Youtube
from lib.common.checkpoint.PlayerCheck_Base import PlayerCheck_Base
from tests.OTT_Hybrid import config_yaml
import pytest
import time

youtube = Youtube()
playerCheck = PlayerCheck_Base()
apk_exist = youtube.check_Youtube_exist()

p_conf_online = config_yaml.get_note('conf_online')
p_conf_check_seek_enable = p_conf_online['check_seek_enable']


# logging.info(f'Youtube p_conf_check_seek_enable:{p_conf_check_seek_enable}')

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
        youtube.home()
        time.sleep(20)
    youtube.youtube_playback(seekcheck=p_conf_check_seek_enable)
    youtube.home()