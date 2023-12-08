#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/4 上午11:17
# @Author  : yongbo.shao
# @File    : test_DVB_Sanity_Func_160_Standby_Reboot.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm

import pytest
import logging
import time

from tools.DVBStreamProvider import DVBStreamProvider

from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from . import install_suspend_apk
from .. import config_yaml
from lib.common.system.Reboot import Reboot
from lib import get_device

dvb_stream = DVBStreamProvider()

dvb = DVB()
dvb_check = DvbCheck()
p_conf_suspend = config_yaml.get_note("conf_suspend_time")
p_conf_suspend_time = p_conf_suspend.get("suspend_time")
p_conf_play_time_after_wakeup = p_conf_suspend.get("play_time_after_wakeup")
p_conf_standby = config_yaml.get_note("conf_standby")
p_conf_repeat_standby_time = p_conf_standby.get("repeat_time")
logdir = pytest.result_dir
for g_conf_device_id in get_device():
    adb_cmd = ["/usr/bin/adb", "-s", g_conf_device_id, "shell", "logcat -s ActivityManager"]
    reboot = Reboot(adb_cmd=adb_cmd, device_id=g_conf_device_id, logdir=logdir)

video_name = "gr1"


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    install_suspend_apk()
    # start send stream
    dvb_stream.start_dvbc_stream(video_name)
    dvb.start_livetv_apk_and_manual_scan()
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


@pytest.mark.skip
@pytest.mark.repeat(p_conf_repeat_standby_time)
def test_cas_repeat_reboot():
    channel_id_before = dvb.get_current_channel_info()[1]
    logging.info(f'channel_id : {channel_id_before}')
    # test playback
    dvb_check.check_play_status_main_thread()
    # reboot
    logging.info("start reboot")
    reboot.reboot_once()
    # send stream
    dvb_stream.start_dvbc_stream(video_name)
    dvb.start_livetv_apk_and_manual_scan()
    dvb.root()
    dvb.shell("setenforce 0")
    dvb.shell("setprop media.ammediaplayer.enable 1;setprop iptv.streamtype 1")
    channel_id_after = dvb.get_current_channel_info()[1]
    logging.info(f'channel_id : {channel_id_after}')
    assert channel_id_after == channel_id_before
    start_time = time.time()
    flag = False
    while time.time() - start_time < 5:
        if dvb_check.check_is_playing():
            flag = True
            break
    assert flag
    dvb_check.check_play_status_main_thread()





