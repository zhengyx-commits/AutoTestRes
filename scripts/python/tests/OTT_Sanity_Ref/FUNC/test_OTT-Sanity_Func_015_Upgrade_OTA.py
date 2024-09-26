import pytest
import time
import re
import os
import logging
from tests.OTT.lib.System import Upgrade, Platform
from tests.OTT_Sanity_Ref import config_yaml

config_system_cfg = config_yaml.get_note('conf_system')
p_conf_system_url = config_system_cfg['ota_url']

upgrade_inf = Upgrade()

skip_navigation = 'pm disable com.google.android.tungsten.setupwraith;settings put secure user_setup_complete 1;settings put secure tv_user_setup_complete 1;settings put global device_provisioned 1'


def check_UpdaterApk():
    check_apk = str(upgrade_inf.subprocess_run('ls -la /data/data/com.droidlogic.updater '))
    logging.debug(f'check_apk status : {check_apk}')
    if 'returncode=1' in check_apk:
        return True
    else:
        return False


@pytest.mark.skipif(check_UpdaterApk(), reason='updater apk does not exist, skip the test')
def test_otaUpgrade(device):
    platform_inf = Platform()
    # To download file
    download_f, file_name = platform_inf.get_downloadFolder(p_conf_system_url)
    logging.info(f' --- download_f.name: {download_f}')

    # To mount Udisk
    uuid = upgrade_inf.getUUID()
    basepath = "/storage/" + uuid
    logging.info(f' --- basepath: {basepath}')

    upgrade_inf.push_UdiskZip(download_f, basepath)

    os.system('pwd;adb shell ' + skip_navigation)
    os.system('adb reboot;sleep 30')

    # To run upgrade
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
        assert False

    # To delete local file
    os.system(f'pwd;rm -rf {download_f}')
    logging.info(' --- teardown clear env done')
    upgrade_inf.stop_updater()
