# !/usr/bin python3
# -*- coding: utf-8 -*-
# @author     : jun.yang
# @software   : PyCharm
# @file       : test_OTT-Sanity_Youtube_SwitchVideo.py
# @Time       : 2023/3/10 下午14:00
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
    if youtube.getprop("ro.build.version.sdk") == "34":
        youtube.open_media_codec_info()
    else:
        youtube.open_omx_info()
    yield
    if youtube.getprop("ro.build.version.sdk") == "34":
        youtube.close_media_codec_info()
    else:
        youtube.close_omx_info()
    youtube.stop_youtube()


# @pytest.mark.skipif(condition=(1 - apk_exist), reason='apk not exist')
@pytest.mark.flaky(reruns=3)
def test_youtube_switch_video():
    # init youtube
    youtube.checkoutput(f'monkey -p {youtube.GOOGLE_YOUTUBE_PACKAGENAME} 1')
    time.sleep(20)

    # judge whether apk start is not
    start_time = time.time()
    current_window = youtube.run_shell_cmd('dumpsys window | grep -i mCurrentFocus')[1]
    if 'com.google.android.apps.youtube.tv.activity.MainActivity' not in current_window:
        while time.time() - start_time < 60:
            youtube.run_shell_cmd('input keyevent 3')
            time.sleep(5)
            youtube.checkoutput(f'monkey -p {youtube.GOOGLE_YOUTUBE_PACKAGENAME} 1')
            time.sleep(10)
            current_window = youtube.run_shell_cmd('dumpsys window | grep -i mCurrentFocus')[1]
            if 'com.google.android.apps.youtube.tv.activity.MainActivity' not in current_window:
                logging.debug("continue")
            else:
                break
    else:
        logging.debug("APK OK")
    if 'com.google.android.apps.youtube.tv.activity.MainActivity' not in current_window:
        raise ValueError("apk hasn't exited yet")
    else:
        logging.debug("APK OK")

    youtube.uiautomator_dump()
    if 'Choose an account' in youtube.get_dump_info():
        logging.info('first time playback youtube ')
        youtube.enter()
        time.sleep(20)
    playback_format = "VP9 and AV1"
    assert youtube.youtube_playback(playback_format, seekcheck=p_conf_seek_check)

