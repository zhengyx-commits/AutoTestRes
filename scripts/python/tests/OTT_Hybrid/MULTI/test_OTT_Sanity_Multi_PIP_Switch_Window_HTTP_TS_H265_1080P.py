#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/4/22
# @Author  : jianhua.huang
import itertools

import numpy

from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

common_case = Common_Playcontrol_Case(playerNum=2)


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()


# @pytest.mark.skip
@pytest.mark.flaky(reruns=3)
def test_PIP_Switch_Window_HTTP_TS_H265_1080P():
    # url = get_conf_url("conf_http_url", "http_TS_H265_1080")
    # if url:
    #     p_start_play_cmd = multi.get_start_cmd([url, url])
    # else:
    #     p_start_play_cmd = multi.start_play_cmd(1, 'http_TS_H265_1080', 'http_TS_H265_1080')
    finalurl_list = get_conf_url("conf_http_url", "http_TS_H265_1080")
    if p_conf_single_stream:
        for item in finalurl_list:
            start_cmd = multi.get_start_cmd([item, item])
            multi.send_cmd(start_cmd)
            assert common_case.player_check.check_startPlay()[0], "start play failed"
            common_case.switch_pip_2_window()
            multi.stop_multiPlayer_apk()
    else:
        urls = list(zip(finalurl_list, sorted(finalurl_list, reverse=True)))
        for url in urls:
            p_start_cmd = multi.get_start_cmd([url[0], url[1]])
            multi.send_cmd(p_start_cmd)
            assert common_case.player_check.check_startPlay()[0], "start play failed"
            common_case.switch_pip_2_window()
            multi.stop_multiPlayer_apk()
