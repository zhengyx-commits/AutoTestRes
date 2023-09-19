import pytest
import logging
import os
import time
from tests.OTT.lib.System import Sys, Upgrade, Platform
from tests.OTT_Sanity_Ref import config_yaml
from lib import get_device
from pathlib import Path

devices = get_device()
logdir = pytest.result_dir

config_system_cfg = config_yaml.get_note('conf_system')
p_conf_system_url = config_system_cfg['fastboot_url']
p_conf_system_password = config_system_cfg['password']
upgrade = Upgrade()
work_space = os.path.abspath(os.path.join(os.getcwd(), "../.."))
download_path = work_space + "/temp_image"
image_path = work_space + "/image"

if not os.path.exists(download_path):
    os.makedirs(download_path)
else:
    os.system(f"rm -rf {download_path}/*")

if not os.path.exists(image_path):
    os.makedirs(image_path)
else:
    os.system(f"rm -rf {image_path}/*")


def test_Flash():
    platform_inf = Platform()

    # download file
    logging.info(f' --- start to download and extract file: {p_conf_system_url}')
    logging.info(" --- Extract tgz file: fastboot_package.tgz ...")
    down_status = os.system(f"wget -q -c {p_conf_system_url} -O {download_path}/fastboot_package.zip")
    if down_status == 0:
        logging.info("download successful")
    else:
        raise Exception("download failed")

    # unzip file
    logging.info(" ---  unzip zip file: fastboot_package.zip...")
    tar_status = os.system(f"unzip {download_path}/fastboot_package.zip -d {image_path}")
    if tar_status == 0:
        logging.info("unzip successful")
    else:
        raise Exception("unzip failed")

    # To run upgrade
    for g_conf_device_id in devices:
        platform_inf.run_fastbootImg(image_path, p_conf_system_password, g_conf_device_id)
    logging.info(' --- flash_image done')
    time.sleep(90)

    # Wait DUT
    upgrade.wait_devices()
    upgrade.root()

    # DUT remount
    logging.info('start to remount')
    for g_conf_device_id in devices:
        os.system(f'cd ../shell; ./adb_remount.sh {g_conf_device_id}')





    # download_f, file_name = platform_inf.get_downloadFolder(p_conf_system_url)
    # logging.info(f' --- download_f: {download_f}')
    #
    # # platform_inf.extract_localFile(file_name, download_f)
    # os.system(f'unzip -o {download_f} -d ./target/{file_name}')
    # # To run upgrade
    # platform_inf.run_fastbootImg(file_name, p_conf_system_password, g_conf_device_id)
    # logging.info(' --- flash_image done')
    # time.sleep(90)
    # # To delete local file
    # os.system(f'pwd;rm -rf {download_f}')
    # os.system(f'rm -rf ./image/{download_f};rm -rf ./target/{download_f}')
    # logging.info(' --- teardown clear env done')
    # upgrade.wait_devices()
    # upgrade.root()
    # # DUT remount
    # logging.info('start to remount')
    # os.system(f'cd ../shell; ./adb_remount.sh {g_conf_device_id}')
