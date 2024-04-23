import pytest
import time
import re
import os
import logging
import allure
from tests.OTT.lib.System import Upgrade, Platform
from lib import get_device

work_space = os.path.abspath(os.path.join(os.getcwd(), "../.."))
upgrade_inf = Upgrade()
output = upgrade_inf.getprop("ro.boot.slot_suffix")
devices = get_device()

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

skip_navigation = 'pm disable com.google.android.tungsten.setupwraith;settings put secure user_setup_complete 1;settings put secure tv_user_setup_complete 1;settings put global device_provisioned 1'


def check_UpdaterApk():
    check_apk = str(upgrade_inf.subprocess_run('ls -la /data/data/com.droidlogic.updater '))
    logging.debug(f'check_apk status : {check_apk}')
    if 'returncode=1' in check_apk:
        return True
    else:
        return False


def update(url):
    platform_inf = Platform()
    download_f, file_name = platform_inf.get_downloadFolder(url)
    logging.info(f' --- download_f.name: {download_f}')

    # To mount Udisk
    uuid = upgrade_inf.getUUID()
    basepath = "/storage/" + uuid
    logging.info(f' --- basepath: {basepath}')
    #
    upgrade_inf.push_UdiskZip(download_f, basepath)

    os.system('pwd;adb shell ' + skip_navigation)
    os.system('adb reboot;sleep 90;adb root')

    # To run upgrade
    upgrade_inf.start_updater()
    upgrade_inf.wait_and_tap('UPDATE LOCAL', "text")
    upgrade_inf.enter()
    time.sleep(5)
    upgrade_inf.uiautomator_dump(upgrade_inf.logdir)
    dumpInfo = upgrade_inf.get_dump_info()
    ota_zip = re.findall(download_f, dumpInfo, re.S)[0]
    ota_zip = upgrade_inf.get_zip(uuid, download_f)

    if ota_zip in dumpInfo:
        logging.info('can update')
        upgrade_inf.find_and_tap(ota_zip, "text")
        time.sleep(5)
        upstep = upgrade_inf.upgrade_step()
        # print(' --- upstep: ', upstep)
        assert True if upstep else False
    else:
        logging.info('can not update')
        assert False

    # To delete local file
    os.system(f'pwd;rm -rf {download_f}')
    logging.info(' --- teardown clear env done')
    upgrade_inf.stop_updater()


def download_file(content):
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
    tar_status = os.system(f"unzip {download_path}/fastboot_package.zip -d {image_path}")
    if tar_status == 0:
        logging.info("unzip successful")
    else:
        raise Exception("unzip failed")

    # To run upgrade
    for g_conf_device_id in devices:
        platform_inf.run_fastbootImg(image_path, "Linux2017", g_conf_device_id)
    logging.info(' --- flash_image done')
    time.sleep(90)

    # Wait DUT
    upgrade_inf.wait_devices()
    upgrade_inf.root()

    # DUT remount
    logging.info('start to remount')
    for g_conf_device_id in devices:
        os.system(f'cd ../shell; ./adb_remount.sh {g_conf_device_id}')


@allure.step("Start downgrade: from U to S")
@pytest.mark.skip()
def test_014_otaDowngrade(device):
    # To download file
    firmware_url = "http://10.18.7.30/res/android_s/ohm_hybrid-ota-20240326-16879.zip"
    update(firmware_url)
    upgrade_inf.root()
    output_a = upgrade_inf.getprop("ro.boot.slot_suffix")
    assert output_a != output


@allure.step("Start downgrade: from U to S")
def test_Flash_downgrade():
    # download file
    s_system_url = 'http://10.18.7.30/res/android_s/ohm_hybrid-fastboot-flashall-16879.zip'
    download_file(s_system_url)
    assert upgrade_inf.build_version == "31"


@allure.step("Start downgrade: from S to U")
@pytest.mark.skipif(check_UpdaterApk(), reason='updater apk does not exist, skip the test')
def test_014_otaUpgrade(device):
    # To download file
    with open(f'{tmp_path}/ota_url.txt', 'r') as f:
        content = f.read()
    # print(content)
    update(content.strip())
    upgrade_inf.root()
    output_b = upgrade_inf.getprop("ro.boot.slot_suffix")
    assert output_b != output
