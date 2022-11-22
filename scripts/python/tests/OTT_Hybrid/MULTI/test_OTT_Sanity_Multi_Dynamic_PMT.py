#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/6/21
# @Author  : yongbo.shao


import logging
from tools.StreamProvider import StreamProvider
from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

player_check = PlayerCheck()
g_config_device_id = pytest.config['device_id']
multi = MultiPlayer(g_config_device_id)
streamProvider = StreamProvider()


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()
    streamProvider.stop_send()


@pytest.mark.flaky(reruns=3)
def test_Multi_dynamic_pmt():
    stream_name_list, url = get_conf_url("conf_udp_url", "udp", "conf_stream_name", "pid_changed")
    for stream_name in stream_name_list:
        file_path = streamProvider.get_file_path('pid_changed', 'ts', stream_name)
        print(f"file_path: {file_path}")
        if not file_path:
            assert False, "stream not found"
        else:
            file_path = file_path[0]
        # if not streamProvider.get_file_path('ts', stream_name):
        #     logging.error("stream provider file path doesn't exist.")
        #     return
        # else:
        #     file_path = streamProvider.get_file_path('ts', stream_name)[0]
            try:
                streamProvider.start_send('udp', file_path, iswait=True)
            except Exception as e:
                logging.error("stream provider start send failed.")
                raise False
            if url:
                start_cmd = multi.get_start_cmd(url)
            else:
                start_cmd = multi.start_play_cmd(1, 'udp')
            multi.send_cmd(start_cmd)
            assert player_check.check_startPlay(timeout=60)[0]
            multi.stop_multiPlayer_apk()
