#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/5 上午10:53
# @Author  : yongbo.shao
# @File    : test_Sanity_Func_http_start_kpi.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
import os
import logging
import time
import pytest

from tools.KpiAnalyze import KpiAnalyze
from tests.OTT_Hybrid.KPI import *

config_yaml = get_config()
p_conf_rtp_h264_1080p = config_yaml.get_note("kpi_config").get("live_s_t_switch_exit").get("rtp_1080p")

for g_conf_device_id in devices:
    kpianalyze = KpiAnalyze(for_framework=True, adb=g_conf_device_id, config="/config/config.yaml",
                            kpi_name="live_s_t_switch_exit",
                            targetfile=None, kpifileobj=f"rtp_h264_1080p_switch_exit_{g_conf_device_id}.txt",
                            kpifileobj_xlsx=f"rtp_h264_1080p_switch_exit_{g_conf_device_id}.xlsx")
    repeat_count = kpianalyze.repeat_count


@pytest.fixture(scope='module', autouse=True)
def multi_teardown():
    # get_filepath("UD2D-Paris_30fps")
    setprop()
    url = prepare("conf_rtp_url", "rtp", "conf_stream_name", "h265_1080P_3")
    url1 = prepare("conf_rtp_url", "rtp", "conf_stream_name", "Andy_Lau")
    push_xml()
    # set_url("udp://239.1.2.1:1234")
    # set_url("http://10.18.7.30/res/video/H264_1080P_PhilipsColorsofMiami_25M_25fps_5.5min.ts")
    adb.run_shell_cmd(f'am start -n {MULTIMEDIAPLAYER_TEST_APP_NAME}/.multiplay.MultiPlayActivity --esal url_list "{url};{url1}" --ez is_loopplay true --ez is_amumediaplayer true --ez is_ts_mode true --ez IS_prefer_tunerhal false')
    # permission.permission_check()
    # adb.keyevent(23)
    time.sleep(3)
    adb.run_shell_cmd("dmesg -c")
    adb.run_shell_cmd("adb logcat -b all -c")
    time.sleep(3)
    yield
    stop_multi_apk()
    stop_send()


@pytest.mark.repeat(repeat_count)
def test_switch_channel():
    time.sleep(3)
    # adb.keyevent(20)
    adb.keyevent("KEYCODE_CHANNEL_DOWN")
    time.sleep(15)


def test_kpi_result():
    kpianalyze.kpi_analysis()
    kpianalyze.kpi_calculate()
    kpianalyze.save_to_excel()
    kpianalyze.save_to_db(name='live_s_t_switch_channel_kpi', flag='rtp_h264_1080p')
    save_result(kpianalyze.kpifileobj_xlsx)
    kpianalyze.filter_abnormal_value(p_conf_rtp_h264_1080p)
