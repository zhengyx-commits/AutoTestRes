#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/4 上午11:17
# @Author  : yongbo.shao
# @File    : test_DVB_Sanity_Func_46_Decoder_4K_Playback.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
import time

import pytest

from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.checkpoint.PlayerCheck import PlayerCheck
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck

dvb_stream = DVBStreamProvider()
player_check = PlayerCheck()
dvb = DVB()
dvb_check = DvbCheck()

video_name = "4KH265_16"


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_stream(video_name)
    dvb.start_livetv_apk()
    time.sleep(5)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.flaky(reruns=3)
def test_decoder_4k_playback():
    # test playback 4K channel
    dvb_check.check_play_status_main_thread()



