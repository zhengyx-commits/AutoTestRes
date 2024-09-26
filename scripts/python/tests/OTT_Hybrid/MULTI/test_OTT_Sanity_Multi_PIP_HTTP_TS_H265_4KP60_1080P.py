#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/4/22
# @Author  : jianhua.huang
import itertools

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
def test_Multi_PIP_HTTP_TS_H265_4KP60_1080P():
    if p_conf_single_stream:
        p_start_cmd = ""
        H265_4K_P60_urls = get_conf_url("conf_http_url", "http_TS_H265_4K_P60")
        H265_1080_urls = get_conf_url("conf_http_url", "http_TS_H265_1080")
        if len(H265_4K_P60_urls) != 0 and len(H265_1080_urls) != 0:
            for H265_4K_P60_url, H265_1080_url in zip(H265_4K_P60_urls, H265_1080_urls):
                p_start_cmd = multi.get_start_cmd([H265_4K_P60_url, H265_1080_url])
        else:
            p_start_cmd = multi.start_play_cmd(1, 'http_TS_H265_4K_P60', 'http_TS_H265_1080')
        multi.send_cmd(p_start_cmd)
        assert common_case.player_check.check_startPlay()[0], "start play failed"
        common_case.switch_pip_2_window()
        common_case.pause_resume_seek_stop()
    else:
        http_TS_H265_4K_P60_final_urllist = get_conf_url("conf_http_url", "http_TS_H265_4K_P60")
        http_TS_H265_1080_final_urllist = get_conf_url("conf_http_url", "http_TS_H265_1080")
        if len(http_TS_H265_4K_P60_final_urllist) != 0 and len(http_TS_H265_1080_final_urllist) != 0:
            urls = list(itertools.product(http_TS_H265_4K_P60_final_urllist, http_TS_H265_1080_final_urllist))
            for url in urls:
                url = list(url)
                start_cmd = multi.get_start_cmd([url[0], url[1]])
                multi.send_cmd(start_cmd)
                assert common_case.player_check.check_startPlay()[0], "start play failed"
                common_case.switch_pip_2_window()
                # common_case.pause_resume_seek_stop()
                multi.stop_multiPlayer_apk()
