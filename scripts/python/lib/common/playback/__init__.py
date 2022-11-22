import logging
import time
import pytest
from tools.resManager import ResManager
from lib.common.system.ADB import ADB
from lib import CheckAndroidVersion


class Environment_Detection(ADB, ResManager, CheckAndroidVersion):
    def android_s_so_check(self):
        pass
        # if self.getprop("ro.build.version.sdk") == "31":
        #     IPTV_MEDIA_SO = 'libAmIptvMedia.so'
        #     FFMPEG_CTC_SO = 'libffmpeg_ctc.so'
        #     logging.info("Android s environment detection")
        #     if 'ott_hybrid' == pytest.target.get("prj"):
        #         self.root()
        #         self.run_shell_cmd(
        #             'pm disable com.google.android.tungsten.setupwraith;settings put secure user_setup_complete 1;settings put secure tv_user_setup_complete 1;settings put global device_provisioned 1;')
        #         # adb.reboot()
        #         time.sleep(5)
        #
        #     # # Check iptv media so
        #     # if IPTV_MEDIA_SO not in self.checkoutput('ls /system_ext/lib/'):
        #     #     self.root()
        #     #     self.run_adb_cmd_specific_device(['remount'])
        #     #     time.sleep(5)
        #     #     self.get_target("apk/libAmIptvMedia.so")
        #     #     self.push('res/apk/libAmIptvMedia.so', '/system_ext/lib/')
        #     #     logging.info("reboot , waiting for the device")
        #     #     self.reboot()
        #     #     start_time = time.time()
        #     #     logging.debug("Waiting for bootcomplete")
        #     #     while time.time() - start_time < 60:
        #     #         reboot_check = self.run_shell_cmd('getprop sys.boot_completed')[1]
        #     #         if reboot_check == '1':
        #     #             logging.info("Device booted up !!!!")
        #     #             break
        #     #         else:
        #     #             time.sleep(5)
        #     #     logging.info("wait for the device enter the home page")
        #     #     check_time = time.time()
        #     #     while time.time() - check_time < 30:
        #     #         if self.find_element('Add account', 'text') or self.find_element('Search', 'text'):
        #     #             break
        #     #         else:
        #     #             time.sleep(5)
        #     #     self.root()
        #     #
        #     # # Check ffmpeg so
        #     # # if FFMPEG_CTC_SO not in self.checkoutput('ls /system_ext/lib/'):
        #     # if FFMPEG_CTC_SO not in self.checkoutput('ls /system/lib/'):
        #     #     self.root()
        #     #     self.run_adb_cmd_specific_device(['remount'])
        #     #     time.sleep(5)
        #     #     self.get_target("apk/libffmpeg_ctc.so")
        #     #     self.push('res/apk/libffmpeg_ctc.so', '/system/lib/')
        #     #     # self.push('res/apk/libffmpeg_ctc.so', '/system_ext/lib/')
        #     #     logging.info("reboot , waiting for the device")
        #     #     self.reboot()
        #     #     start_time = time.time()
        #     #     logging.debug("Waiting for bootcomplete")
        #     #     while time.time() - start_time < 60:
        #     #         reboot_check = self.run_shell_cmd('getprop sys.boot_completed')[1]
        #     #         if reboot_check == '1':
        #     #             logging.info("Device booted up !!!!")
        #     #             break
        #     #         else:
        #     #             time.sleep(5)
        #     #     logging.info("Wait for the device enter the home page")
        #     #     check_time = time.time()
        #     #     while time.time() - check_time < 30:
        #     #         if self.find_element('Add account', 'text') or self.find_element('Search', 'text'):
        #     #             break
        #     #         else:
        #     #             time.sleep(5)
        #     #     self.root()
        #
        #     # Check mediasync so
        #     avsync_flag = self.checkoutput('ls -la /system_ext/lib/libmediahal_mediasync.system.so')
        #     logging.debug(f"Avsync so status is {avsync_flag}")
        #     if '2022' not in avsync_flag:
        #         self.root()
        #         self.run_adb_cmd_specific_device(['remount'])
        #         time.sleep(5)
        #         self.push('/home/amlogic/mediahal/system_ext/*', '/system_ext/lib/')
        #         self.push('/home/amlogic/mediahal/vendor/*', '/vendor/lib/')
        #         logging.info("reboot , waiting for the device")
        #         self.reboot()
        #         start_time = time.time()
        #         logging.debug("Waiting for bootcomplete")
        #         while time.time() - start_time < 60:
        #             reboot_check = self.run_shell_cmd('getprop sys.boot_completed')[1]
        #             if reboot_check == '1':
        #                 logging.info("Device booted up !!!!")
        #                 break
        #             else:
        #                 time.sleep(5)
        #         logging.info("wait for the device enter the home page")
        #         check_time = time.time()
        #         while time.time() - check_time < 30:
        #             if self.find_element('Add account', 'text') or self.find_element('Search', 'text'):
        #                 break
        #             else:
        #                 time.sleep(5)
        #         self.root()
            # self.run_shell_cmd("setprop media.ammediaplayer.enable 1;setprop iptv.streamtype 1")
