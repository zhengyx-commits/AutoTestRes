#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/6/21
# @Author  : yongbo.shao
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
def test_Multi_PIP_HTTP_TS_1080i():
    final_urllist = get_conf_url("conf_http_url", "http_TS_1080i")
    if p_conf_single_stream:
        for item in final_urllist:
            start_cmd = multi.get_start_cmd([item, item])
            multi.send_cmd(start_cmd)
            assert common_case.player_check.check_startPlay()[0], "start play failed"
            common_case.switch_pip_2_window()
            common_case.pause_resume_seek_stop()
            multi.stop_multiPlayer_apk()
    else:
        # urls = list(itertools.product(final_urllist, final_urllist))
        urls = numpy.stack([final_urllist, sorted(final_urllist, reverse=True)], 1).tolist()
        for url in urls:
            url = list(url)
            # print(f"url[0]:{url[0]}")
            # print(f"url[1]:{url[1]}")
            p_start_cmd = multi.get_start_cmd([url[0], url[1]])
            multi.send_cmd(p_start_cmd)
            assert common_case.player_check.check_startPlay()[0], "start play failed"
            common_case.switch_pip_2_window()
            common_case.pause_resume_seek_stop()
            multi.stop_multiPlayer_apk()
