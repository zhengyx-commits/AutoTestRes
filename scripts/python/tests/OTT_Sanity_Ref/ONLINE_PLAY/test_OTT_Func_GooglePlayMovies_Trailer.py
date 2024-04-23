#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2023/3/16 14:00
# @Author  : jun.yang
# @Site    :
# @File    : test_OTT-Sanity_GooglePlayMovies_Trailer.py
# @Software: PyCharm
import time
import pytest
import logging
from lib.common.playback.GooglePlayMovies import GooglePlayMovies
from tests.OTT.lib.OTTNetset import OTTNetSet
from tests.OTT_Sanity_Ref import *

reboot_and_retore()
ott_netset = OTTNetSet()
playmovies = GooglePlayMovies()
apk_exist = playmovies.check_apk_exist()


# # googlemovies loggin check#
# def test_login():
#     ott_netset.start()
#     ott_netset.account_check()
@pytest.fixture(scope='module', autouse=True)
def setup_teardown():
    if android_version == "34":
        playmovies.run_shell_cmd("setprop debug.stagefright.c2-debug 3")
    yield
    playmovies.app_stop(playmovies.PLAYER_PACKAGE_TUPLE[0])
    if android_version == "34":
        playmovies.run_shell_cmd("setprop debug.stagefright.c2-debug 0")


# @pytest.mark.skipif(condition=(1 - apk_exist), reason='apk not exist')
# @pytest.mark.flaky(reruns=3)
@pytest.mark.skip(reason="No paid videos")
def test_google_play_trailer():
    playmovies.apk_enable(playmovies.PLAYER_PACKAGE_TUPLE[0])
    time.sleep(5)
    playmovies.start_activity(*playmovies.PLAYER_PACKAGE_TUPLE)
    time.sleep(10)

    # judge whether apk start is not
    start_time = time.time()
    current_window = playmovies.run_shell_cmd('dumpsys window | grep -i mCurrentFocus')[1]
    if 'com.google.android.apps.play.movies.tv.usecase.home.TvHomeActivity' not in current_window:
        while time.time() - start_time < 60:
            playmovies.run_shell_cmd('input keyevent 3')
            time.sleep(5)
            playmovies.start_activity(*playmovies.PLAYER_PACKAGE_TUPLE)
            time.sleep(10)
            current_window = playmovies.run_shell_cmd('dumpsys window | grep -i mCurrentFocus')[1]
            if 'com.google.android.apps.play.movies.tv.usecase.home.TvHomeActivity' not in current_window:
                logging.debug("continue")
            else:
                break
    else:
        logging.debug("APK OK")
    if 'com.google.android.apps.play.movies.tv.usecase.home.TvHomeActivity' not in current_window:
        raise ValueError("apk hasn't exited yet")
    else:
        logging.debug("APK OK")

    playmovies.wait_and_tap('Movies', 'text')
    time.sleep(2)
    playmovies.enter()
    time.sleep(5)
    playmovies.keyevent(20)
    time.sleep(5)
    playmovies.uiautomator_dump()
    playback_type = "trailer"
    playmovies.run_googleplaymovies(playback_type)
    playmovies.home()
    playmovies.app_stop(playmovies.PLAYER_PACKAGE_TUPLE[0])
