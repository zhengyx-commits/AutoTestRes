#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/6/23
# @Author  : yongbo.shao
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
def test_PIP_Small_Window_Switch_Channel_HTTP_TS_H265_4K():
    if p_conf_single_stream:
        urls = get_conf_url("conf_http_url", "http_TS_H265_4K")
        for url in urls:
            if url:
                start_play_cmd = multi.get_start_cmd([url, url])
            else:
                start_play_cmd = multi.start_play_cmd(1, 'http_TS_H265_4K', 'http_TS_H265_4K')
            multi.send_cmd(start_play_cmd)
            assert common_case.player_check.check_startPlay()[0], "start play failed"
            # focus on check
            common_case.player_check.keyevent(22)
            assert common_case.player_check.check_common_threadpool()
            switch_channel_cmd = multi.SWITCH_CHANNEL1
            multi.send_cmd(switch_channel_cmd)
            assert common_case.player_check.check_switchChannel()[0]
    else:
        finalurl_list = get_conf_url("conf_http_url", "http_TS_H265_4K")
        for i in range(0, len(finalurl_list)-1):
            start_cmd = multi.get_start_cmd([finalurl_list[i], finalurl_list[i+1]])
            multi.send_cmd(start_cmd)
            assert common_case.player_check.check_startPlay()[0], "start play failed"
            # focus on check
            common_case.player_check.keyevent(22)
            assert common_case.player_check.check_common_threadpool()
            switch_channel_cmd = multi.SWITCH_CHANNEL
            multi.send_cmd(switch_channel_cmd)
            assert common_case.player_check.check_switchChannel()[0]
            multi.stop_multiPlayer_apk()

