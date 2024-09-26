#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/6/21
# @Author  : yongbo.shao

from tools.StreamProvider import StreamProvider
from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

player_check = PlayerCheck_Iptv()
streamProvider = StreamProvider()


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()
    streamProvider.stop_send()


# @pytest.mark.flaky(reruns=3)
def test_Multi_dynamic_pmt():
    stream_name_list, url = get_conf_url("conf_udp_url", "udp", "conf_stream_name", "pid_changed")
    for key_value in stream_name_list:
        file_path = streamProvider.get_file_path("pid_changed", 'ts', key_value)
        print(f"file_path: {file_path}")
        if not file_path:
            pass
        else:
            file_path = file_path[0]
            try:
                streamProvider.start_send('udp', file_path, url=url[6:], iswait=True)
            except Exception as e:
                logging.error("stream provider start send failed.")
                raise False
            if url:
                start_cmd = multi.get_start_cmd(url)
            else:
                start_cmd = multi.start_play_cmd(1, 'udp')
            multi.send_cmd(start_cmd)
            assert player_check.check_startPlay(timeout=60, scan_type="Interlaced")[0]
            multi.stop_multiPlayer_apk()
            streamProvider.stop_send()
