#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/8/1 上午10:53
# @Author  : yongbo.shao
# @File    : test_Sanity_Func_http_start_kpi.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
import logging
import random
import time
import pytest

from tools.KpiAnalyze import KpiAnalyze
from tests.OTT_Hybrid.KPI import *

config_yaml = get_config()
p_conf_hls_4k = config_yaml.get_note("kpi_config").get("vod_s_t_seek").get("hls_4k")

for g_conf_device_id in devices:
    kpianalyze = KpiAnalyze(for_framework=True, adb=g_conf_device_id, config="/config/config.yaml",
                                kpi_name="vod_s_t_seek",
                                targetfile=None, kpifileobj=f"hls_4k_seek_{g_conf_device_id}.txt", kpifileobj_xlsx=f"hls_4k_seek_{g_conf_device_id}.xlsx")
    repeat_count = kpianalyze.repeat_count
# vod hls, http, vod rtsp


@pytest.fixture(scope='module', autouse=True)
def multi_teardown():
    setprop()
    #set_url("/storage/7F5D-3C01/video/video_pid_change_201_to_202.ts")
    set_url(f"http://{DEVICE_IP}/res/video/hlsV3_TS_H265_4K/4K-HLS-V3-H265-EAC3-TS/index.m3u8")
    # set_url("http://10.58.180.124/files/hlsV3_TS_H264_4K/4K-HLS-V3-H265-EAC3-TS/index.m3u8")
    push_xml()
    adb.run_shell_cmd(f"monkey -p {MULTIMEDIAPLAYER_TEST_APP_NAME} 1")
    # permission.permission_check()
    adb.keyevent(23)
    time.sleep(3)
    # adb.run_shell_cmd("adb logcat -b all -c")
    yield
    stop_multi_apk()


@pytest.mark.repeat(repeat_count)
def test_seek():
    seek_position = [0, 10000, 20000, 50000, 100000, 150000, 30000, 120000, 40000, 90000]
    # seek_position = [50000]
    seek_cmd = f'am broadcast -a multimediaplayer.test --ei instance_id 0 --es command seek_offset --el seek_pos {random.choice(seek_position)}'
    logging.info(f"seek_cmd: {seek_cmd}")
    adb.run_shell_cmd(seek_cmd)
    time.sleep(10)


def test_kpi_result():
    kpianalyze.kpi_analysis()
    kpianalyze.kpi_calculate()
    kpianalyze.save_to_excel()
    kpianalyze.save_to_db(name='vod_s_t_seek_kpi', flag='hls_4k')
    save_result(kpianalyze.kpifileobj_xlsx)
    kpianalyze.filter_abnormal_value(p_conf_hls_4k)
