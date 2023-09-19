#!/usr/bin/env python
# -*- coding: utf-8 -*-/
# @Time    : 2022/4/22
# @Author  : jianhua.huang

import logging
from tools.StreamProvider import StreamProvider
from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

streamProvider = StreamProvider()

common_case = Common_Playcontrol_Case(playerNum=2)


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()
    streamProvider.stop_send()


# @pytest.mark.skip
@pytest.mark.flaky(reruns=3)
def test_PIP_Switch_Window_UDP_TS_1080P():
    stream_name_list, url = get_conf_url("conf_udp_url", "udp", "conf_stream_name", "h264_1080P")
    for stream_name in stream_name_list:
        file_path = streamProvider.get_file_path('h264_1080P', 'ts', stream_name)
        if file_path:
            file_path = file_path[0]
            try:
                streamProvider.start_send('udp', file_path, url=url[6:])
            except Exception as e:
                logging.error("stream provider start send failed.")
                raise False
            if url:
                start_cmd = multi.get_start_cmd([url, url])
            else:
                start_cmd = multi.start_play_cmd(1, 'udp', 'udp')
            multi.send_cmd(start_cmd)
            assert common_case.player_check.check_startPlay()[0], "start play failed"
            common_case.switch_pip_2_window()
            # common_case.pause_resume_seek_stop()
            multi.stop_multiPlayer_apk()
            streamProvider.stop_send()
