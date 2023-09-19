#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/5 上午10:53
# @Author  : yongbo.shao
# @File    : test_Sanity_Func_http_h264_4KP30_start_kpi.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
import os
import logging
import time
import pytest

from tools.KpiAnalyze import KpiAnalyze
from tests.OTT_Hybrid.KPI import *

config_yaml = get_config()
p_conf_rtsp_4kP30_h264 = config_yaml.get_note("kpi_config").get("vod_s_t_kpi").get("rtsp_4kP30_h264")

for g_conf_device_id in devices:
    kpianalyze = KpiAnalyze(for_framework=True, adb=g_conf_device_id, config="/config/config.yaml", kpi_name="rtsp_s_4kP30_h264_speed_to_start",
                            targetfile=None, kpifileobj=f"rtsp_s_4kP30_h264_speed_to_start_{g_conf_device_id}.txt", kpifileobj_xlsx=f"rtsp_s_4kP30_h264_speed_to_start_{g_conf_device_id}.xlsx")
    repeat_count = kpianalyze.repeat_count

@pytest.fixture(scope='module', autouse=True)
def multi_teardown():
    setprop()
    url = prepare("conf_rtsp_url", "rtsp_TS_H264_4K", "conf_stream_name", "h264_4K")
    print(url)
    push_xml()
    adb.run_shell_cmd(
        f'am start -n {MULTIMEDIAPLAYER_TEST_APP_NAME}/.multiplay.MultiPlayActivity --esal url_list "{url}" --ez is_loopplay true --ez is_amumediaplayer true --ez is_ts_mode true --ez IS_prefer_tunerhal false')

    time.sleep(1)
    adb.run_shell_cmd("logcat -b all -c")
    # permission.permission_check()
    yield
    stop_multi_apk()
    stop_send()


@pytest.mark.repeat(repeat_count)
def test_speed_to_start():
    adb.run_shell_cmd("am broadcast -a multimediaplayer.test --ei instance_id 0 --es command setspeed --ef speed 2.0")
    time.sleep(10)
    adb.run_shell_cmd("am broadcast -a multimediaplayer.test --ei instance_id 0 --es command setspeed --ef speed 1.0")
    time.sleep(10)


def test_kpi_result():
    kpianalyze.kpi_analysis()
    kpianalyze.kpi_calculate()
    kpianalyze.save_to_excel()
    kpianalyze.save_to_db(name='rtsp_s_4kP30_h264_speed_to_start', flag='rtsp_4kP30_h264_speed_to_start')
    save_result(kpianalyze.kpifileobj_xlsx)
    kpianalyze.filter_abnormal_value(p_conf_rtsp_4kP30_h264)
