#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/28 下午2:10
# @Author  : yongbo.shao
# @File    : __init__.py.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
import time

from tests.OTT_Sanity_Ref import *
from tools.OBS import OBS

obs = OBS(ip=p_conf_obs_websocket_ip, port=4455, scene_name='gtv')


def wait_boot_complete():
    start = time.time()
    ref_bluetooth_remote_pair_image = resmanager.get_target("image/bluetooth_remote_pair.png", source_path="image/bluetooth_remote_pair.png")
    while time.time() - start < 120:
        obs.capture_screen(sleep_time=10)
        file = obs.get_latest_file(obs.screenshot_dir)
        # print(file)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        process = subprocess.run(["tools/VideoStateDetector", "--method", "1", "--image_path", f"{file}", "--background_image_path", ref_bluetooth_remote_pair_image, "--saved_path", f'{obs.screenshot_dir}{timestamp}bluetooth_remote.png'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        logging.info(f"process: {process}")
        output = eval(process.stdout.decode())
        if output['Matched'] == True:
            break
