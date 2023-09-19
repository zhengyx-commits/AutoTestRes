#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2021/7/15 15:50
# @Author  : chao.li
# @Site    :
# @File    : test_OTT-Sanity_Func_084-085_GooglePlayMovies.py
# @Software: PyCharm
import time
import pytest
from lib.common.playback.GooglePlayMovies import GooglePlayMovies
from tests.OTT.lib.OTTNetset import OTTNetSet

ott_netset = OTTNetSet()
playmovies = GooglePlayMovies()
apk_exist = playmovies.check_apk_exist()


# # googlemovies loggin check#
# def test_login():
#     ott_netset.start()
#     ott_netset.account_check()


@pytest.mark.skipif(condition=(1 - apk_exist), reason='apk not exist')
def test_online_video():
    playmovies.apk_enable(playmovies.PLAYER_PACKAGE_TUPLE[0])
    time.sleep(5)
    playmovies.start_activity(*playmovies.PLAYER_PACKAGE_TUPLE)
    time.sleep(10)
    playmovies.wait_and_tap('Movies', 'text')
    time.sleep(2)
    playmovies.enter()
    time.sleep(5)
    playmovies.keyevent(20)
    time.sleep(5)
    playmovies.uiautomator_dump()
    playmovies.run_googleplaymovies()
    playmovies.home()
    playmovies.app_stop(playmovies.PLAYER_PACKAGE_TUPLE[0])
