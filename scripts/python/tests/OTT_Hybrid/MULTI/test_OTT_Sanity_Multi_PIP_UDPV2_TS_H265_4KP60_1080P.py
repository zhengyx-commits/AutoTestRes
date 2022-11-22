#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/6/21
# @Author  : yongbo.shao


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
    multi.stop_multiPlayer_apk()
    streamProvider.stop_send()
    streamProvider1.stop_send()


# @pytest.mark.skip
def test_Multi_PIP_UDPV2_TS_H265_4KP60_1080P():
    if p_conf_single_stream:
        stream_name_2015Hisense, Hisense_url = get_conf_url("conf_udp_url", "udp", "conf_stream_name", "h265_4K")
        stream_name_SAMSUNG, SAMSUNG_url = get_conf_url("conf_udp_url", "udp1", "conf_stream_name", "h265_1080P")
        file_path = streamProvider.get_file_path('h265_4K', 'ts', stream_name_2015Hisense[0])
        file_path1 = streamProvider1.get_file_path('h265_1080P', 'ts', stream_name_SAMSUNG[0])
        if file_path and file_path1:
            file_path = file_path[0]
            file_path1 = file_path1[0]
        try:
            streamProvider.start_send('udp', file_path)
            streamProvider1.start_send('udp1', file_path1)
        except Exception as e:
            logging.error("stream provider start send failed.")
            raise False
        if Hisense_url and SAMSUNG_url:
            start_cmd = multi.get_start_cmd([Hisense_url, SAMSUNG_url])
        else:
            start_cmd = multi.start_play_cmd(1, 'udp', 'udp1')
        multi.send_cmd(start_cmd)
        assert common_case.player_check.check_startPlay()[0], "start play failed"
    else:
        file_path_list = []
        h264_1080P_list, url = get_conf_url("conf_udp_url", "udp", "conf_stream_name", "h264_1080P")
        h265_4k_list, url1 = get_conf_url("conf_udp_url", "udp1", "conf_stream_name", "h265_4K")
        if len(h264_1080P_list) != 0 and len(h265_4k_list) != 0:
            for stream_name in h264_1080P_list:
                file_path = streamProvider.get_file_path('h264_1080P', 'ts', stream_name)
                file_path1 = streamProvider1.get_file_path('h265_4K', 'ts', stream_name)
                if file_path:
                    file_path = file_path[0]
                    file_path_list.append(file_path)
                if file_path1:
                    file_path1 = file_path1[0]
                    file_path_list.append(file_path1)
            print("file_path_list", file_path_list)
            for i in range(0, len(file_path_list) - 1):
                try:
                    streamProvider.start_send('udp', file_path_list[i])
                    streamProvider1.start_send('udp1', file_path_list[i + 1])
                except Exception as e:
                    logging.error("stream provider start send failed.")
                    raise False
                print(file_path_list[i], file_path_list[i + 1])
                if url and url1:
                    start_cmd = multi.get_start_cmd([url, url1])
                else:
                    start_cmd = multi.start_play_cmd(1, 'udp', 'udp1')
                multi.send_cmd(start_cmd)
                assert common_case.player_check.check_startPlay()[0], "start play failed"
                common_case.switch_pip_2_window()
                common_case.pause_resume_seek_stop()
                multi.stop_multiPlayer_apk()


