#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/1
# @Author  : yongbo.shao


import logging
import time
from tools.StreamProvider import StreamProvider
from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

player_check = PlayerCheck()
g_config_device_id = pytest.config['device_id']
multi = MultiPlayer(g_config_device_id)
streamProvider = StreamProvider()
resManager = ResManager()
apk_path = "apk/testSuspend2.apk"
p_conf_suspend = config_yaml.get_note("conf_suspend_time")
p_conf_suspend_time = p_conf_suspend.get("suspend_time")
p_conf_play_time_after_wakeup = p_conf_suspend.get("play_time_after_wakeup")


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    resManager.download_target(apk_path)
    multi.install_apk(apk_path)
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()
    streamProvider.stop_send()


# @pytest.mark.flaky(reruns=3)
# @pytest.mark.skip
def test_Multi_Suspend():
    stream_name_list, url = get_conf_url("conf_rtp_url", "rtp", "conf_stream_name", "mpeg2_1080I_30FPS")
    for stream_name in stream_name_list:
        file_path = streamProvider.get_file_path('mpeg2_1080I_30FPS', 'ts', stream_name)
        if file_path:
            file_path = file_path[0]
            try:
                streamProvider.start_send('rtp', file_path)
            except Exception as e:
                logging.error("stream provider start send failed.")
                raise False
            if url:
                start_cmd = multi.get_start_cmd(url)
            else:
                start_cmd = multi.start_play_cmd(1, 'rtp')
            multi.send_cmd(start_cmd)
            assert player_check.check_startPlay()[0]
            # suspend
            logging.info("start suspend")
            multi.send_cmd("am broadcast -n com.droidlogic.suspend/.SuspendReceiver -a suspend.test --es command suspend")
            time.sleep(p_conf_suspend_time)
            # wakeup
            logging.info("start wakeup")
            multi.send_cmd("am broadcast -n com.droidlogic.suspend/.SuspendReceiver -a suspend.test --es command wakeup")
            assert player_check.check_play_after_restore(p_conf_play_time_after_wakeup, flag=False)
            multi.stop_multiPlayer_apk()
