#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/4/22
# @Author  : jianhua.huang

import logging
from tools.StreamProvider import StreamProvider
from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

streamProvider = StreamProvider()
streamProvider1 = StreamProvider()
common_case = Common_Playcontrol_Case(playerNum=2)


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.multi_setup()
    yield
    # multi.stop_multiPlayer_apk()
    # streamProvider.stop_send()


# @pytest.mark.skip
@pytest.mark.flaky(reruns=3)
def test_Multi_PIP_UDP_TS_H265_1080():
    h264_1080P_stream_name, h264_1080P_url = get_conf_url("conf_udp_url", "udp", "conf_stream_name", "h264_1080P")
    if p_conf_single_stream:
        h264_1080P_1_stream_name, h264_1080P_1_url = get_conf_url("conf_udp_url", "udp1", "conf_stream_name", "h264_1080P_1") 
        file_path = streamProvider.get_file_path('h264_1080P', 'ts', h264_1080P_stream_name[0])
        file_path1 = streamProvider1.get_file_path('h264_1080P', 'ts', h264_1080P_1_stream_name[0])
        if file_path and file_path1:
            file_path = file_path[0]
            file_path1 = file_path1[0]
        try:
            streamProvider.start_send('udp', file_path, url=h264_1080P_url[6:])
            streamProvider1.start_send('udp', file_path1, url=h264_1080P_1_url[6:])
        except Exception as e:
            logging.error("stream provider start send failed.")
            raise False
        if h264_1080P_url and h264_1080P_1_url:
            start_cmd = multi.get_start_cmd([h264_1080P_url, h264_1080P_1_url])
        else:
            start_cmd = multi.start_play_cmd(1, 'udp', 'udp1')
        multi.send_cmd(start_cmd)
        assert common_case.player_check.check_startPlay()[0], "start play failed"
        common_case.switch_pip_2_window()
        multi.stop_multiPlayer_apk()
        streamProvider.stop_send()
        #common_case.pause_resume_seek_stop()
    else:
        file_path_list = []
        stream_name_list, url = get_conf_url("conf_udp_url", "udp", "conf_stream_name", "h264_1080P")
        stream_name_list, url1 = get_conf_url("conf_udp_url", "udp1", "conf_stream_name", "h264_1080P_1")
        if len(h264_1080P_stream_name) != 0:
            for stream_name in h264_1080P_stream_name:
                file_path = streamProvider.get_file_path('h264_1080P', 'ts', stream_name)
                if file_path:
                    file_path = file_path[0]
                    file_path_list.append(file_path)

            for i in range(0, len(file_path_list) - 1):
                try:
                    streamProvider.start_send('udp', file_path_list[i], url=url[6:])
                    streamProvider1.start_send('udp', file_path_list[i + 1], url=url1[6:])
                except Exception as e:
                    logging.error("stream provider start send failed.")
                    raise False
                if url and url1:
                    start_cmd = multi.get_start_cmd([url, url1])
                    multi.send_cmd(start_cmd)
                    assert common_case.player_check.check_startPlay()[0], "start play failed"
                    common_case.switch_pip_2_window()
                    #common_case.pause_resume_seek_stop()
                    multi.stop_multiPlayer_apk()
                    streamProvider.stop_send()
                    streamProvider1.stop_send()
