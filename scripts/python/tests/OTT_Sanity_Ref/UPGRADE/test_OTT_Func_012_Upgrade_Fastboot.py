import pytest
import logging
import os
import time
from tests.OTT.lib.System import Sys, Upgrade, Platform
from tests.OTT_Sanity_Ref import *
from lib import get_device
import allure
from pathlib import Path

devices = get_device()
logdir = pytest.result_dir

upgrade = Upgrade()
work_space = os.path.abspath(os.path.join(os.getcwd(), "../../"))
download_path = work_space + "/temp_image"
image_path = work_space + "/image"
tmp_path = work_space + "/tmp"

if not os.path.exists(download_path):
    os.makedirs(download_path)
else:
    os.system(f"rm -rf {download_path}/*")

if not os.path.exists(image_path):
    os.makedirs(image_path)
else:
    os.system(f"rm -rf {image_path}/*")


@allure.step("Start downgrade: from U to S")
def test_012_Flash_downgrade():
    # download file
    s_system_url = 'http://10.18.7.30/res/android_s/ohm_hybrid-fastboot-flashall-16879.zip'
    download_file(s_system_url, tmp_path)
    assert upgrade.build_version == "31"


@allure.step("Start downgrade: from S to U")
def test_012_Flash_upgrade():
    with open(f'{tmp_path}/fastboot_url.txt', 'r') as f:
        content = f.read()
    print(content)

    download_file(content.strip(), tmp_path)
    assert upgrade.build_version == "34"


def download_file(content, file_path):
    platform_inf = Platform()
    # download file
    logging.info(f' --- start to download and extract file: {content}')
    logging.info(" --- Extract tgz file: fastboot_package.tgz ...")
    logging.info(f"wget -q -c {content} -O {download_path}/fastboot_package.zip")
    down_status = os.system(f"wget -q -c {content} -O {download_path}/fastboot_package.zip")
    if down_status == 0:
        logging.info("download successful")
    else:
        raise Exception("download failed")

    # unzip file
    logging.info(" ---  unzip zip file: fastboot_package.zip...")
    tar_status = os.system(f"unzip {download_path}/fastboot_package.zip -d {file_path}")
    if tar_status == 0:
        logging.info("unzip successful")
    else:
        raise Exception("unzip failed")

    # To run upgrade
    for g_conf_device_id in devices:
        platform_inf.run_fastbootImg(file_path, "Linux2017", g_conf_device_id)
    logging.info(' --- flash_image done')
    time.sleep(90)

    # Wait DUT
    upgrade.wait_devices()
    upgrade.root()

    # DUT remount
    logging.info('start to remount')
    for g_conf_device_id in devices:
        os.system(f'cd ../shell; ./adb_remount.sh {g_conf_device_id}')
