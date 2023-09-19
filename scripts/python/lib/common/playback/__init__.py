import logging
import time
import pytest
from tools.resManager import ResManager
from lib.common.system.ADB import ADB
from lib import CheckAndroidVersion

res_manager = ResManager()

class Environment_Detection(ADB, ResManager, CheckAndroidVersion):
    def replace_logd(self):
        if ('ott_hybrid' or 'ott_hybrid_t' or 'ott_hybrid_compatibility' or 'ott_hybrid_t_compatibility') == pytest.target.get("prj"):
            LOGD = 'logd'
            LOGD_JSON = 'll_aut_carton.json'
            self.root()
            self.run_shell_cmd(
                'pm disable com.google.android.tungsten.setupwraith;settings put secure user_setup_complete 1;settings put secure tv_user_setup_complete 1;settings put global device_provisioned 1;')

            # Check logd
            logd_flag = self.checkoutput('ls -la /system/bin/logd')
            if '2022' not in logd_flag:
                self.root()
                self.run_adb_cmd_specific_device(['remount'])
                time.sleep(5)
                self.push(f'/var/www/res/caton/{LOGD}', '/system/bin/')
                self.push(f'/var/www/res/caton/{LOGD_JSON}', '/data/')
                self.run_shell_cmd("setenforce 0")
                self.run_shell_cmd("stop logd")
                self.run_shell_cmd("start logd")
                self.run_shell_cmd("setprop vendor.logd.aut.enable 1")

    def android_s_so_add(self):
        if pytest.target.get("prj") == "ott_hybrid" or pytest.target.get("prj") == "ott_hybrid_compatibility":
            MS12_SO = "libdolbyms12.so"
            ms12_flag = self.checkoutput('ls -la /odm/lib/ms12/')
            if MS12_SO not in ms12_flag:
                res_manager.get_target(path="ms12_X4", source_path="so/ms12_X4")
                logging.info("android push so")
                self.root()
                self.run_shell_cmd("setenforce 0")
                self.run_adb_cmd_specific_device(["remount"])
                self.push(f"/home/amlogic/so/ms12_X4/{MS12_SO}", "/oem/lib/ms12/libdolbyms12.so")
                self.reboot()
                start_time = time.time()
                while time.time() - start_time < 60:
                    reboot_check = self.run_shell_cmd("getprop sys.boot_completed")[1]
                    if reboot_check == "1":
                        logging.info("booted up")
                        break
                    else:
                        time.sleep(5)
                reboot_check = self.run_shell_cmd("getprop sys.boot_completed")[1]
                if reboot_check != "1":
                    raise Exception('boot up run time error')
                else:
                    pass
                time.sleep(20)
            else:
                logging.info(f"{MS12_SO} exists")

    def add_so(self):
        if pytest.target.get("prj") == "ott_hybrid_widevine_cas":
            self.root()
            self.run_adb_cmd_specific_device(["remount"])
            time.sleep(5)
            self.push("/home/amlogic/so/wvcas_so/libdec_ca_wvcas.system.so", "/system_ext/lib/")
            self.run_shell_cmd("chmod 644 /system_ext/lib/libdec_ca_wvcas.system.so")
            self.push("/home/amlogic/so/wvcas_so/libdsm.system.so", "/system_ext/lib/")
            self.run_shell_cmd("chmod 644 /system_ext/lib/libdsm.system.so")
            self.push("/home/amlogic/so/wvcas_so/wvcas_iptv_test_sys", "/system_ext/bin/")
            self.run_shell_cmd("chmod 755 /system_ext/bin/wvcas_iptv_test_sys")
            self.push("/home/amlogic/Videos/wvcas_video/bbb_1080p_30fps_mp3_enc_cbc_fixed_content_iv.ts", "/data")
            self.reboot()
            start_time = time.time()
            while time.time() -start_time < 60:
                reboot_check = self.run_shell_cmd("getprop sys.boot_completed")[1]
                if reboot_check == "1":
                    logging.info("booted up")
                    break
                else:
                    time.sleep(5)
            reboot_check = self.run_shell_cmd("getprop sys.boot_completed")[1]
            if reboot_check != "1":
                raise Exception('boot up run time error')
            else:
                pass
            time.sleep(5)
        elif pytest.target.get("prj") == "ott_hybrid_compatibility":
            self.root()
            self.run_adb_cmd_specific_device(["remount"])
            time.sleep(5)
            self.push("/home/amlogic/kit/dump_decoder.sh", "/data/")
            time.sleep(2)
        elif pytest.target.get("prj") == "ott_sanity":
            self.root()
            self.run_adb_cmd_specific_device(["remount"])
            time.sleep(5)
            self.push("/home/amlogic/so/adt4_camera2/Camera2", "/product/app")
            self.run_shell_cmd("mkdir /product/lib/")
            self.push("/home/amlogic/so/adt4_camera2/lib/libjni_jpegutil.so", "/product/lib")
            self.push("/home/amlogic/so/adt4_camera2/lib/libjni_tinyplanet.so", "/product/lib")
            time.sleep(5)
            self.reboot()
            start_time = time.time()
            while time.time() - start_time < 60:
                reboot_check = self.run_shell_cmd("getprop sys.boot_completed")[1]
                if reboot_check == "1":
                    logging.info("booted up")
                    break
                else:
                    time.sleep(5)
            reboot_check = self.run_shell_cmd("getprop sys.boot_completed")[1]
            if reboot_check != "1":
                raise Exception('boot up run time error')
            else:
                pass
            time.sleep(5)
        else:
            pass

