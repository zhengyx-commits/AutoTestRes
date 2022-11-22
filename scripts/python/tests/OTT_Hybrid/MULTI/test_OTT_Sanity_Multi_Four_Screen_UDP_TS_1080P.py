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
common_case = Common_Playcontrol_Case(playerNum=4)


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()
    streamProvider.stop_send()
    streamProvider1.stop_send()


# @pytest.mark.skip
def test_Multi_FOUR_SCREEN_UDP_TS_1080P():
    h264_1080P_stream_names, h264_1080P_url = get_conf_url("conf_udp_url", "udp", "conf_stream_name", "h264_1080P")
    if p_conf_single_stream:
        h264_1080P_1_stream_names, h264_1080P_1_url = get_conf_url("conf_udp_url", "udp", "conf_stream_name", "h264_1080P_1")
        for h264_1080P_stream_name, h264_1080P_1_stream_name in zip(h264_1080P_stream_names, h264_1080P_1_stream_names):
            file_path = streamProvider.get_file_path('h264_1080P', 'ts', h264_1080P_stream_name)
            file_path1 = streamProvider1.get_file_path('h264_1080P', 'ts', h264_1080P_1_stream_name)
            if file_path and file_path1:
                file_path = file_path[0]
                file_path1 = file_path1[0]
            try:
                streamProvider.start_send('udp', file_path)
                streamProvider1.start_send('udp1', file_path1)
            except Exception as e:
                logging.error("stream provider start send failed.")
                raise False
            if h264_1080P_url and h264_1080P_1_url:
                start_cmd = multi.get_start_cmd([h264_1080P_url, h264_1080P_1_url, h264_1080P_url, h264_1080P_1_url])
            else:
                start_cmd = multi.start_play_cmd(1, 'udp', 'udp1', 'udp', 'udp1')
            multi.send_cmd(start_cmd)
            assert common_case.player_check.check_startPlay()[0], "start play failed"

    else:
        file_path_list = []
        stream_name_list, h264_1080P_url = get_conf_url("conf_udp_url", "udp", "conf_stream_name", "h264_1080P")
        stream_name_list1, h264_1080P_url1 = get_conf_url("conf_udp_url", "udp1", "conf_stream_name", "h264_1080P")
        if len(h264_1080P_stream_names) != 0:
            for stream_name in h264_1080P_stream_names:
                file_path = streamProvider.get_file_path('h264_1080P', 'ts', stream_name)
                if file_path:
                    file_path = file_path[0]
                    file_path_list.append(file_path)

            for i in range(0, len(file_path_list) - 1):
                try:
                    streamProvider.start_send('udp', file_path_list[i])
                    streamProvider1.start_send('udp1', file_path_list[i+1])
                except Exception as e:
                    logging.error("stream provider start send failed.")
                    raise False
                start_cmd = multi.get_start_cmd([h264_1080P_url1, h264_1080P_url, h264_1080P_url, h264_1080P_url1])
                multi.send_cmd(start_cmd)
                assert common_case.player_check.check_startPlay()[0], "start play failed"
                multi.stop_multiPlayer_apk()
