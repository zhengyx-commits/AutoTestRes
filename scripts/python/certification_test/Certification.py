#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Author  : yu.zeng
# @Site    :
# @File    : Certification.py
# @Software: PyCharm
import fnmatch
import json
import logging
import os
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path
import random
from xml.dom import minidom
import paramiko
import serial
from certification_test import config_certification, android_type, server_site
from datetime import datetime, timedelta


# noinspection PyUnboundLocalVariable
class Certification(object):
    RUN_COMMAND = {
        "cts": "run cts",
        "gts": "run gts",
        "tvts": "run tvts-cert",
        "vts": "run vts",
        "sts": "run sts-dynamic-full"
    }
    RUN_RETRY = {
        "tvts": "run commandAndExit retry -r {}",
        "else": "run retry --retry {}"
    }
    CHECK_RELEASE = "getprop | grep finger| head -n 1"
    OPEN_SETTINGS = "am start -n com.android.tv.settings/.MainSettings"
    CLOSE_USB_VERIFY = "settings put global verifier_verify_adb_installs 0"
    STAY_AWAKE = "settings put global stay_on_while_plugged_in 1"
    OPEN_LOCATION = "settings put secure location_mode 3"
    GET_CURRENT_WINDOW = "dumpsys window | grep mCurrentFocus"
    NETFLIX_PACKAGE = 'com.netflix.ninja'
    CTS_ABNORMAL_LOG = "*I/ModuleListener:*android.devicepolicy.cts*"
    GOOGLE_PAY = "am start -n com.android.vending/com.google.android.finsky.tvmainactivity.TvMainActivity"
    STS_TEST_ARGS = "--test-arg com.android.compatibility.common.tradefed.testtype.JarHostTest:set-option:android" \
                    ".security.sts.KernelLtsTest:acknowledge_kernel_update_requirement_warning_failure:true "
    CTS_BASIC_FILTER = "--exclude-filter CtsDevicePolicyManagerTestCases --exclude-filter CtsDevicePolicySimTestCases " \
                       "--exclude-filter CtsDevicePolicySimTestCases[run-on-clone-profile] --exclude-filter " \
                       "CtsDevicePolicySimTestCases[run-on-secondary-user] --exclude-filter " \
                       "CtsDevicePolicySimTestCases[run-on-work-profile] --exclude-filter CtsDevicePolicyTestCases " \
                       "--exclude-filter CtsDevicePolicyTestCases[run-on-clone-profile] --exclude-filter " \
                       "CtsDevicePolicyTestCases[run-on-secondary-user] --exclude-filter CtsDevicePolicyTestCases[" \
                       "run-on-work-profile] "
    CTS_FILTER = "--exclude-filter CtsMediaAudioTestCases --exclude-filter CtsMediaAudioTestCases[instant] " \
                 "--exclude-filter CtsMediaBitstreamsTestCases --exclude-filter CtsMediaCodecTestCases " \
                 "--exclude-filter CtsMediaCodecTestCases[instant] --exclude-filter CtsMediaDecoderTestCases " \
                 "--exclude-filter CtsMediaDecoderTestCases[instant] --exclude-filter " \
                 "CtsMediaDrmFrameworkTestCases --exclude-filter CtsMediaDrmFrameworkTestCases[instant] " \
                 "--exclude-filter CtsMediaEncoderTestCases --exclude-filter CtsMediaEncoderTestCases[instant] " \
                 "--exclude-filter CtsMediaExtractorTestCases --exclude-filter CtsMediaExtractorTestCases[" \
                 "instant] --exclude-filter CtsMediaHostTestCases --exclude-filter CtsMediaHostTestCases[" \
                 "instant] --exclude-filter CtsMediaMiscTestCases --exclude-filter CtsMediaMiscTestCases[" \
                 "instant] --exclude-filter CtsMediaMuxerTestCases --exclude-filter CtsMediaMuxerTestCases[" \
                 "instant] --exclude-filter CtsMediaParserHostTestCases --exclude-filter " \
                 "CtsMediaParserHostTestCases[instant] --exclude-filter CtsMediaParserTestCases " \
                 "--exclude-filter CtsMediaPerformanceClassTestCases --exclude-filter " \
                 "CtsMediaPlayerTestCases --exclude-filter CtsMediaPlayerTestCases[instant] " \
                 "--exclude-filter CtsMediaProviderTranscodeTests --exclude-filter " \
                 "CtsMediaRecorderTestCases --exclude-filter CtsMediaRecorderTestCases[instant] " \
                 "--exclude-filter CtsMediaStressTestCases --exclude-filter CtsMediaTranscodingTestCases" \
                 " --exclude-filter CtsMediaV2TestCases --exclude-filter CtsMediaProviderTranscodeTests" \
                 " --exclude-filter CtsMediaProjectionTestCases "

    def __init__(self, suite=""):
        self.certification = suite.lower()
        self.config_certification = config_certification
        self.android_type = android_type
        self.server = self.config_certification["server"]
        self.certification_devices = self.config_certification["devices"][self.certification]
        if "test_suite_path" in self.config_certification:
            self.suite_bin = self.config_certification["test_suite_path"][
                                 self.certification] + f"/tools/{self.certification}-tradefed"
            self.suite_folder = self.config_certification["test_suite_path"][self.certification]
        else:
            if server_site == "XA":
                self.suite_folder = self.find_suite_main_folder(search_path="/home/amlogic/xTS")
                self.suite_bin = self.find_suite_bin(search_path="/home/amlogic/xTS")
            else:
                self.suite_folder = self.find_suite_main_folder()
                self.suite_bin = self.find_suite_bin()
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.server["ip"], self.server["port"], self.server["username"], self.server["password"])
        self.pass_oobe_fail = []
        self.workspace = os.environ.get("WORKSPACE", subprocess.getoutput("pwd"))
        self.start_timestamp = os.environ.get("START_TIME", int(time.time()))
        self.build_url = os.environ.get("BUILD_URL",
                                        "https://jenkins-sh.amlogic.com/job/FAE/job/AutoTest/job/OTT/view/XTS/")
        self.report_url = "http://aut.amlogic.com/AutoTest/AllureReport/XTS_Test/{}/{}/{}/last_report/".format(
            android_type, server_site, self.certification.upper())
        self.image_url = os.environ.get("TEST_IMAGE_URL")
        if self.image_url:
            self.devices_list = self.check_release_key()
        else:
            self.devices_list = [device["device_id"] for device in self.certification_devices]
        self.check_network_connection()
        self.google_tv_list = []
        self.basic_tv_list = []
        self.min_fails_results_dir = None

    def channel(self):
        channel = self.ssh.get_transport().open_session()
        channel.get_pty()
        channel.invoke_shell()
        return channel

    def find_suite_bin(self, search_path=""):
        if not search_path:
            search_path = f"/home/{self.server['username']}"
        target = "{}-tradefed".format(self.certification)
        for root, _, files in os.walk(search_path):
            if target in files:
                return os.path.join(root, target)
        raise Exception(f"{self.certification.upper()} test suite not found,exit test!!!!!!!!!")

    def find_suite_main_folder(self, search_path=""):
        if not search_path:
            search_path = f"/home/{self.server['username']}"
        target = "android-{}".format(self.certification)
        for root, dirs, _, in os.walk(search_path):
            if target in dirs:
                suite_path = os.path.join(root, target)
                logging.debug("{} test suit folder: {}".format(self.certification.upper(), suite_path))
                return os.path.join(root, target)
        logging.info(f"{self.certification.upper()} test suite not found!")

    @staticmethod
    def check_network_connection(time_out=3600):
        counter = 0
        while counter < time_out:
            # The os.system command will return 0 if the ping is successful
            if os.system('ping -c 1 www.google.com > /dev/null') == 0:
                logging.info("Network connection is active, successfully pinged.")
                return
            logging.info("Network connection is not available, continuing to ping...")
            time.sleep(10)  # Pause for 10 seconds in each iteration, adjust as needed
            counter += 10
        raise Exception("Network connection is not available, exceeded the 1-hour timeout.")

    def check_wifi_status(self):
        if self.certification == "cts":
            wifi_ssid = self.config_certification["wifi"]["cts_wifi_ssid"]
            wifi_pwd = self.config_certification["wifi"]["cts_wifi_pwd"]
        elif self.certification == "tvts":
            wifi_ssid = self.config_certification["wifi"]["tvts_wifi_ssid"]
            wifi_pwd = self.config_certification["wifi"]["tvts_wifi_pwd"]
        else:
            wifi_ssid = self.config_certification["wifi"]["public_wifi_ssid"]
            wifi_pwd = self.config_certification["wifi"]["public_wifi_pwd"]
        for device in self.devices_list:
            os.system(f"adb -s {device} shell cmd wifi set-wifi-enabled enabled")
            res = subprocess.getoutput(f"adb -s {device} shell cmd wifi status")
            if wifi_ssid not in res:
                logging.info(f"{res}")
                try:
                    os.system(f"adb -s {device} shell cmd wifi connect-network {wifi_ssid} wpa2 {wifi_pwd}")
                    time.sleep(10)
                except Exception as e:
                    logging.info(f"Connect wifi failed\n{e}")
            else:
                logging.info(f"Wifi status: {device} wifi has connected to {wifi_ssid}")

    def run_test(self, command):
        if self.certification == "vts":
            self.check_wifi_status()
        channel = self.channel()
        channel.send(command)
        prev_time = None
        log_timeout_count = 0
        pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - .*I/ModuleListener:\s+\[\d+/\d+\]\s+(\w+)\s+" \
                  r"android.devicepolicy.cts"
        while True:
            log = str(channel.recv(1024), 'utf-8', 'ignore').strip()
            logging.info(log)
            if self.certification == "cts" and self.android_type == "Android_U":
                if fnmatch.fnmatch(log, self.CTS_ABNORMAL_LOG):
                    matches = re.findall(pattern, log)
                    if matches:
                        current_time_str, device = matches[0]
                        current_time = datetime.strptime(current_time_str, "%Y-%m-%d %H:%M:%S,%f")
                        if prev_time:
                            time_difference = current_time - prev_time
                            if time_difference > timedelta(seconds=299):
                                log_timeout_count += 1
                        prev_time = current_time
                if log_timeout_count >= 10:
                    self.reboot_device(device)
                    prev_time = None
                    log_timeout_count = 0
            if 'FAILED            :' in log or 'PASSED            :' in log:
                time_now = time.time()
                wait_timeout = 600
                while time.time() - time_now <= wait_timeout:
                    if self.find_last_result_file():
                        break
                channel.close()
                return log

    def reboot_device(self, device):
        for info in self.certification_devices:
            if device in info:
                power_relay = info['powerRelay']
                os.system(f"{self.workspace}/AutoTestRes/bin/powerRelay {power_relay} all off")
                time.sleep(5)
                os.system(f"{self.workspace}/AutoTestRes/bin/powerRelay {power_relay} all on")

    def find_last_result_file(self):
        target_path = self.suite_folder + "/results"
        all_results = subprocess.getoutput(f"ls {target_path} | grep -v \".zip\" | grep -v 'latest'")
        last_report = all_results.split("\n")[-1]
        last_report_path = f"{target_path}/{last_report}"
        logging.debug("Last result fodler : {}".format(last_report_path))
        res = subprocess.getoutput(f"ls {last_report_path}")
        if ("test_result.html" in res) and ("test_result_failures_suite.html" in res):
            if self.android_type == "Android_U" and self.certification == 'cts':
                time.sleep(300)
            else:
                time.sleep(180)
            return True
        else:
            return False

    def start_suite_bin(self):
        process = subprocess.Popen(self.suite_bin, shell=True)
        return process

    def get_all_failed_modules(self, directory=None):
        failed_modules_list = []
        fail_modules_dict = {}
        if directory:
            file_path = self.suite_folder + f"/results/{directory}/test_result_failures_suite.html"
        else:
            file_path = self.suite_folder + "/results/latest/test_result_failures_suite.html"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    all_modules = re.findall(r'name="[^"]+%C2%A0([^"]+)"', line)
                    all_fails = re.findall(r'<td>.*?&nbsp;(.*?)</a></td><td>\d+</td><td>(\d+)</td>', line)
                    if all_modules:
                        failed_modules_list.append(all_modules[0])
                    if all_fails:
                        if all_fails[0][1] != '0':
                            fail_modules_dict[all_fails[0][0]] = int(all_fails[0][1])
            for module in failed_modules_list:
                if module not in fail_modules_dict:
                    fail_modules_dict[module] = None
            return fail_modules_dict
        else:
            raise Exception("Could not find last results,exit test!")

    def get_min_fail_result(self, report=False):
        new_test_results = []
        latest_min_fail = {}
        command = self.suite_bin + " " + "l r"
        results = subprocess.check_output(command.split(), encoding='utf-8')
        # logging.info(results)
        pattern = r'\n(\d+)\s+\d+\s+(\d+)\s+(\d+)\sof\s\d+\s+(\d{4}.\d{2}.\d{2}_\d{2}.\d{2}.\d{2})\s+'
        match_results = re.findall(pattern, results)
        if match_results:
            for result in match_results:
                test_time = datetime.strptime(result[-1], "%Y.%m.%d_%H.%M.%S").timestamp()
                if int(test_time) > int(self.start_timestamp):
                    new_test_results.append(result)
            if report:
                max_module = max(new_test_results, key=lambda x: int(x[2]))
                max_module_list = [j for j in new_test_results if j[2] == max_module[2]]
                if len(max_module_list) > 1:
                    min_fail = min(max_module_list, key=lambda x: int(x[1]))
                    min_fail_list = [i for i in max_module_list if i[1] == min_fail[1]]
                    if len(min_fail_list) > 1:
                        final_choice = random.choice(min_fail_list)
                    else:
                        final_choice = min_fail_list[0]
                else:
                    final_choice = max_module_list[0]
            else:
                min_fail = min(new_test_results, key=lambda x: int(x[1]))
                min_fail_list = [i for i in new_test_results if i[1] == min_fail[1]]
                if len(min_fail_list) > 1:
                    max_module = max(min_fail_list, key=lambda x: int(x[2]))
                    max_module_list = [j for j in min_fail_list if j[2] == max_module[2]]
                    if len(max_module_list) > 1:
                        final_choice = random.choice(max_module_list)
                    else:
                        final_choice = max_module_list[0]
                else:
                    final_choice = min_fail_list[0]
            latest_min_fail["session"] = final_choice[0]
            latest_min_fail["fail"] = final_choice[1]
            latest_min_fail["module"] = final_choice[2]
            latest_min_fail["result_dir"] = final_choice[3]
            return latest_min_fail
        else:
            logging.info("The test result is abnormal,Please check result or pattern")
            return latest_min_fail

    def one_module_retry_command(self, module, devices, session=None):
        command_s = ''
        if session:
            last_session = session
        else:
            last_session = self.last_result()[0]
        for device in devices:
            command_s += " -s {}".format(device)
        if len(devices) == 1:
            shard_count = " "
        else:
            shard_count = " --shard-count {}".format(len(devices))
        run_retry_command = self.suite_bin + " " + self.RUN_RETRY["else"].format(
            last_session) + f" -m {module}" + shard_count + command_s + "\n"
        logging.info(f"Retry command: {run_retry_command}")
        return run_retry_command

    def execute_suite_command(self, suite_command):
        command = f"{self.suite_bin} {suite_command}"
        res = subprocess.check_output(command.split(), encoding="utf-8")
        return res

    def last_result(self):
        command = self.suite_bin + " " + "l r"
        result = subprocess.check_output(command.split(), encoding='utf-8')
        logging.info(result)
        last_session_info = re.findall(r"\n(\d+)\s+\d+\s+\d+", result)
        last_module_info = re.findall(r"\n\d+\s+\d+\s+\d+\s+(\d+)\sof\s(\d+)\s+", result)
        last_failed_info = re.findall(r"\n\d+\s+\d+\s+(\d+)\s+", result)
        if last_module_info and last_session_info and last_failed_info:
            last_num = last_session_info[-1]
            logging.info(f"Last session id: {last_num}")
            last_module = last_module_info[-1]
            if all(module_num == "0" for module_num in last_module):
                raise Exception("Last loop failed,can't retry")
            else:
                last_failed_num = int(last_failed_info[-1])
                if last_module[0] == last_module[1]:
                    return last_num, last_failed_num
                else:
                    if last_failed_num == 0:
                        logging.info("Failed number is 0 ,but not all modules completed")
                        return last_num, -1
                    else:
                        return last_num, last_failed_num
        else:
            raise Exception("Can't find last session id and last failed number,can't retry")

    def find_last_results(self):
        command = self.suite_bin + " " + "l r"
        result = subprocess.check_output(command.split(), encoding='utf-8')
        last_result_directory = re.findall(r"(\d{4}.\d{2}.\d{2}_\d{2}.\d{2}.\d{2})", result)
        if last_result_directory:
            return last_result_directory[-1]

    def zip_file(self, target=""):
        results_path = self.suite_folder + "/results/"
        logs_path = self.suite_folder + "/logs/"
        if target:
            result_directory = target
        else:
            result_directory = self.find_last_results()
        result_zip = self.workspace + f"/last_report/{result_directory}_results"
        log_zip = self.workspace + f"/last_report/{result_directory}_logs"
        try:
            shutil.make_archive(base_name=result_zip, format="tar", root_dir=results_path + result_directory)
            shutil.make_archive(base_name=log_zip, format="tar", root_dir=logs_path + result_directory)
        except Exception as e:
            logging.info(e)

    def create_run_command(self, filter=False):
        command_s = ""
        for device in self.devices_list:
            command_s += " -s {}".format(device)
        if len(self.devices_list) == 1:
            shard_count = " "
        else:
            shard_count = " --shard-count {}".format(len(self.devices_list))
        run_command_first = self.suite_bin + " " + self.RUN_COMMAND[self.certification] + shard_count + command_s + "\n"
        if self.certification == "sts":
            run_command_first = self.suite_bin + " " + self.RUN_COMMAND[
                self.certification] + shard_count + command_s + " " + self.STS_TEST_ARGS + "\n"
        if self.certification == "cts" and filter:
            run_command_first = self.suite_bin + " " + self.RUN_COMMAND[
                self.certification] + shard_count + command_s + " " + self.CTS_BASIC_FILTER + "\n"
        logging.info(f"Run command: {run_command_first}")
        return run_command_first

    def create_retry_command(self, single=False, session_id=None, filter=False, devices=None):
        # global device_list
        command_s = ""
        last_session = session_id if session_id else self.last_result()[0]
        if single:
            if self.certification == "cts":
                device_list = [self.config_certification["devices"]["cts_single"]["device_id"]]
            if self.certification == "tvts":
                device_list = [self.config_certification["devices"]["tvts_single"]["device_id"]]
        elif devices:
            device_list = devices
        else:
            device_list = self.devices_list
        logging.info(f"Current devices list : {device_list}")
        for device in device_list:
            command_s += " -s {}".format(device)
        if len(device_list) == 1:
            shard_count = " "
        else:
            shard_count = " --shard-count {}".format(len(device_list))
        if self.certification == "tvts":
            run_retry_command = self.suite_bin + " " + self.RUN_RETRY["tvts"].format(
                last_session) + shard_count + command_s + "\n"
        elif self.certification == "cts" and filter:
            run_retry_command = self.suite_bin + " " + self.RUN_RETRY["else"].format(
                last_session) + shard_count + command_s + " " + self.CTS_BASIC_FILTER + "\n"
        else:
            run_retry_command = self.suite_bin + " " + self.RUN_RETRY["else"].format(
                last_session) + shard_count + command_s + "\n"
        logging.info(f"Retry command: {run_retry_command}")
        return run_retry_command

    def copy_result_xml_file(self, filename, target=""):
        if filename not in ["old", "new"]:
            raise ValueError("filename must be 'old' or 'new'")
        source_file_name = "test_result.xml"
        result_comparison = Path(self.workspace) / 'result_comparison'
        target_file_name = f"test_result_{filename}.xml"
        old_file = result_comparison / 'test_result_old.xml'
        new_file = result_comparison / 'test_result_new.xml'
        if filename == "old":
            command = self.suite_bin + " " + "l r"
            result = subprocess.check_output(command.split(), encoding='utf-8')
            if old_file.exists() and new_file.exists():
                old_file.unlink()
                new_file.rename(old_file)
            elif new_file.exists() and not old_file.exists():
                new_file.rename(old_file)
            else:
                if "No results" in result:
                    logging.info("Maybe it is a new test suite,Has no results")
                else:
                    source_path = self.suite_folder + "/results/latest"
                    source_file = Path(source_path) / source_file_name
                    if source_file.is_file():
                        shutil.copy2(source_file, result_comparison / target_file_name)
        else:
            if target:
                source_path = self.suite_folder + f"/results/{target}"
            else:
                source_path = self.suite_folder + f"/results/latest"
            source_file = Path(source_path) / source_file_name
            if source_file.is_file():
                shutil.copy2(source_file, result_comparison / target_file_name)

    def generate_report(self, retry=False):
        html_copy_status = False
        if not retry:
            min_fails_results = self.get_min_fail_result(report=True)
            if min_fails_results:
                self.min_fails_results_dir = min_fails_results["result_dir"]
                target_path = self.suite_folder + f"/results/{self.min_fails_results_dir}"
            else:
                target_path = self.suite_folder + "/results/latest"
        else:
            target_path = self.suite_folder + "/results/latest"
        last_report_dir = Path(self.workspace) / 'last_report'
        last_report_dir.mkdir(exist_ok=True)
        # latest_zip = max((f for f in Path(target_path).iterdir() if f.is_file()), key=os.path.getmtime)
        # shutil.copy2(latest_zip, last_report_dir)
        if self.min_fails_results_dir:
            self.zip_file(target=self.min_fails_results_dir)  # Compress results and log files to last_report
        else:
            self.zip_file()
        file_to_copy = [('test_result_failures_suite.html', 'index.html'), "compatibility_result.css", "logo.png"]
        for file_info in file_to_copy:
            source_file_name = file_info[0] if isinstance(file_info, tuple) else file_info
            target_file_name = file_info[1] if isinstance(file_info, tuple) else file_info
            source_file = Path(target_path) / source_file_name
            if source_file.is_file():
                shutil.copy2(source_file, last_report_dir / target_file_name)
                logging.info(f"File {source_file_name} has copied to /last_report/")
                if "html" in source_file_name:
                    html_copy_status = True
            else:
                logging.info(f"File {source_file_name} not found")
        # Result html copy succeed ,create Summary.json
        if html_copy_status:
            end_timestamp = int(time.time())
            duration = end_timestamp - int(self.start_timestamp)
            data = {}
            test_data = {}
            index_html = last_report_dir / "index.html"
            with open(index_html, "r") as html_file:
                html_content = html_file.read()
            test_data["passed"] = re.findall(r"Passed</td><td>(.*?)</td>", html_content)[0]
            test_data["failed"] = re.findall(r"Failed</td><td>(.*?)</td>", html_content)[0]
            test_data["module_done"] = re.findall(r"Modules Done</td><td>(.*?)</td>", html_content)[0]
            test_data["module_total"] = re.findall(r"Modules Total</td><td>(.*?)</td>", html_content)[0]
            xts_project = self.certification.upper()
            data["projectName"] = f"{self.android_type} Certification"
            data["reportName"] = xts_project
            data["build_job_url"] = self.build_url
            data["statistic"] = test_data
            data["time"] = {
                "start": self.start_timestamp,
                "stop": end_timestamp,
                "duration": duration
            }
            data["chipset"] = self.config_certification["chip"]
            data["report_url"] = self.report_url
            file_path = last_report_dir / "summary.json"
            with open(file_path, "w") as json_file:
                json.dump(data, json_file, indent=4)
            logging.info(f"Summary.json of {xts_project} create successfully!")

    def bluetooth_powerRelay(self, method=False):
        """
        Args:
            method: if False control two serials else control one serial
        Returns:None
        """
        if method:
            powerRelay = self.config_certification["bluetooth_powerRelay_two"]
            serial1 = serial.Serial(powerRelay[0], 9600)
            serial0 = serial.Serial(powerRelay[1], 9600)
            try:
                logging.info("Start matching bluetooth remote")
                serial1.write(b'\xA0\x01\x01\xA2')  # Power on,simulate pressing the button
                serial0.write(b'\xA0\x01\x01\xA2')  # Power on,simulate pressing the button
                time.sleep(8)
                serial1.write(b'\xA0\x01\x00\xA1')  # Power off,simulate releasing the button
                serial0.write(b'\xA0\x01\x00\xA1')  # Power off,simulate releasing the button
                time.sleep(1)
                logging.info("Stop matching bluetooth remote")
                serial1.close()
                serial0.close()
            except KeyboardInterrupt:
                serial1.close()
                serial0.close()
        else:
            powerRelay = self.config_certification["bluetooth_powerRelay_one"]
            serial0 = serial.Serial(powerRelay, 9600)
            try:
                logging.info("Start matching bluetooth remote")
                serial0.write(b'\xA0\x01\x01\xA2')  # Power on,simulate pressing the button
                time.sleep(8)
                serial0.write(b'\xA0\x01\x00\xA1')  # Power off,simulate releasing the button
                time.sleep(1)
                logging.info("Stop matching bluetooth remote")
                serial0.close()
            except KeyboardInterrupt:
                serial0.close()

    def pair_bluetooth_remote(self, basic_mode=False, retry=False, loop=0):
        """
        Args:
            basic_mode: if False set Google TV else set Basic TV
            retry: Retry pass oobe failed devices
            loop: if third loop for cts,only one device to pass oobe
        Returns:
        """
        EXECUTE_OOBE_COUNT = 0
        HAS_IN_HOME = 0
        # Get devices list based on different situations
        if retry:
            devices = self.pass_oobe_fail
        else:
            if loop == 3 and self.certification == "cts":
                logging.info("The third loops for cts,only need one device to run retry!")
                devices = [self.config_certification["devices"]["cts_single"]["device_id"]]
            # elif loop == 2 and self.certification == "tvts":
            #     logging.info("The second loops for tvts,only need one device to run retry!")
            #     devices = [self.config_certification["devices"]["tvts_single"]["device_id"]]
            else:
                devices = self.devices_list
        for i in range(15):
            logging.info(f"Pair bluetooth_remote for {i + 1} times")
            # if self.certification == "gts":
            #     # Currently, GTS is equipped with single button pairing remote
            #     self.bluetooth_powerRelay()
            # else:
            self.bluetooth_powerRelay(method=True)
            for device_id in devices:
                ui_info = self.get_ui_info(device_id)
                if ("id/remote_pairing_video" in ui_info) or ("id/imageView1" in ui_info and "button exit" in ui_info):
                    logging.info(f"{device_id} is now in remote pairing mode, Continue to pair bluetooth_remote!")
                    continue
                elif ("text=\"Home\"" in ui_info) or ("text=\"Library\"" in ui_info and "text=\"Apps\"" in ui_info):
                    logging.info(f"{device_id} is now in the home page. This may failed image upgrade or "
                                 f"the OOBE process has passed.")
                    HAS_IN_HOME += 1
                    continue
                elif "text=\"Restart now\"" in ui_info:
                    logging.info(f"{device_id} now in sleep mode, reboot it!")
                    os.system(f"adb -s {device_id} reboot")
                    time.sleep(60)
                else:
                    logging.info(f"{device_id} Not in remote pairing, Start pass OOBE>>>>>>>>")
                    if basic_mode:  # Start basic mode oobe
                        if EXECUTE_OOBE_COUNT < 3:
                            self.pass_oobe(device=device_id, basic_mode=True)
                            EXECUTE_OOBE_COUNT += 1
                            break
                        else:
                            self.pass_oobe(device=device_id)
                            EXECUTE_OOBE_COUNT += 1
                            break
                    else:  # Start google tv mode oobe
                        if loop == 2:
                            self.pass_oobe(device=device_id, loop=2)
                            EXECUTE_OOBE_COUNT += 1
                            break
                        else:
                            if EXECUTE_OOBE_COUNT < 3:
                                self.pass_oobe(device=device_id)
                                EXECUTE_OOBE_COUNT += 1
                                break
                            else:
                                self.pass_oobe(device=device_id, basic_mode=True)
                                EXECUTE_OOBE_COUNT += 1
                                break
            if EXECUTE_OOBE_COUNT == len(devices) or HAS_IN_HOME == len(devices):
                logging.info("All devices has executed OOBE")
                break

    def check_oobe(self):
        oobe_pass_count = 0
        for device in self.devices_list:
            subprocess.run(["adb", "-s", device, "shell", "input keyevent 3"])
            time.sleep(2)
            activity = subprocess.check_output(["adb", "-s", device, "shell", self.GET_CURRENT_WINDOW]).decode()
            if "home.HomeActivity" in activity:
                logging.info(f"{device} in google TV mode")
                oobe_pass_count += 1
                self.google_tv_list.append(device)
            elif "home.VanillaModeHomeActivity" in activity:
                logging.info(f"{device} in basic TV mode")
                oobe_pass_count += 1
                self.basic_tv_list.append(device)
            else:
                logging.info(f"{device} may fail in passing OOBE")
                self.pass_oobe_fail.append(device)
        # if self.certification == "cts":
        if oobe_pass_count >= len(self.devices_list) - 1:
            return True
        else:
            return False

    def check_release_key(self):
        devices_list = []
        update_success_devices = []
        check_count = 0
        for device_info in self.certification_devices:
            devices_list.append(device_info["device_id"])
        image_build_number = re.findall(r"-(\d+)/", self.image_url)[-1]
        for device in devices_list:
            release_key = subprocess.getoutput(f"adb -s {device} shell getprop | grep finger| head -n 1")
            if image_build_number in release_key:
                logging.info(f"{device} update image successfully!")
                update_success_devices.append(device)
            else:
                logging.info(f"{device} update image failed!")
                check_count += 1
        if check_count >= 3:
            raise Exception("Update img failed number too much,exit test")
        else:
            return update_success_devices

    def get_ui_info(self, device):
        # os.system(f"adb -s {device} shell mkdir /sdcard/temp")
        os.system(f"adb -s {device} shell uiautomator dump > /dev/null")
        os.system(f"adb -s {device} pull /sdcard/window_dump.xml {self.workspace + '/'} > /dev/null")
        xml_path = self.workspace + "/window_dump.xml"
        with open(xml_path, 'r') as f:
            temp = f.read()
        return temp

    def get_button_coordinates(self, text, attribute="text"):
        xml_path = self.workspace + "/window_dump.xml"
        xml_file = minidom.parse(xml_path)
        itemlist = xml_file.getElementsByTagName('node')
        bounds = None
        for item in itemlist:
            # logging.debug(f'try to find {text} - {item.attributes[attribute].value}')
            if text == item.attributes[attribute].value:
                bounds = item.attributes['bounds'].value
                logging.info(f"Find {text} - {item.attributes[attribute].value}")
                break
        if bounds is None:
            logging.error("attr: %s not found" % attribute)
            return -1, -1
        bounds = re.findall(r"\[(\d+),(\d+)]", bounds)
        x_start, y_start = bounds[0]
        x_end, y_end = bounds[1]
        x_midpoint, y_midpoint = (int(x_start) + int(x_end)) / 2, (int(y_start) + int(y_end)) / 2
        return int(x_midpoint), int(y_midpoint)

    def pass_oobe(self, device, basic_mode=False, loop=0):
        """
        Args:
            loop: int
            device: adb serial number
            basic_mode: if False set Google TV else set Basic TV
        Returns:None
        """
        if self.certification == "cts":
            wifi_ssid = self.config_certification["wifi"]["cts_wifi_ssid"]
            wifi_pwd = self.config_certification["wifi"]["cts_wifi_pwd"]
            account_username = self.config_certification["google_account"]["cts_username"]
            account_pwd = self.config_certification["google_account"]["cts_password"]
        elif self.certification == "tvts":
            wifi_ssid = self.config_certification["wifi"]["tvts_wifi_ssid"]
            wifi_pwd = self.config_certification["wifi"]["tvts_wifi_pwd"]
            account_username = self.config_certification["google_account"]["public_username"]
            account_pwd = self.config_certification["google_account"]["public_password"]
        else:
            wifi_ssid = self.config_certification["wifi"]["public_wifi_ssid"]
            wifi_pwd = self.config_certification["wifi"]["public_wifi_pwd"]
            account_username = self.config_certification["google_account"]["public_username"]
            account_pwd = self.config_certification["google_account"]["public_password"]
        logging.info(f"Start to pass OOBE for device {device}")
        os.system(f"adb -s {device} shell \"input keyevent 4;input keyevent 4\"")
        for _ in range(25):
            ui_info = self.get_ui_info(device)
            time.sleep(3)
            if "English (United States)" in ui_info:
                logging.info("Choose language")
                x, y = self.get_button_coordinates("English (United States)")
                logging.info(f">English (United States)< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
            if ("text=\"Home\"" in ui_info) or ("text=\"Library\"" in ui_info and "text=\"Apps\"" in ui_info):
                logging.info(f"{device} is now in the home page. This may failed image upgrade or "
                             f"the OOBE process has passed.")
                break
            if "Quickly set up your TV with your Android phone?" in ui_info:
                logging.info("Use phone to set up android tv")
                x, y = self.get_button_coordinates("Skip")
                logging.info(f">Skip< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
            if "American Samoa" in ui_info:
                logging.info("Choose a country")
                x, y = self.get_button_coordinates("American Samoa")
                logging.info(f">American Samoa< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
            if "Set up Google TV" in ui_info:
                logging.info("Choose Google TV or Basic TV")
                if basic_mode:
                    x, y = self.get_button_coordinates("Set up basic TV")
                    logging.info(f">Set up basic TV< coordinates:{x} {y}")
                    os.system(f"adb -s {device} shell input tap {x} {y}")
                else:
                    x, y = self.get_button_coordinates("Set up Google TV")
                    logging.info(f">Set up Google TV< coordinates:{x} {y}")
                    os.system(f"adb -s {device} shell input tap {x} {y}")
                time.sleep(3)
            if "You're connected to" in ui_info:
                logging.info("Has connected wifi,Continue")
                x, y = self.get_button_coordinates("Continue")
                logging.info(f">Continue< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
                time.sleep(20)
            if "You're connected using Ethernet" in ui_info:
                logging.info("Has connected ethernet,Continue")
                x, y = self.get_button_coordinates("Continue")
                logging.info(f">Continue< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
                time.sleep(20)
            if "Select your Wi-Fi network" in ui_info:
                logging.info("Choose an other wifi to connect")
                for _ in range(60):
                    os.system(f"adb -s {device} shell \"input keyevent 20\"")
                for _ in range(5):
                    wifi_ui_info = self.get_ui_info(device)
                    time.sleep(3)
                    if "Other network" in wifi_ui_info:
                        x, y = self.get_button_coordinates("Other network…")
                        logging.info(f">Other network…< coordinates:{x} {y}")
                        os.system(f"adb -s {device} shell input tap {x} {y}")
                        time.sleep(2)
                    if "Enter name of Wi-Fi" in wifi_ui_info:
                        os.system(f"adb -s {device} shell 'input text {wifi_ssid};input keyevent 66'")
                        time.sleep(5)
                    if "Type of security" in wifi_ui_info:
                        x, y = self.get_button_coordinates("WPA/WPA2-Personal")
                        logging.info(f">WPA/WPA2-Personal< coordinates:{x} {y}")
                        os.system(f"adb -s {device} shell input tap {x} {y}")
                        time.sleep(5)
                    if "Enter password for" in wifi_ui_info:
                        os.system(f"adb -s {device} shell 'input text {wifi_pwd};input keyevent 66'")
                        time.sleep(60)
                        wifi_status = subprocess.getoutput(f"adb -s {device} shell cmd wifi status")
                        if f"Wifi is connected to \"{wifi_ssid}\"" in wifi_status:
                            logging.info("Wifi set up success")
                            break
                        else:
                            logging.info("Wifi set up failed")
                            os.system(f"adb -s {device} shell 'cmd wifi connect-network {wifi_ssid} wpa2 {wifi_pwd}'")
                            os.system(f"adb -s {device} shell \"input keyevent 4;input keyevent 4;\"")
                            time.sleep(5)
            if "Make the most of your TV" in ui_info:
                logging.info("Sign in with google account")
                x, y = self.get_button_coordinates("Sign In")
                logging.info(f">Sign In< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
                time.sleep(10)
                os.system(f"adb -s {device} shell 'input text {account_username};input keyevent 66'")
                time.sleep(10)
                os.system(f"adb -s {device} shell 'input text {account_pwd};input keyevent 66'")
                time.sleep(30)
            if "Sign in - Google Accounts" in ui_info:
                logging.info("Sign in with google account")
                os.system(f"adb -s {device} shell 'input text {account_username};input keyevent 66'")
                time.sleep(10)
                os.system(f"adb -s {device} shell 'input text {account_pwd};input keyevent 66'")
                time.sleep(30)
            if "Terms of Service" in ui_info:
                if "text=\"View more\"" in ui_info:
                    x, y = self.get_button_coordinates("View more")
                    logging.info(f">Terms of Service: View more< coordinates:{x} {y}")
                    os.system(f"adb -s {device} shell input tap {x} {y}")
                else:
                    x, y = self.get_button_coordinates("Accept")
                    logging.info(f">Terms of Service: Accept< coordinates:{x} {y}")
                    os.system(f"adb -s {device} shell input tap {x} {y}")
            if "Stay in the know" in ui_info:
                x, y = self.get_button_coordinates("No thanks")
                logging.info(f">Stay in the know :No thanks< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
                time.sleep(5)
            if "Did you know?" in ui_info:
                x, y = self.get_button_coordinates("Got it")
                logging.info(f">Did you know?: Got it< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
                time.sleep(5)
            if "Get personal results" in ui_info:
                x, y = self.get_button_coordinates("Turn on")
                logging.info(f">Get personal results: Turn on< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
                time.sleep(5)
            if "Google Services" in ui_info:
                x, y = self.get_button_coordinates("Accept")
                logging.info(f">Google Services: Accept< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
                time.sleep(5)
            if "Get better voice control of your TV" in ui_info:
                x, y = self.get_button_coordinates("Continue")
                logging.info(f">Get better voice control of your TV: Continue< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
                time.sleep(5)
            if "text=\"Google Assistant\"" in ui_info:
                x, y = self.get_button_coordinates("Continue")
                logging.info(f">Google Assistant: Continue< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
                time.sleep(5)
            if "Search across all your TV apps" in ui_info:
                x, y = self.get_button_coordinates("Allow")
                logging.info(f">Search across all your TV apps: Allow< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
                time.sleep(5)
            if "Activate Voice Match" in ui_info:
                x, y = self.get_button_coordinates("I agree")
                logging.info(f">Activate Voice Match: I agree< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
                time.sleep(5)
            if "Get the most out of your Google Assistant" in ui_info:
                x, y = self.get_button_coordinates("Yes")
                logging.info(f">Get the most out of your Google Assistant: Yes< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
                time.sleep(5)
            if "Install additional apps" in ui_info:
                x, y = self.get_button_coordinates("Continue")
                logging.info(f">Install additional apps: Continue< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
                time.sleep(5)
            if "You're signed in with" in ui_info:
                x, y = self.get_button_coordinates("Continue")
                logging.info(f">You're signed in with: Continue< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
                time.sleep(5)
            if "Get the full Assistant experience" in ui_info:
                x, y = self.get_button_coordinates("Turn on")
                logging.info(f">Get the full Assistant experience: Turn on< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
                time.sleep(5)
            if "Choose your subscriptions" in ui_info:
                x, y = self.get_button_coordinates("Confirm")
                logging.info(f">Choose your subscriptions: Confirm< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
                time.sleep(30)
                timeout = 600
                counter = 0
                while counter < timeout:
                    installing = self.get_ui_info(device)
                    if "Your Google TV experience is ready" in installing:
                        logging.info("Apps installation completed")
                        break
                    # logging.info("Installing apps, wait>>>>>>>>>>>")
                    time.sleep(10)
                    counter += 10
                    # logging.info(f"Has checked for {counter} seconds")
            if "Your Google TV experience is ready" in ui_info:
                x, y = self.get_button_coordinates("Start exploring")
                logging.info(f">Your Google TV experience is ready: Start exploring< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
                time.sleep(10)
                window_info = subprocess.getoutput(f"adb -s {device} shell {self.GET_CURRENT_WINDOW}")
                if "home.HomeActivity" in window_info or "home.VanillaModeHomeActivity" in window_info:
                    logging.info("Launch screen set up success")
                    break
                else:
                    logging.info("Launch screen set up success not")
                    os.system(f"adb -s {device} shell \"input keyevent 4;input keyevent 4;\"")

        logging.info("Set up device Stay awake")
        os.system(f"adb -s {device} shell \"{self.STAY_AWAKE}\"")
        if self.certification == "tvts" or self.certification == "gts":
            os.system(f"adb -s {device} shell {self.CLOSE_USB_VERIFY}")
        time.sleep(5)
        if loop == 0:
            self.forget_bluetooth(device)
        if self.certification == "cts":  # CTS need open location
            os.system(f"adb -s {device} shell {self.CLOSE_USB_VERIFY}")
            os.system(f"adb -s {device} shell {self.OPEN_LOCATION}")
            time.sleep(5)
            location_alert = self.get_ui_info(device)
            if "Turn on location" in location_alert:
                x, y = self.get_button_coordinates("Agree")
                os.system(f"adb -s {device} shell input tap {x} {y}")

    def login_netflix(self, device):
        ACCOUNT = self.config_certification["netflix"]["account"]
        PASSWORD = self.config_certification["netflix"]["password"]
        logging.info("Start to login Netflix")
        os.system(f"adb -s {device} shell monkey -p {self.NETFLIX_PACKAGE} 1")
        time.sleep(30)
        os.system(f"adb -s {device} shell \"input keyevent 21;input keyevent 23\"")
        time.sleep(5)
        os.system(f"adb -s {device} shell \"input keyevent 22;input keyevent 23\"")
        time.sleep(2)
        os.system(f"adb -s {device} shell input text {ACCOUNT}")
        time.sleep(3)
        os.system(f"adb -s {device} shell \"input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 23\"")
        time.sleep(3)
        os.system(f"adb -s {device} shell input text {PASSWORD}")
        time.sleep(3)
        os.system(f"adb -s {device} shell \"input keyevent 20;input keyevent 20;input keyevent 23\"")
        time.sleep(30)
        os.system(f"adb -s {device} shell input keyevent 23")
        time.sleep(5)
        logging.info("Stop Netflix")
        os.system(f"adb -s {device} shell am force-stop {self.NETFLIX_PACKAGE}")

    def forget_bluetooth(self, device):
        if self.certification == "vts" or self.certification == "sts":
            return
        logging.info("Start to forgot paired Bluetooth remote control")
        for i in range(3):
            os.system(f"adb -s {device} shell {self.OPEN_SETTINGS}")
            time.sleep(3)
            for _ in range(15):
                os.system(f"adb -s {device} shell input keyevent 20")
            time.sleep(2)
            os.system(f"adb -s {device} shell input keyevent 19")
            time.sleep(1)
            os.system(f"adb -s {device} shell input keyevent 23")
            ui_info = self.get_ui_info(device)
            if "B12" in ui_info:
                os.system(f"adb -s {device} shell \"input keyevent 20;input keyevent 20;input keyevent 20;\"")
                time.sleep(2)
                os.system(f"adb -s {device} shell input keyevent 23")
                time.sleep(2)
                os.system(f"adb -s {device} shell \"input keyevent 20;input keyevent 20;input keyevent 20;input "
                          f"keyevent 20\"")
                time.sleep(2)
                os.system(f"adb -s {device} shell input keyevent 23")
                time.sleep(2)
                os.system(f"adb -s {device} shell \"input keyevent 19;input keyevent 19;input keyevent 19;\"")
                time.sleep(2)
                os.system(f"adb -s {device} shell input keyevent 23")
                if "Connected" in self.get_ui_info(device):
                    logging.info("Forget Bluetooth remote Failed,retry")
                    os.system(f"adb -s {device} shell \"input keyevent 4;input keyevent 4\"")
                else:
                    logging.info("Forget Bluetooth remote successfully,return home")
                    os.system(f"adb -s {device} shell \"input keyevent 4;input keyevent 4;input keyevent 4\"")
                    os.system(f"adb -s {device} shell input keyevent 3")
                    break
            else:
                logging.info("This devices has not paired B12 remote, return home")
                os.system(f"adb -s {device} shell input keyevent 4")
                os.system(f"adb -s {device} shell input keyevent 4")
                break

    def update_apps(self, device):
        # open Google Play Store
        os.system(f"adb -s {device} shell {self.GOOGLE_PAY}")
        time.sleep(10)
        os.system(f"adb -s {device} shell \"input keyevent 19\"")
        time.sleep(3)
        os.system(f"adb -s {device} shell \"input keyevent 21\"")
        time.sleep(3)
        os.system(f"adb -s {device} shell \"input keyevent 20\"")
        time.sleep(3)
        os.system(f"adb -s {device} shell \"input keyevent 22\"")
        time.sleep(3)
        # Search Google TV Movies
        os.system(f"adb -s {device} shell \"input text 'Google TV'\"")
        os.system(f"adb -s {device} shell input keyevent 66")
        time.sleep(3)
        search_result = self.get_ui_info(device)
        if 'text="About these results"' in search_result:
            if "content-desc=\"Google TV\" checkable" in search_result:
                x, y = self.get_button_coordinates("Google TV", "content-desc")
                logging.info("Google TV has found! Check enable or disable")
                os.system(f"adb -s {device} shell input tap {x} {y}")
                time.sleep(3)
                google_tv_info = self.get_ui_info(device)
                if "Enable" in google_tv_info:
                    logging.info("Google TV is disabled,enter \"Enable\" to enable it!")
                    x, y = self.get_button_coordinates("Enable")
                    logging.info(f">Google TV Movies: Enable< coordinates:{x} {y}")
                    os.system(f"adb -s {device} shell input tap {x} {y}")
                    time.sleep(3)
        else:
            if "Enable" in search_result:
                logging.info("Google TV is disabled,enter \"Enable\" to enable it!")
                x, y = self.get_button_coordinates("Enable")
                logging.info(f">Google TV Movies: Enable< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
                time.sleep(3)
        # Go to update all apps
        for _ in range(5):
            os.system(f"adb -s {device} shell \"input keyevent 19\"")
        time.sleep(2)
        os.system(f"adb -s {device} shell \"input keyevent 22;input keyevent 22;input keyevent 22;input keyevent "
                  f"22;input keyevent 23\"")
        time.sleep(2)
        os.system(f"adb -s {device} shell \"input keyevent 23\"")
        time.sleep(2)
        os.system(f"adb -s {device} shell \"input keyevent 23\"")
        time.sleep(5)
        ui_info = self.get_ui_info(device)
        if "Update all" in ui_info:
            os.system(f"adb -s {device} shell \"input keyevent 23\"")
            time_out = 1200
            counter = 0
            while counter < time_out:
                ui_text = self.get_ui_info(device)
                if "No updates available" in ui_text:
                    logging.info("Update apps finished, return home")
                    time.sleep(2)
                    os.system(
                        f"adb -s {device} shell \"input keyevent 4;input keyevent 4;input keyevent 4;input keyevent "
                        f"4;input keyevent 4;input keyevent 3\"")
                    break
                if "Update all" in ui_text:
                    os.system(f"adb -s {device} shell \"input keyevent 23\"")
                time.sleep(20)
                counter += 20
                logging.info(f"Updating apps, wait {counter} seconds>>>>>>>>>>>")
        else:
            logging.info("May open update failed!")
            os.system(f"adb -s {device} shell \"input keyevent 4\"")

    def factory_reset(self, device, powerRelay):
        MAX_COUNT = 3
        COUNT = 0
        while COUNT < MAX_COUNT:
            # Power off,cold start
            os.system(f"{self.workspace}/AutoTestRes/bin/powerRelay {powerRelay} all off")
            time.sleep(5)
            os.system(f"{self.workspace}/AutoTestRes/bin/powerRelay {powerRelay} all on")
            time.sleep(120)
            # Open settings
            os.system(f"adb -s {device} shell {self.OPEN_SETTINGS}")
            time.sleep(5)
            for _ in range(15):
                os.system(f"adb -s {device} shell \"input keyevent 20\"")
            time.sleep(3)
            if self.android_type == "Android_U":
                os.system(f"adb -s {device} shell \"input keyevent 19;input keyevent 19;input keyevent 19;input "
                          f"keyevent 23\"")
                time.sleep(3)
                os.system(f"adb -s {device} shell \"input keyevent 23\"")
                time.sleep(3)
            else:
                os.system(f"adb -s {device} shell \"input keyevent 19;input keyevent 19;input keyevent 23\"")
                time.sleep(3)
                os.system(f"adb -s {device} shell \"input keyevent 19;input keyevent 19;input keyevent 20;input "
                          f"keyevent 23\"")
                time.sleep(3)
            os.system(f"adb -s {device} shell \"input keyevent 19;input keyevent 20;input keyevent 20;input "
                      f"keyevent 23\"")
            time.sleep(3)
            os.system(f"adb -s {device} shell \"input keyevent 20;input keyevent 20;input keyevent 20;input keyevent "
                      f"23\"")
            time.sleep(3)
            os.system(f"adb -s {device} shell \"input keyevent 20;input keyevent 20;input keyevent 20;input keyevent "
                      f"23\"")
            time.sleep(180)
            all_devices = subprocess.getoutput("adb devices")
            if device in all_devices:
                if "id/remote_pairing_video" in self.get_ui_info(device):
                    logging.info(f"{device} is now in remote pairing mode, Factory reset successfully!")
                    break
                else:
                    COUNT += 1
            else:
                logging.info(f"{device} may power on failed , Use powerRelay to start device")
                os.system(f"{self.workspace}/AutoTestRes/bin/powerRelay {powerRelay} all off")
                time.sleep(5)
                os.system(f"{self.workspace}/AutoTestRes/bin/powerRelay {powerRelay} all on")
                time.sleep(180)
                if "id/remote_pairing_video" in self.get_ui_info(device):
                    logging.info(f"{device} is now in remote pairing mode, Factory reset successfully!")
                    break
                else:
                    COUNT += 1

    def factory_reset_thread(self):
        devices_list = self.certification_devices
        threads = []
        for device_info in devices_list:
            thread = threading.Thread(target=self.factory_reset,
                                      args=(device_info["device_id"], device_info["powerRelay"],))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()

    def update_apps_thread(self, devices=None):
        if devices:
            devices_list = devices
        else:
            devices_list = self.devices_list
        threads = []
        for device in devices_list:
            thread = threading.Thread(target=self.update_apps, args=(device,))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()

    def login_netflix_thread(self):
        devices_list = self.devices_list
        threads = []
        for device in devices_list:
            thread = threading.Thread(target=self.login_netflix, args=(device,))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()

# if __name__ == '__main__':
#     XTS = Certification("nts")
#     # XTS.pass_oobe(device="oppen000650")
#     # XTS.update_apps(device="oppen000650")
#     # XTS.factory_reset(device="oppen000650", powerRelay="/dev/powerRelay")
#     XTS.factory_reset_thread()
