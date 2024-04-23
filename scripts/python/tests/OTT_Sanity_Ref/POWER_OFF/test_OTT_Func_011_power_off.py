#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/21 上午10:48
# @Author  : yongbo.shao
# @File    : test_power_off.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
import time

import allure
from tests.OTT_Sanity_Ref.POWER_OFF import *


p_conf_config_poweroff_time = config_yaml.get_note("kpi_config").get("poweroff_time")
g_conf_device_id = pytest.config['device_id']
poweroff_time_list = []
reference_values = {"poweroff_time": p_conf_config_poweroff_time}
poweroff_time_list_name = 'poweroff_time_list.xlsx'


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    yield
    obs.stop_recording()
    adb.home()


@allure.step("Start long press power")
def test_011_power_off():
    logging.info("start power off")
    obs.start_recording()
    adb.run_shell_cmd("sendevent /dev/input/event2 1 116 1")
    adb.run_shell_cmd("sendevent /dev/input/event2 0 0 0")
    time.sleep(3)
    obs.capture_screen()
    assert get_power_off_logo(confirm=True)
    adb.enter()
    time.sleep(2)
    obs.stop_recording()
    assert get_power_off_logo(black=True)
    powerRelay_bin_path = get_powerRelay_path()
    logging.info(f"Power OFF")
    subprocess.run([f"{powerRelay_bin_path}powerRelay", p_conf_power_symlink, "1", "off"])
    time.sleep(2)
    logging.info(f"Power ON")
    subprocess.run([f"{powerRelay_bin_path}powerRelay", p_conf_power_symlink, "1", "on"])
    time.sleep(60)
    assert get_launcher()


def get_power_off_logo(confirm=None, black=None):
    ref_poweroff_confirm_image = resmanager.get_target("image/poweroff_confirm.png", source_path="image/poweroff_confirm.png")
    ref_black_screen_image = resmanager.get_target("image/black_screen.png", source_path="image/black_screen.png")
    # file = obs.get_latest_file(obs.record_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if confirm:
        file = obs.get_latest_file(obs.screenshot_dir)
        process = subprocess.run(["tools/VideoStateDetector", "--method", "1", "--image_path", f"{file}", "--background_image_path", ref_poweroff_confirm_image, "--saved_path", f'{obs.screenshot_dir}{timestamp}_poweroff_confirm.png'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        logging.info(f"process: {process}")
        output = eval(process.stdout.decode())
        if output['Matched']:
            return True
    if black:
        file = obs.get_latest_file(obs.record_dir)
        process = subprocess.run(["tools/VideoStateDetector", "--method", "2", "--video_path", f"{file}", "--background_image_path", ref_black_screen_image, "--saved_path", f'{obs.screenshot_dir}{timestamp}_black.png', '--match_number', '2', '--cooldown_time', '0'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        logging.info(f"process: {process}")
        output = eval(process.stdout.decode())
        poweroff_time = output['Matched time']
        logging.info(f"poweroff_time: {poweroff_time}")
        if poweroff_time:
            return True


