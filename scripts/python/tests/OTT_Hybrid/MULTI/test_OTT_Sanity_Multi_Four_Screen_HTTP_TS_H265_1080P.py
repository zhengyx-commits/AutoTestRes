#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/4/22
# @Author  : jianhua.huang
import numpy

from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *
from random import choice
import itertools

common_case = Common_Playcontrol_Case(playerNum=4)


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()


# @pytest.mark.skip
def test_Multi_FOUR_SCREEN_HTTP_TS_H265_1080P():
    http_TS_H265_1080_urls = get_conf_url("conf_http_url", "http_TS_H265_1080")
    if p_conf_single_stream:
        http_TS_H265_1080_1_urls = get_conf_url("conf_http_url", "http_TS_H265_1080")
        if len(http_TS_H265_1080_urls) != 0 and len(http_TS_H265_1080_1_urls) != 0:
            urls = list(itertools.product(http_TS_H265_1080_urls, http_TS_H265_1080_1_urls))
            # print(f"urls: {urls}")
            for url in urls:
                url = list(url)
                # print(f"url[0]:{url[0]}")
                # print(f"url[1]:{url[1]}")
                p_start_cmd = multi.get_start_cmd([url[0], url[0], url[1], url[1]])
                multi.send_cmd(p_start_cmd)
                assert common_case.player_check.check_startPlay()[0], "start play failed"
                common_case.switch_pip_4_window()
                # common_case.pause_resume_seek_stop()
                multi.stop_multiPlayer_apk()
        else:
            p_start_cmd = multi.start_play_cmd(1, 'http_TS_H265_1080', 'http_TS_H265_1080_1', 'http_TS_H265_1080',
                                               'http_TS_H265_1080_1')
            multi.send_cmd(p_start_cmd)
            assert common_case.player_check.check_startPlay()[0], "start play failed"
            common_case.switch_pip_4_window()
            # common_case.pause_resume_seek_stop()
    else:  # get file from directory
        if len(http_TS_H265_1080_urls) != 0:
            new_url_list = numpy.stack([http_TS_H265_1080_urls, sorted(http_TS_H265_1080_urls, reverse=True)],
                                       0).tolist()
            # urls = list(itertools.product(http_TS_H265_1080_urls, http_TS_H265_1080_urls))
            # print(f"new_url_list: {new_url_list}")
            for url in new_url_list:
                url = list(url)
                p_start_cmd = multi.get_start_cmd([url[0], url[1], url[2], choice(url)])
                # print(p_start_cmd)
                multi.send_cmd(p_start_cmd)
                assert common_case.player_check.check_startPlay()[0], "start play failed"
                common_case.switch_pip_4_window()
                # common_case.pause_resume_seek_stop()
                multi.stop_multiPlayer_apk()
