#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2021/12/27 10:15
# @Author  : chao.li
# @Site    :
# @File    : test_OTT-Sanity_TIF.py
# @Software: PyCharm
import pytest
import time
from lib.OTT.S905Y4.HybridDTV import HybirdDtv
from lib.OTT.S905Y4.HybridGooglePlayMovies import HybridGooglePlayMovies
from lib.OTT.S905Y4.HybridNetflix import HybridNetflix
from lib.OTT.S905Y4.HybridYoutbe import HybridYoutbe
import logging

dtv = HybirdDtv()
googleplay = HybridGooglePlayMovies()
netflix = HybridNetflix()
youtube = HybridYoutbe()


@pytest.mark.repeat(1)
def test_tif():
    # DTV 播放
    dtv.playback()
    # playchecker.run_check_main_thread(30)
    time.sleep(30)

    # init youtube
    youtube.checkoutput(f'monkey -p {youtube.PACKAGE_NAME} 1')
    time.sleep(20)
    youtube.uiautomator_dump()
    if 'Choose an account' in youtube.get_dump_info():
        logging.info('first time playback youtube ')
        youtube.keyevent(23)
        youtube.keyevent(23)
        time.sleep(20)
        youtube.keyevent(4)
        youtube.keyevent(4)
        youtube.keyevent(4)
        youtube.keyevent(4)
    # youtube 播放
    youtube.playback(activity)
    assert youtube.check_playback_status(), 'playback not success'
    time.sleep(30)
    # playchecker.run_check_main_thread(30)
    # time.sleep(30)

    # netflix init
    netflix.netflix_setup()
    # netflix 播放
    netflix.playback(activity)
    assert netflix.check_playback_status(), 'playback not success'
    time.sleep(30)
    # playchecker.run_check_main_thread(30)
    # time.sleep(30)

    # googlemovies 播放
    googleplay.start_activity(*googleplay.PLAYER_PACKAGE_TUPLE)
    time.sleep(3)
    googleplay.keyevent(20)
    googleplay.wait_and_tap('Movies', 'text')
    googleplay.enter()
    time.sleep(5)
    googleplay.uiautomator_dump()
    i = googleplay.get_movies_list()[0]
    googleplay.wait_and_tap(i, 'text')
    googleplay.enter()
    time.sleep(5)
    if googleplay.u2.d.exists(text='PLAY MOVIE'):
        googleplay.find_and_tap('PLAY MOVIE', 'text')
        googleplay.enter()
    else:
        googleplay.find_and_tap('PLAY FROM BEGINNING', 'text')
        googleplay.enter()
    assert googleplay.check_playback_status(), 'playback not success'
    # googleplay.playerCheck.run_check_main_thread(30)
    time.sleep(30)
