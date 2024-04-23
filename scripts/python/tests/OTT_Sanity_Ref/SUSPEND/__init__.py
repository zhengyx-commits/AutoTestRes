#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/03/25 上午10:32
# @Author  : yongbo.shao
# @File    : __init__.py.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
import time

from tests.OTT_Sanity_Ref import *
from tools.OBS import OBS

obs = OBS(ip=p_conf_obs_websocket_ip, port=4455, scene_name='gtv')


def check_suspend(suspend=None):
    ref_black_screen_image = resmanager.get_target("image/black_screen.png", source_path="image/black_screen.png")
    checked = True
    start = time.time()
    while time.time() - start < 60:
        file = obs.get_latest_file(obs.record_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if suspend:
            process = subprocess.run(["tools/VideoStateDetector", "--method", "2", "--video_path", f"{file}", "--background_image_path", ref_black_screen_image, "--saved_path", f'{obs.screenshot_dir}{timestamp}_black.png', '--match_number', '1', '--cooldown_time', '0'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            logging.info(f"process: {process}")
            if process.returncode == 0:
                output = eval(process.stdout.decode())
                # logging.info(f"output: {output}")
                if output['Matched time'] is not None:
                    logging.info(f"output: {output}")
                    break
    return checked


def get_launcher(timeout=10):
    launcher = False
    start = time.time()
    ref_image = resmanager.get_target("image/home.png", source_path="image/home.png")
    while time.time() - start < 120:
        obs.capture_screen(sleep_time=timeout)
        file = obs.get_latest_file(obs.screenshot_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        process = subprocess.run(["tools/VideoStateDetector", "--method", "1", "--image_path", f"{file}", "--background_image_path", ref_image, "--saved_path", f'{obs.screenshot_dir}{timestamp}_home.png'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        logging.info(f"process: {process}")
        if process.returncode == 0:
            output = eval(process.stdout.decode())
            if output and output['Matched']:
                launcher = True
                break
    if "home.HomeActivity" in adb.run_shell_cmd(CURRENT_FOCUS)[1]:
        launcher = True
    return launcher