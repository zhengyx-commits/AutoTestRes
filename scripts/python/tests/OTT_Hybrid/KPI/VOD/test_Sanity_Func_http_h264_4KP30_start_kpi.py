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
from tests.OTT_Hybrid import *

config_yaml = get_config()
p_conf_http_h264_4kP30 = config_yaml.get_note("kpi_config").get("vod_s_t_kpi").get("http_4kP30_h264")


for g_conf_device_id in devices:
    kpianalyze = KpiAnalyze(for_framework=True, adb=g_conf_device_id, config="/config/config.yaml", kpi_name="vod_s_t_kpi",
                            targetfile=None, kpifileobj=f"h264_4kP30_start_{g_conf_device_id}.txt", kpifileobj_xlsx=f"h264_4kP30_start_{g_conf_device_id}.xlsx")
    repeat_count = kpianalyze.repeat_count


@pytest.fixture(scope='module', autouse=True)
def multi_teardown():
    setprop()
    set_url(f"http://{DEVICE_IP}/res/video/http_TS_H264_4K/H264_Butterfly_4k_High@L5.1_AAC_30M_30fps_3min.ts")
    # set_url("http://10.58.180.124/files/h264_1080P/H264_1080P_PhilipsColorsofMiami_25M_25fps_5.5min.ts")
    push_xml()
    adb.run_shell_cmd(f"monkey -p {MULTIMEDIAPLAYER_TEST_APP_NAME} 1")
    # permission.permission_check()
    yield
    stop_multi_apk()


@pytest.mark.repeat(repeat_count)
def test_startPlay():
    adb.keyevent(23)
    time.sleep(3)
    adb.keyevent(4)
    time.sleep(1)


def test_kpi_result():
    kpianalyze.kpi_analysis()
    kpianalyze.kpi_calculate()
    kpianalyze.save_to_excel()
    kpianalyze.save_to_db(name='vod_s_t_start_kpi', flag='http_h264_4kP30')
    save_result(kpianalyze.kpifileobj_xlsx)
    kpianalyze.filter_abnormal_value(p_conf_http_h264_4kP30)
