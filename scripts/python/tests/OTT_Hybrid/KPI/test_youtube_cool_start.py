#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/6/12 上午10:48
# @Author  : yongbo.shao
# @File    : test_youtube_cool_start.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
import time
import pytest
import logging
from lib.common.system.SerialPort import SerialPort
from tools.KpiAnalyze import KpiAnalyze
from tests.OTT_Hybrid.KPI import *
from . import get_config

ser = SerialPort()

for g_conf_device_id in devices:
    kpianalyze = KpiAnalyze(for_framework=True, adb=g_conf_device_id, config="/config/config.yaml",
                                    kpi_name="youtube_cool_start",
                                    targetfile=None, kpifileobj=f"youtube_cool_start_{g_conf_device_id}.txt",
                                    kpifileobj_xlsx=f"youtube_cool_start_{g_conf_device_id}.xlsx")
    repeat_count = kpianalyze.repeat_count

logcat_file = "youtube_cool_start.log"
GOOGLE_YOUTUBE_PACKAGENAME = 'com.google.android.youtube.tv'
count = 0
config_yaml = get_config()


@pytest.fixture(scope='function', autouse=True)
def setup():
    ser.write(f"ifconfig eth0 down")
    ser.write(f"cmd wifi connect-network sunshine wpa2 Home1357")
    yield
    ser.write(f"cmd wifi set-wifi-enabled disabled")
    ser.write(f"ifconfig eth0 up")


@pytest.mark.repeat(repeat_count)
def test_youtube_cool_start():
    ser.write(f"am force-stop {GOOGLE_YOUTUBE_PACKAGENAME}")
    ser.enter_uboot()
    ser.enter_kernel()
    ser.write("su")
    ser.write("logcat -c")
    data = ser.write_pipe(
        "logcat |grep -i 'for service {com.google.android.apps.tv.launcherx/com.google.android.apps.tv.launcherx.coreservices.notificationlistener.TvNotificationListenerService}' ")
    if data:
        time.sleep(30)
        ser.write("\x03")
        ser.write("\x03")
        ser.write("\x03")
        start_youtube()
    # kpi_calculate()


def start_youtube():
    global count
    count += 1
    start_time = time.time()
    ser.write(f"monkey -p {GOOGLE_YOUTUBE_PACKAGENAME} 1")
    data = ser.write_pipe("logcat |grep -i 'ActivityTaskManager: Displayed com.google.android.youtube.tv/com.google.android.apps.youtube.tv.activity.MainActivity' ")
    if data:
        ser.write("\x03")
        ser.write("\x03")
        ser.write("\x03")
        end_time = time.time()
        launch_time = end_time - start_time
        kpianalyze.offset_list.append(launch_time)
        if launch_time > config_yaml.get_note('kpi_config').get("youtube_cool_start_launch_time"):
            logging.info(f"start youtube the {count} time")
            assert False
        else:
            assert True


def test_kpi_calculate():
    kpianalyze.save_to_excel()
    kpianalyze.save_to_db(name='youtube_cool_start', flag='1')
