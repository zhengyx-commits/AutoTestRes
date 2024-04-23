import pytest
import time
import re
import os
import logging
import allure
from tests.OTT.lib.System import Upgrade, Platform
from lib import get_device
import tarfile

work_space = os.path.abspath(os.path.join(os.getcwd(), "../.."))
upgrade_inf = Upgrade()
output = upgrade_inf.getprop("ro.boot.slot_suffix")
devices = get_device()

download_path = work_space + "/temp_image"
image_path = work_space + "/image"
bin_path = work_space + "/bin/setDutInUpdateMode"
update_path = work_space + "/bin/update/adnl_burn_pkg"
if not os.path.exists(download_path):
    os.makedirs(download_path)
else:
    os.system(f"rm -rf {download_path}/*")

if not os.path.exists(image_path):
    os.makedirs(image_path)
else:
    os.system(f"rm -rf {image_path}/*")

skip_navigation = 'pm disable com.google.android.tungsten.setupwraith;settings put secure user_setup_complete 1;settings put secure tv_user_setup_complete 1;settings put global device_provisioned 1'


def download_file(url):
    # 下载文件
    down_status = os.system(f"wget -q -c {url} -O {download_path}/aml_upgrade_img-20240415-5785.tar.bz2")
    if down_status != 0:
        raise Exception("download failed")

    # 解压文件
    with tarfile.open(f"{download_path}/aml_upgrade_img-20240415-5785.tar.bz2", "r:bz2") as tar:
        tar.extractall(download_path)

    logging.info("Download and extraction successful")


def update(url):
    enter_uboot = f"{bin_path} /dev/ott_hybrid_u_kpi_common_connector 921600 /dev/ott_hybrid_u_kpi_common_powerRelay 1 {work_space} adnl"
    os.system(enter_uboot)
    start_burn = f"{update_path} -p {url}"
    os.system(start_burn)


@allure.step("Start downgrade: from U to S")
def test_013_adnlDowngrade(device):
    # To download file
    firmware_url = "http://10.18.7.30/res/android_s/aml_upgrade_img-20240415-5785.tar.bz2"
    download_file(firmware_url)
    update(f"{download_path}/aml_upgrade_img-20240415-5785/aml_upgrade_package.img")
    upgrade_inf.root()
    assert upgrade_inf.build_version == "31"


@allure.step("Start downgrade: from S to U")
def test_013_adnlUpgrade(device):
    # To download file
    update(f"{image_path}/aml_upgrade_package.img")
    upgrade_inf.root()
    assert upgrade_inf.build_version == "34"
