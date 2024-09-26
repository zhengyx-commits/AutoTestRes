#!/usr/bin/env python
# -*- coding: utf-8 -*-/
# @Time    : 2022/4/22
# @Author  : jianhua.huang
import itertools
import logging
from tools.StreamProvider import StreamProvider
from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

streamProvider = StreamProvider()
streamProvider1 = StreamProvider()

common_case = Common_Playcontrol_Case(playerNum=4)


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    if pytest.target.get("prj") == "ott_hybrid_compatibility":
        multi.add_so()
        multi.root()
        multi.run_shell_cmd("setenforce 0")
        multi.run_shell_cmd("getenforce")
        multi.run_shell_cmd("nohup sh /data/dump_decoder.sh /data/output.txt > /dev/null 2>&1 &")
        multi.multi_setup()
        multi.run_shell_cmd("echo 0 > /proc/sys/kernel/printk")
        multi.run_shell_cmd("setprop vendor.amtsplayer.debuglevel 1")
        multi.run_shell_cmd("setprop vendor.media.mediahal.mediasync.debug_level 2")
        multi.run_shell_cmd("setprop vendor.media.audio.hal.debug 1")
        multi.run_shell_cmd("setprop vendor.media.audiohal.aut 1")
    else:
        multi.multi_setup()
    yield
    if pytest.target.get("prj") == "ott_hybrid_compatibility":
        multi.run_shell_cmd("echo 1 > /proc/sys/kernel/printk")
        multi.run_shell_cmd("setprop vendor.amtsplayer.debuglevel 0")
        multi.run_shell_cmd("setprop vendor.media.mediahal.mediasync.debug_level 0")
        multi.run_shell_cmd("setprop vendor.media.audio.hal.debug 0")
        multi.run_shell_cmd("setprop vendor.media.audiohal.aut 0")
        os.system(f"adb -s {multi.serialnumber} pull /data/output.txt {multi.logdir}")
        multi.run_shell_cmd("pkill -f \"sh /data/dump_decoder.sh /data/output.txt\"")
        multi.run_shell_cmd("rm -rf /data/output.txt")
    else:
        pass
    multi.stop_multiPlayer_apk()
    streamProvider.stop_send()
#    streamProvider1.stop_send()


# @pytest.mark.skip
def test_Four_Screen_Switch_Window_UDP_TS_1080P():
    h264_1080I_stream_names, h264_1080I_url = get_conf_url("conf_udp_url", "udp", "conf_stream_name", "h264_1080I")
    if p_conf_single_stream:
        h264_1080P_stream_names, h264_1080P_url = get_conf_url("conf_udp_url", "udp", "conf_stream_name", "h264_1080P")
        for h264_1080I_stream_name, h264_1080P_stream_name in zip(h264_1080I_stream_names, h264_1080P_stream_names):
            file_path = streamProvider.get_file_path('h264_1080I', 'ts', h264_1080I_stream_name)
            file_path1 = streamProvider1.get_file_path('h264_1080P', 'ts', h264_1080P_stream_name)
            if not (file_path and file_path1):
                assert False, "stream not found"
            else:
                file_path = file_path[0]
                file_path1 = file_path1[0]
                try:
                    streamProvider.start_send('udp', file_path, url=h264_1080I_url[6:])
                    streamProvider1.start_send('udp', file_path1, url=h264_1080P_url[6:])
                except Exception as e:
                    logging.error("stream provider start send failed.")
                    raise False
            if h264_1080I_url and h264_1080P_url:
                start_cmd = multi.get_start_cmd([h264_1080I_url, h264_1080P_url, h264_1080I_url, h264_1080P_url])
            else:
                start_cmd = multi.start_play_cmd(1, 'udp', 'udp1', 'udp', 'udp1')
            multi.send_cmd(start_cmd)
            assert common_case.player_check.check_startPlay()[0], "start play failed"
            common_case.switch_pip_4_window()
            # common_case.pause_resume_seek_stop()
            multi.stop_multiPlayer_apk()
    else:
        file_path_list = []
        h264_1080P_stream_names, h264_1080P_url = get_conf_url("conf_udp_url", "udp", "conf_stream_name", "h264_1080P")
        if len(h264_1080I_stream_names) != 0:
            h264_1080I_stream_names = list(set(h264_1080I_stream_names))
            for stream_name in h264_1080I_stream_names:
                file_path = streamProvider.get_file_path('h264_1080I', 'ts', stream_name)
                if file_path:
                    file_path = file_path[0]
                    file_path_list.append(file_path)
                file_path1 = streamProvider.get_file_path('h264_1080P_25FPS', 'ts', stream_name)
                if file_path1:
                    file_path1 = file_path1[0]
                    file_path_list.append(file_path1)

            for i in range(0, len(file_path_list) - 1):
                try:
                    streamProvider.start_send('udp', file_path_list[i], url=h264_1080I_url[6:])
                    streamProvider1.start_send('udp', file_path_list[i + 1], url=h264_1080P_url[6:])
                except Exception as e:
                    logging.error("stream provider start send failed.")
                    raise False
                if h264_1080I_url and h264_1080P_url:
                    start_cmd = multi.get_start_cmd(
                        [h264_1080I_url, h264_1080P_url, h264_1080I_url, h264_1080P_url])
                    # print(start_cmd)
                    multi.send_cmd(start_cmd)
                    assert common_case.player_check.check_startPlay()[0], "start play failed"
                    common_case.switch_pip_4_window()
                    # common_case.pause_resume_seek_stop()
                    multi.stop_multiPlayer_apk()
                    streamProvider.stop_send()
                    streamProvider1.stop_send()

