import pytest
import time
import re
import os
import logging
from tests.OTT.lib.System import Upgrade, Platform
from . import *

upgrade_inf = Upgrade()

skip_navigation = 'pm disable com.google.android.tungsten.setupwraith'


def test_otaUpgrade(device):
    # Init
    # Todo: should set default value if there is no item in yaml configuration
    p_conf_ota = config_yaml.get_note('conf_ota')
    if p_conf_ota is not None:
        p_conf_ota_url = p_conf_ota['ota_url']
    else:
        logging.error('can not get p_conf_ota_url')
        assert False

    platform_inf = Platform()

    # To download file
    download_f, file_name = platform_inf.get_downloadFolder(p_conf_ota_url)
    print(' --- download_f.name: ', download_f)

    # To mount Udisk
    uuid = upgrade_inf.getUUID()
    basepath = "/storage/" + uuid
    print(' --- basepath:', basepath)


    upgrade_inf.push_UdiskZip(download_f, basepath)
    os.system('pwd;adb shell ' + skip_navigation)
    os.system('adb reboot;sleep 30')

    # To run upgrade
    time.sleep(15)
    upgrade_inf.start_updater()
    upgrade_inf.wait_and_tap('UPDATE LOCAL', "text")

    upgrade_inf.enter()
    time.sleep(5)
    upgrade_inf.uiautomator_dump(upgrade_inf.logdir)
    dumpInfo = upgrade_inf.get_dump_info()
    # ota_zip = re.findall(download_f, dumpInfo, re.S)[0]
    ota_zip = upgrade_inf.get_zip(uuid, download_f)

    if ota_zip in dumpInfo:
        logging.info('can update')
        upgrade_inf.find_and_tap(ota_zip, "text")
        upstep = upgrade_inf.upgrade_step()
        # print(' --- upstep: ', upstep)
        assert True if upstep else False
    else:
        logging.info('can not update')

    # To delete local file
    os.system(f'pwd;rm -rf {download_f}')
    print(' --- teardown clear env done')
    upgrade_inf.stop_updater()