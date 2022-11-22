#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/5/5 09:29
# @Author  : chao.li
# @Site    :
# @File    : coco.py
# @Software: PyCharm

import logging
import re
import subprocess
import time

from lib.common.system.ADB import ADB
from protocol.aats.aats_target.aats_adb_target import AATSADBTarget


class Reboot:
    '''
    reboot test over adb for iptv object 

    Attributes:
        bootup_time_filepath : boot up time log file 
        adb_cmd : logcat command for boot up search
        device_id : device number
        run_times : reboot times
        repeat_flag : multi test flag
        aats_adb_target : framework adb target
        adb : ADB instance

    '''

    def __init__(self, adb_cmd='', device_id='', logdir='', run_times='', repeat=False):
        self.bootup_time_filepath = logdir + "/" + "boot_up_time.log"
        self.adb_cmd = adb_cmd
        self.device_id = device_id
        self.run_times = run_times
        self.repeat_flag = repeat
        self.adb = ADB()
        # self.version = {"version": self.adb.build_version}
        self.aats_adb_target = AATSADBTarget(self.device_id, version=self.adb.build_version)

    def reboot_once(self, timeout=60):
        '''
        reboot device once
        @param timeout: timeout
        @return: bootup status : boolean
        '''
        if self.adb.build_version == "31":
            launcher_log = b"com.google.android.apps.tv.launcherx/com.google.android.apps.tv.launcherx.home.HomeActivity"
        else:
            launcher_log = b"com.bestv.ott.baseservices/com.bestv.ott.wraplauncher.WrapActivity"
        start_time = time.time()
        self.aats_adb_target.reboot()
        p = subprocess.Popen(self.adb_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        res = ""
        while True:
            recv = p.stdout.readline()
            logging.debug(f"recv:{recv}")
            if re.search(launcher_log, recv):
                res = True
                break
            else:
                res = False
                if time.time() - start_time > timeout:
                    break
        if res == True:
            end_time = time.time()
            run_time = end_time - start_time
            logging.info(f"run_time:{run_time}")
            return run_time
        elif res == False:
            logging.info("haven't get launcher apk signal")
            return False

    def count_reboot_cost(self):
        '''
        Calculate the boot time
        @return: reboot status list [boolean]
        '''
        logging.info("delete boot AD")
        self.adb.run_shell_cmd("rm -rf /data/local/")
        logging.info('start test reboot')
        test_result = []
        if self.repeat_flag:
            for _ in range(int(self.run_times)):
                run_time = self.reboot_once()
                if run_time:
                    test_result.append(run_time)
                else:
                    return False
        else:
            run_time = self.reboot_once()
            if run_time:
                test_result.append(run_time)
            else:
                return False
        return test_result

    def write_to_file(self, test_result):
        '''
        write reboot status to boot up file
        @param test_result: reboot status list [boolean]
        @return: None
        '''
        for time in test_result:
            with open(self.bootup_time_filepath, "a+", encoding="utf-8") as f:
                f.write(str(time))
                f.write('\n')
