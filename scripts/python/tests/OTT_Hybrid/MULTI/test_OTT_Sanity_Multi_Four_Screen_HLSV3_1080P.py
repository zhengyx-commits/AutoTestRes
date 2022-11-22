#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/4/22
# @Author  : jianhua.huang

from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *
import itertools

common_case = Common_Playcontrol_Case(playerNum=4)


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()



# @pytest.mark.skip
def test_Multi_FOUR_SCREEN_HLSV3_1080P():
    hlsV3_TS_H265_1080_urls = get_conf_url("conf_hls_url", "hlsV3_TS_H265_1080")
    hlsV3_TS_H265_4K_urls = get_conf_url("conf_hls_url", "hlsV3_TS_H265_4K")
    if len(hlsV3_TS_H265_1080_urls) != 0 and len(hlsV3_TS_H265_4K_urls) != 0:
        urls = list(itertools.product(hlsV3_TS_H265_1080_urls, hlsV3_TS_H265_4K_urls))
        # print(f"urls: {urls}")
        for url in urls:
            url = list(url)
            # print(f"url[0]:{url[0]}")
            # print(f"url[1]:{url[1]}")
            p_start_cmd = multi.get_start_cmd([url[0], url[1], url[0], url[1]])
            multi.send_cmd(p_start_cmd)
            assert common_case.player_check.check_startPlay()[0], "start play failed"
            common_case.switch_pip_4_window()
            #common_case.pause_resume_seek_stop()
            multi.stop_multiPlayer_apk()
    else:
        p_start_cmd = multi.start_play_cmd(1, 'hlsV3_TS_H265_1080', 'hlsV3_TS_H265_1080', 'hlsV3_TS_H265_1080', 'hlsV3_TS_H265_4K')
        multi.send_cmd(p_start_cmd)
        assert common_case.player_check.check_startPlay()[0], "start play failed"
        common_case.switch_pip_4_window()
        #common_case.pause_resume_seek_stop()
        multi.stop_multiPlayer_apk()


