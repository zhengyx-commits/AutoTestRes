#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2021/7/15 15:50
# @Author  : chao.li
# @Site    :
# @File    : test_OTT-Sanity_Func_084-085_GooglePlayMovies.py
# @Software: PyCharm
import time
import pytest
import logging
from lib.OTT.S905X4.GooglePlayMovies import AH212GooglePlayMovies
from tests.OTT.lib.OTTNetset import OTTNetSet

ott_netset = OTTNetSet()
playmovies = AH212GooglePlayMovies()
apk_exist = playmovies.check_apk_exist()


# googlemovies loggin check#
def test_login():
    playmovies.start_activity(*playmovies.PLAYER_PACKAGE_TUPLE)
    if playmovies.wait_and_tap('Sign in', 'text'):
        ott_netset.text("amlogictest1@gmail.com")
        ott_netset.back()
        for i in range(2):
            ott_netset.keyevent("KEYCODE_DPAD_DOWN")
        ott_netset.keyevent("KEYCODE_DPAD_RIGHT")
        ott_netset.enter()
        time.sleep(5)
        ott_netset.text("amltest123")
        ott_netset.back()
        for i in range(2):
            ott_netset.keyevent("KEYCODE_DPAD_DOWN")
        ott_netset.keyevent("KEYCODE_DPAD_RIGHT")
        ott_netset.enter()
        time.sleep(5)
    else:
        logging.info("already login")
    playmovies.app_stop(playmovies.PLAYER_PACKAGE_TUPLE[0])


@pytest.mark.skipif(condition=(1 - apk_exist), reason='apk not exist')
def test_online_video():
    playmovies.start_activity(*playmovies.PLAYER_PACKAGE_TUPLE)
    playmovies.keyevent(22)
    playmovies.wait_and_tap('Movies', 'text')
    playmovies.enter()
    time.sleep(5)
    playmovies.uiautomator_dump()
    playmovies.run_googleplaymovies()
    playmovies.home()
    playmovies.app_stop(playmovies.PLAYER_PACKAGE_TUPLE[0])
