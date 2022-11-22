#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/4/22
# @Author  : jianhua.huang
import itertools

from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

common_case = Common_Playcontrol_Case(playerNum=4)


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()


# @pytest.mark.skip
def test_Four_Screen_Switch_Window_HTTP_TS_H265_1080P():
    H265_1080_urls = get_conf_url("conf_http_url", "http_TS_H265_1080")
    H265_4K_urls = get_conf_url("conf_http_url", "http_TS_H265_4K")
    H265_4K_P60_urls = get_conf_url("conf_http_url", "http_TS_H265_4K_P60")
    H265_1080_1_urls = get_conf_url("conf_http_url", "http_TS_H265_1080")
    if (len(H265_1080_urls) != 0 and len(H265_4K_P60_urls) != 0 and len(H265_4K_urls) != 0 and len(H265_1080_1_urls) != 0):
        urls = list(itertools.product(H265_1080_urls, H265_4K_urls, H265_4K_P60_urls, H265_1080_1_urls))
        for url in urls:
            url = list(url)
            p_start_play_cmd = multi.get_start_cmd([url[0], url[1], url[2], url[3]])
            print(p_start_play_cmd)
            multi.send_cmd(p_start_play_cmd)
            assert common_case.player_check.check_startPlay()[0], "start play failed"
            common_case.switch_pip_4_window()
            #common_case.pause_resume_seek_stop()
            multi.stop_multiPlayer_apk()
    else:
        p_start_play_cmd = multi.start_play_cmd(1, 'http_TS_H265_1080', 'http_TS_H265_4K', 'http_TS_H265_4K_P60', 'http_TS_H265_1080_1')
        multi.send_cmd(p_start_play_cmd)
        assert common_case.player_check.check_startPlay()[0], "start play failed"
        common_case.switch_pip_4_window()
        #common_case.pause_resume_seek_stop()
