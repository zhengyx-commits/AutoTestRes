#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/2/17 下午3:35
# @Author  : yongbo.shao
# @File    : test_demux.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
import pytest
# from lib.common.tools.Demux import DemuxCheck
from lib.common.playback.LocalPlayer import LocalPlayer
from tests.OTT_Hybrid import config_yaml
import logging


p_conf_localplay_config = config_yaml.get_note('conf_localplay')
p_conf_uuid = p_conf_localplay_config.get('uuid')
p_conf_path = p_conf_localplay_config.get('path')


def test_demux():
    """
    1. setprop, catch logcat
    2. apk: setup, start play
    3. prepare ffprobe video and audio pts/dts info
    4. complete: play next stream
    6. analysis
    Returns:
    """
    logging.info('start test demux')
    videoplayer = LocalPlayer(p_conf_uuid, path=p_conf_path, play_from_list=True)
    if pytest.target.get("prj") == "iptv_product_line_p_yuv":
        videoplayer.install_apk('apk/VideoPlayerP.apk')
    else:
        videoplayer.install_apk('apk/VideoPlayer.apk')
    # videoplayer = LocalPlayer("6614-140D", path="/H264/", play_from_list=True)
    videoplayer.set_up(yuv_able=False, demux_able=True, video_player_monitor_enable=True)
    videoplayer.install_apk("apk/VideoPlayer.apk")
    assert videoplayer.startPlay()
    # close yuv
    if videoplayer.yuv_enable:
        videoplayer.video_player_monitor.yuv.close_yuv()

