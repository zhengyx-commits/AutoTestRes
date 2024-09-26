#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/2/15 下午4:25
# @Author  : yongbo.shao
# @File    : Demux.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm

# audio: ffprobe -select_streams a:0 -show_packets -of json ~/Videos/H264_1080P_PhilipsColorsofMiami_25M_25fps_5.5min.ts > packet_audio.json
# video: ffprobe -select_streams v:0 -show_packets -of json ~/Videos/H264_1080P_PhilipsColorsofMiami_25M_25fps_5.5min.ts > packet_video.json
# S: echo 1 > /sys/module/dvb_demux/parameters/debug_ts_output
# T: echo 1 > /sys/module/amlogic_dvb_demux/parameters/debug_ts_output
# load json
import logging
import os
import subprocess
import threading
import time

from lib.common.system.ADB import ADB
from lib import get_device
import json
import pytest
import re
import matplotlib.pyplot as plt
import numpy as np


class DemuxCheck(ADB):

    T_DEMUX_TS_OUTPUT = "setenforce 0;echo 1 > /sys/module/amlogic_dvb_demux/parameters/debug_ts_output"
    S_DEMUX_TS_OUTPUT = "setenforce 0;echo 1 > /sys/module/dvb_demux/parameters/debug_ts_output"

    def __init__(self):
        super().__init__()
        self.check_project()
        self.video_pts = []
        self.video_dts = []
        self.audio_pts = []
        self.audio_dts = []
        self.audio_info = []
        self.video_info = []
        self.name = self.logdir + "/" + "dmx_info.txt"
        # self.open_file()

    def open_file(self, video):
        # self.f = open(self.logdir + "/" + f"dmx_info_{video}.txt", "w", encoding="utf-8")
        self.f = open(self.name, "w", encoding="utf-8")

    def close_file(self):
        self.f.close()

    def check_project(self):
        if "ott_hybrid_t_yuv" in pytest.target.get("prj"):
            self.run_shell_cmd(self.T_DEMUX_TS_OUTPUT)
        elif "ott_hybrid_s_yuv" in pytest.target.get("prj"):
            self.run_shell_cmd(self.S_DEMUX_TS_OUTPUT)
        else:
            pass

    def ffprobe_dmx_video(self, file_path, target_json):
        os.system(f"ffprobe -select_streams v:0 -show_packets -of json {file_path} > {target_json}")
        return target_json

    def ffprobe_dmx_audio(self, fila_path, target_json):
        os.system(f"ffprobe -select_streams a:0 -show_packets -of json {fila_path} > {target_json}")
        return target_json

    def get_dmx_probe_info(self, target_json):
        pts_probe = []
        dts_probe = []
        size_probe = []
        with open(target_json, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        # print(video_json_data["packets"])
        for ele in json_data["packets"]:
            pts = ele["pts"]
            dts = ele["dts"]
            size = ele["size"]
            pts_probe.append(int(pts)/1000000)
            dts_probe.append(int(dts)/1000000)
            size_probe.append(int(size))
        # print(video_pts_probe)
        # print(video_dts_probe)
        # print(video_size_probe)
        return pts_probe, dts_probe, size_probe

    def analysis_dmx_video_info(self, video_pid, file_path, target_json):
        target_json = self.ffprobe_dmx_video(file_path, target_json)
        video_pts_probe, video_dts_probe, video_size_probe = self.get_dmx_probe_info(target_json)
        # with open(self.name, "r", encoding="utf-8", errors="ignore") as f:
        with open(self.name, "r", errors="ignore") as f:
        # with open(self.logdir + "/" + f"dmx_info_{video}.txt", "r", encoding="utf-8") as f:
            outputValues = f.readlines()
        for outputValue in outputValues:
            try:
                if ("ts_output: video pid" in outputValue) and (len(outputValue) <= 150):
                    # dmx video info
                    dmx_info = re.findall(r"ts_output: video pid:(.*) sid:.* flag:.*, pts:(.*), dts:(.*), offset:.*", outputValue)[0]
                    self.video_info.append(dmx_info)
                else:
                    pass
            except Exception as e:
                logging.warning(f"{e}")
        logging.debug(f"self.video_info: {self.video_info}")
        for ele in self.video_info:
            if ele[0] == video_pid and (ele[2] != "\x00x0"):
                self.video_pts.append(int(ele[1], 16) / 1000000)
                self.video_dts.append(int(ele[2], 16) / 1000000)
        logging.debug(f"self.video_pts: {self.video_pts}")
        logging.debug(f"video_pts_probe: {video_pts_probe}")
        return self.final_check(self.video_pts, video_pts_probe)

    def final_check(self, hw_demux_pts, ffprobe_pts):
        count = 0
        if (len(hw_demux_pts) != 0):
            for ele in hw_demux_pts:
                if ele not in ffprobe_pts:
                    count += 1
                    logging.info(f"pts {ele} is not in ffprobe packets")
            if count >= 1:
                return False
            else:
                return True
        else:
            logging.info("pls check if ts_output output or not in logcat")
            return False

    def analysis_dmx_audio_info(self, audio_pid, file_path, target_json):
        target_json = self.ffprobe_dmx_audio(file_path, target_json)
        audio_pts_probe, audio_dts_probe, audio_size_probe = self.get_dmx_probe_info(target_json)
        # with open(self.name, "r", encoding="utf-8", errors="ignore") as f:
        with open(self.name, "r", errors="ignore") as f:
            outputValues = f.readlines()
        for outputValue in outputValues:
            try:
                if ("ts_output: audio pid" in outputValue) and (len(outputValue) <= 150):
                    # dmx audio info
                    dmx_info = re.findall(r"ts_output: audio pid:(.*) sid:.* flag:.*, pts:(.*), dts:(.*), len:.*", outputValue)[0]
                    self.audio_info.append(dmx_info)
                else:
                    pass
            except Exception as e:
                logging.warning(f"{e}")
        logging.debug(f"self.audio_info: {self.audio_info}")
        for ele in self.audio_info:
            if ele[0] == audio_pid and (ele[2] != "\x00x0"):
                self.audio_pts.append(int(ele[1], 16) / 1000000)
                self.audio_dts.append(int(ele[2], 16) / 1000000)
        logging.debug(f"self.audio_pts: {self.audio_pts}")
        logging.debug(f"audio_pts_probe: {audio_pts_probe}")
        return self.final_check(self.audio_pts, audio_pts_probe)

    def plt_image(self, video_size_probe, video_pts, video_pts_probe):
        pass
        plt.style.use("fivethirtyeight")
        plt.figure(figsize=(10, 5), dpi=200)
        plt.plot(video_size_probe, video_pts, color='green', marker='o', linestyle='dashed', linewidth=2,
                 markersize=12)
        plt.plot(video_size_probe, video_pts_probe, color='green', marker='*', linestyle='solid', linewidth=2,
                 markersize=12)
        plt.grid(True)
        plt.show()

    def start_get_dmx_logcat_thread(self, video):
        t = threading.Thread(target=self.get_dmx_logcat_info, args=(video,))
        t.setDaemon(True)
        t.start()

    def get_dmx_logcat_info(self, video):
        self.reset()
        self.open_file(video)
        for serialnumber in get_device():
            log = subprocess.Popen(f"adb -s {serialnumber} shell logcat | grep -E 'ts_output' ", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True, encoding="utf-8")
            # log = subprocess.Popen(f"adb -s {self.serialnumber} shell logcat -b all", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True, encoding="utf-8")
            while True:
                if log:
                    outputValue = log.stdout.readline()
                    outputValue = outputValue.replace('\\r', '\r') \
                            .replace('\\n', '\n') \
                            .replace('\\t', '\t')
                    if not self.f.closed:
                        self.f.write(outputValue)

    def reset(self):
        self.audio_info.clear()
        self.video_info.clear()
        self.video_pts.clear()
        self.video_dts.clear()
        self.audio_pts.clear()
        self.audio_dts.clear()
        self.clear_logcat()
        time.sleep(1)
        self.clear_logcat()
        self.clear_logcat()


if __name__ == '__main__':
    demuxcheck = DemuxCheck()
    demuxcheck.get_dmx_probe_info("packet_video.json")



