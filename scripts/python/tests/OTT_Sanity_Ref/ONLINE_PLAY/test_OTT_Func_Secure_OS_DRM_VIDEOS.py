#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2023/3/10 下午14:00
# @Author  : jun.yang
# @Site    :
# @File    : test_OTT-Sanity_Secure_OS_DRM_VIDEOS.py
# @Software: PyCharm

import pytest
from lib.common.playback.DRM import DRM
import time
import logging
from lib.OTT.S905X4.Exoplayer_json_read import read_json
from tests.OTT_Sanity_Ref import *

drm = DRM()
res = read_json()
p_video_info = config_ott_sanity_yaml.get_note('conf_secure_os')
p_video_name = p_video_info['name']

logging.info(f'p_video_name : {p_video_name}')


class Test_057_Secure_OS:

    # @pytest.mark.skip
    @pytest.mark.flaky(reruns=3)
    def test_playback(self):
        # back
        # drm.back()
        drm.set_ott_flag()
        drm.playback()
        # drm.permission.permission_check()
        time.sleep(5)
        start_time = time.time()
        while time.time() - start_time < 60:
            current_window = drm.run_shell_cmd('dumpsys window | grep -i mCurrentFocus')[1]
            if "com.google.android.permissioncontroller" in current_window:
                drm.find_and_tap("Allow", "text")  # get permission
                time.sleep(2)
            else:
                logging.info("permission OK")
                break

        # judge whether apk start is not
        start_time = time.time()
        current_window = drm.run_shell_cmd('dumpsys window | grep -i mCurrentFocus')[1]
        if 'com.droidlogic.exoplayer2.demo/com.droidlogic.combineplayer.ui.MainTabActivity' not in current_window:
            while time.time() - start_time < 60:
                drm.run_shell_cmd('input keyevent 3')
                time.sleep(5)
                drm.run_shell_cmd("monkey -p com.droidlogic.exoplayer2.demo 1")
                time.sleep(10)
                current_window = drm.run_shell_cmd('dumpsys window | grep -i mCurrentFocus')[1]
                if 'com.droidlogic.exoplayer2.demo/com.droidlogic.combineplayer.ui.MainTabActivity' not in current_window:
                    logging.debug("continue")
                else:
                    break
        else:
            logging.debug("APK OK")
        if 'com.droidlogic.exoplayer2.demo/com.droidlogic.combineplayer.ui.MainTabActivity' not in current_window:
            raise ValueError("apk hasn't exited yet")
        else:
            logging.debug("APK OK")

        drm.wait_and_tap('SETTINGS', 'text')
        drm.keyevent(23)
        time.sleep(2)
        drm.wait_and_tap("ExoPlayer", 'text')
        drm.keyevent(23)
        time.sleep(2)
        drm.u().d2(text="SAMPLE EXOPLAYER").click()
        time.sleep(2)
        for video_name, video_samples in res.items():
            drm.listed = False
            drm.skip_video = False
            if video_name not in p_video_name:
                continue
            for video_sample in video_samples:
                if drm.skip_video is True:
                    break
                drm.during_video = False
                video_sample_name = video_sample['name']
                video_sample_vdec = video_sample['vdec']
                if not drm.player(video_name, video_sample_name, video_sample_vdec):
                    logging.info(f'{video_name} : {video_sample_name}  play error !!!')
                    assert False

        # back to home
        drm.back()
        if drm.getprop("ro.build.version.sdk") == "34":
            drm.run_shell_cmd("setprop vendor.mediahal.loglevels 0")
