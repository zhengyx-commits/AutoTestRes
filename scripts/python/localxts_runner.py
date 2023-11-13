import argparse
import contextlib
import logging
import os
import random
import shutil
import subprocess
import sys
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from certification_test.Certification import Certification


class CertificationRunner(object):

    def __init__(self, args):
        self.file_handler = None
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.formatter = logging.Formatter('%(asctime)s - %(message)s')
        self.console_handler = logging.StreamHandler(sys.stdout)
        self.console_handler.setLevel(logging.INFO)
        self.console_handler.setFormatter(self.formatter)
        self.logger.addHandler(self.console_handler)
        self.args = args
        if self.args.cts_test:
            self.test_type = "cts"
        if self.args.gts_test:
            self.test_type = "gts"
        if self.args.tvts_test:
            self.test_type = "tvts"
        if self.args.vts_test:
            self.test_type = "vts"
        if self.args.sts_test:
            self.test_type = "sts"
        self.XTS = Certification(self.test_type)
        if os.environ.get("WORKSPACE"):
            self.is_jenkins = True
            logging.info(f"The variable WORKSPACE was obtained,Is jenkins :{self.is_jenkins}")
        else:
            self.is_jenkins = False
            logging.info(f"The variable WORKSPACE was not obtained,Is jenkins :{self.is_jenkins}")
        self.time_now = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        self.log_dir = Path(self.XTS.workspace) / 'log'
        self.log_dir.mkdir(exist_ok=True)
        self.logfile = str(self.log_dir / f"{self.test_type}_{self.time_now}_log.txt")
        # self.autobuild_type = os.environ.get("TEST_BUILD_TYPE", "GTV")
        # self.test_series = os.environ.get("TEST_SERIES", "Android_U")
        self.loops = self.XTS.config_certification["retry_count"][self.test_type]
        self.R2_suite = os.environ.get("TEST_SUITE_R2")
        logging.info(f"{self.test_type.upper()} test round :{len(self.loops)}")

    @contextlib.contextmanager
    def configure_logger(self):
        self.file_handler = RotatingFileHandler(self.logfile, maxBytes=100 * 1024 * 1024, backupCount=10)
        self.file_handler.setLevel(logging.INFO)
        self.file_handler.setFormatter(self.formatter)
        self.logger.addHandler(self.file_handler)
        try:
            yield
        finally:
            self.file_handler.close()
            self.logger.removeHandler(self.file_handler)

    def boot_wizard(self):
        self.XTS.google_tv_list = []
        self.XTS.basic_tv_list = []
        for i in range(3):
            if i < 1:
                self.XTS.pair_bluetooth_remote()
            else:
                if self.XTS.certification == "cts":
                    if len(set(self.XTS.basic_tv_list)) < 3:
                        self.XTS.pair_bluetooth_remote(retry=True, basic_mode=True)
                    else:
                        self.XTS.pair_bluetooth_remote(retry=True)
                else:
                    self.XTS.pair_bluetooth_remote(retry=True)
            if self.XTS.check_oobe():
                break
        google_tv = list(set(self.XTS.google_tv_list))
        basic_tv = list(set(self.XTS.basic_tv_list))
        logging.info("Google tv list:{}".format(google_tv))
        logging.info("Basic tv list:{}".format(basic_tv))
        return google_tv, basic_tv

    def retry_with_single_module(self, basic_tv_list, google_tv_list):
        module_count = 0
        if self.XTS.change_suite_time:
            min_fail_dict = self.XTS.get_min_fail_result(timestamp=self.XTS.change_suite_time)
        else:
            min_fail_dict = self.XTS.get_min_fail_result()
        if not min_fail_dict:
            logging.info("Min fails result can't find; can't retry with -m")
            return
        all_failed_modules = self.XTS.get_all_failed_modules(directory=min_fail_dict["result_dir"])
        logging.info(f"All_failed_modules:{all_failed_modules}")
        for module, fails in all_failed_modules.items():
            if "DevicePolicy" in module and basic_tv_list:
                for _ in range(2):
                    execution_list = basic_tv_list[:1] if fails < 50 else basic_tv_list
                    session_id = min_fail_dict["session"] if module_count < 1 else None
                    retry_cmd = self.XTS.one_module_retry_command(module=module,
                                                                  devices=execution_list,
                                                                  session=session_id)
                    self.XTS.run_test(retry_cmd)
                    module_count += 1
            elif "CtsCamera" in module:
                single = [self.XTS.config_certification["devices"]["cts_single"]["device_id"]]
                session_id = min_fail_dict["session"] if module_count < 1 else None
                retry_cmd = self.XTS.one_module_retry_command(module=module,
                                                              devices=single,
                                                              session=session_id)
                self.XTS.run_test(retry_cmd)
                module_count += 1
            else:
                execution_list = google_tv_list[:1] if fails < 50 else google_tv_list
                session_id = min_fail_dict["session"] if module_count < 1 else None
                retry_cmd = self.XTS.one_module_retry_command(module=module,
                                                              devices=execution_list,
                                                              session=session_id)
                self.XTS.run_test(retry_cmd)
                module_count += 1

    def change_test_suite(self, suite_path, results):
        if suite_path:
            logging.info("The R2 test suite is not configured,Modify the test suite path")
            time.sleep(5)
            r1_results = self.XTS.suite_folder + f"/results/{results}"
            time_now = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
            r2_results = os.path.join(suite_path, f"results/{time_now}")
            try:
                shutil.copytree(r1_results, r2_results)
            except Exception as e:
                logging.info("Failed to copy:{}".format(e))
            else:
                self.XTS.suite_folder = suite_path
                self.XTS.suite_bin = suite_path + f"/tools/{self.XTS.certification}-tradefed"
                logging.info(f"R2 test suite folder path:{self.XTS.suite_folder}")
                logging.info(f"R2 test suite bin path:{self.XTS.suite_bin}")
                return True
        else:
            logging.info("The R2 test suite is not configured, continue to use the R1 test suite retry")
            return False

    def run_all(self, device_list=None):
        # self.configure_logger()
        with self.configure_logger():
            if device_list:
                self.XTS.devices_list = device_list
            if self.is_jenkins:
                self.XTS.copy_result_xml_file(filename="old")
            first_retry = self.loops["first_loop"]
            logging.info(f"The first loop retry count :{first_retry}")
            first_retry_count = 0
            logging.info(f"==========Start the first round of {self.XTS.certification.upper()} test==========")
            # pass oobe
            if self.XTS.board == "boreal":
                self.XTS.setting_connect_network_thread()
            else:
                self.XTS.wifi_set_up_thread()
            if self.XTS.certification != "vts":  # vts no need to pass oobe
                if self.XTS.certification == "sts":  # sts no need to pair bluetooth remote
                    self.XTS.pass_oobe(device=self.XTS.devices_list[0])
                else:
                    if self.XTS.board == "boreal" and self.XTS.certification == "cts":
                        pass
                    else:
                        google_tv_list, basic_tv_list = self.boot_wizard()
                        self.XTS.update_apps_thread(google_tv_list)
                    # if self.XTS.certification == "tvts":
                    #     self.XTS.login_netflix_thread()
            self.XTS.run_test(self.XTS.create_run_command())
            logging.info('-' * 40)
            logging.info('First loop done')
            logging.info(time.strftime("%Y-%m-%d-%H_%M_%S", time.localtime()))
            while first_retry_count < first_retry:
                if self.XTS.certification == "cts" and "Android_U" in self.XTS.workspace:
                    use_filter = False if self.XTS.board == "boreal" else True
                    if first_retry_count < 2:
                        retry_command = self.XTS.create_retry_command(filter=use_filter)
                    else:
                        if len(basic_tv_list) > 0:
                            retry_command = self.XTS.create_retry_command(devices=basic_tv_list)
                        else:
                            retry_command = self.XTS.create_retry_command(filter=use_filter)
                elif self.XTS.certification == "tvts" and first_retry_count > 2:
                    retry_command = self.XTS.create_retry_command(single=True)
                else:
                    retry_command = self.XTS.create_retry_command()
                self.XTS.run_test(retry_command)
                if self.XTS.last_result()[1] == 0:
                    break
                first_retry_count += 1
            if self.XTS.certification == "sts":
                if self.XTS.last_result()[1] != 0:
                    self.XTS.factory_reset_thread()
                    retry_command = self.XTS.create_retry_command()
                    self.XTS.run_test(retry_command)
            logging.info('First test round done')
            if len(self.loops) >= 2:
                second_retry = self.loops["second_loop"]
                logging.info(f"The second loop retry count :{second_retry}")
                second_retry_count = 0
                logging.info(f"==========Start the second round of {self.XTS.certification.upper()} test==========")
                if self.XTS.certification == "gts" or self.XTS.certification == "cts":
                    self.XTS.factory_reset_thread()
                    if self.XTS.certification == "cts":
                        self.XTS.devices_list = self.XTS.check_available_devices()  # update the list of devices
                    if self.XTS.board == "boreal":
                        self.XTS.setting_connect_network_thread()
                    else:
                        self.XTS.wifi_set_up_thread()  # Connect to Wi-Fi before pass OOBE
                    google_tv_list, basic_tv_list = self.boot_wizard()
                    self.XTS.update_apps_thread(google_tv_list)
                second_retry_time = time.time()
                min_fail_dict = self.XTS.get_min_fail_result()
                if self.change_test_suite(self.R2_suite, min_fail_dict["result_dir"]):
                    self.XTS.change_suite_time = time.time()
                    min_fail_dict = self.XTS.get_min_fail_result(timestamp=second_retry_time)
                while second_retry_count < second_retry:
                    if self.XTS.certification == "cts" and "Android_U" in self.XTS.workspace:
                        if second_retry_count < 2:
                            self.XTS.run_test(self.XTS.create_retry_command(filter=True))
                        if second_retry_count == 2:
                            if len(basic_tv_list) == 0:
                                self.XTS.run_test(self.XTS.create_retry_command(single=True, not_executed=True))
                                break
                            else:
                                self.XTS.run_test(self.XTS.create_retry_command(devices=basic_tv_list))
                        if second_retry_count == 3 and len(basic_tv_list) > 0:
                            self.retry_with_single_module(basic_tv_list, google_tv_list)
                        if second_retry_count > 3:
                            self.XTS.run_test(self.XTS.create_retry_command(single=True, not_executed=True))
                    else:
                        if second_retry_count < 1:
                            self.XTS.run_test(self.XTS.create_retry_command(session_id=min_fail_dict["session"]))
                        else:
                            self.XTS.run_test(self.XTS.create_retry_command())
                    if self.XTS.last_result()[1] == 0:
                        break
                    second_retry_count += 1
                logging.info('Second test round done')
                if len(self.loops) == 3:
                    third_retry = self.loops["third_loop"]
                    logging.info(f"The third loop retry count :{third_retry}")
                    third_retry_count = 0
                    logging.info(f"==========Start the third round of {self.XTS.certification.upper()} test==========")
                    if self.XTS.last_result()[1] <= 100:
                        single_device = self.XTS.config_certification["devices"]["cts_single"]
                        self.XTS.factory_reset(single_device["device_id"], single_device["powerRelay"])
                        self.XTS.pair_bluetooth_remote(single=True)
                        while third_retry_count < third_retry:
                            self.XTS.run_test(self.XTS.create_retry_command(single=True))
                            if self.XTS.last_result()[1] == 0:
                                break
                            third_retry_count += 1
                    else:
                        self.XTS.factory_reset_thread()
                        self.XTS.pair_bluetooth_remote()
                        while third_retry_count < third_retry:
                            self.XTS.run_test(self.XTS.create_retry_command())
                            if self.XTS.last_result()[1] == 0:
                                break
                            third_retry_count += 1
                    logging.info('Third test round done')
            if self.is_jenkins:
                self.XTS.generate_report()
                self.XTS.copy_result_xml_file(filename="new", target=self.XTS.min_fails_results_dir)

    def list_result(self):
        result_info = self.XTS.execute_suite_command("l r")
        print(result_info)

    def run_retry(self, session_num=None, device_list=None, loop=1):
        with self.configure_logger():
            if device_list:
                self.XTS.devices_list = device_list
            if self.R2_suite:
                self.XTS.suite_folder = self.R2_suite
                self.XTS.suite_bin = self.R2_suite + f"/tools/{self.XTS.certification}-tradefed"
            count = 0
            while count < int(loop):
                if count == 0:
                    self.XTS.run_test(self.XTS.create_retry_command(session_id=session_num))
                else:
                    self.XTS.run_test(self.XTS.create_retry_command())
                count += 1
            if self.is_jenkins:
                self.XTS.generate_report(retry=True)

    def start_bin(self):
        process = self.XTS.start_suite_bin()
        while True:
            if process.poll() is None:
                continue
            else:
                logging.info("Test suite has exited")
                break

    def only_pass_oobe(self, device_list=None, oobe_type=1):
        with self.configure_logger():
            if device_list:
                self.XTS.devices_list = device_list
            self.XTS.wifi_set_up_thread(self.XTS.devices_list)
            if oobe_type != 1:
                for device in device_list:
                    self.XTS.pass_oobe(device)
            else:
                self.boot_wizard()


def get_args():
    parser = argparse.ArgumentParser(description="Parsing the local certification test autotest runner args")
    first_arg = parser.add_mutually_exclusive_group()
    first_arg.add_argument("-c", "--cts",
                           action="store_true",
                           dest="cts_test",
                           help="Execute CTS test suite")
    first_arg.add_argument("-g", "--gts",
                           action="store_true",
                           dest="gts_test",
                           help="Execute GTS test suite")
    first_arg.add_argument("-v", "--vts",
                           action="store_true",
                           dest="vts_test",
                           help="Execute VTS test suite")
    first_arg.add_argument("-t", "--tvts",
                           action="store_true",
                           dest="tvts_test",
                           help="Execute TVTS test suite")
    first_arg.add_argument("-s", "--sts",
                           action="store_true",
                           dest="sts_test",
                           help="Execute STS test suite")
    parser.add_argument("-r", "--retry",
                        dest="retry",
                        nargs='?',
                        const='no_value',
                        help="Set the retry session id,if none,retry last session")
    parser.add_argument("-l", "--loop",
                        dest="loop",
                        type=int,
                        default=1,
                        help="Set the retry count,if none,retry one time")
    parser.add_argument("-device",
                        nargs='*',
                        dest="devices",
                        help="Set the device list. If there are multiple devices, separate them by Spaces")
    parser.add_argument("-result",
                        action="store_true",
                        dest="result",
                        help="List test results")
    parser.add_argument("-oobe",
                        dest="oobe",
                        type=int,
                        default=1,
                        help="Default value 1,Pair bluetooth remote and pass oobe;if value is not 1, Only pass oobe")
    parser.add_argument("-all",
                        action="store_true",
                        dest="all_cases",
                        help="Execute all test cases and retry policies of certification")
    args = parser.parse_args()
    if not any([args.cts_test, args.gts_test, args.vts_test, args.tvts_test, args.sts_test]):
        parser.error('No test suite specified, add -c/--cts, -g/--gts, -v/--vts, -t/--tvts, or -s/--sts')
    return args


if __name__ == '__main__':
    args = get_args()
    runner = CertificationRunner(args)
    if any([args.cts_test, args.gts_test, args.vts_test, args.tvts_test, args.sts_test]):
        if args.all_cases:
            logging.info(f"List of devices from parameters:{args.devices}")
            runner.run_all(device_list=args.devices)
            exit(0)
        elif args.result:
            runner.list_result()
            exit(0)
        elif args.retry:
            session = None if args.retry == 'no_value' else int(args.retry)
            devices = args.devices
            runner.run_retry(session_num=session, device_list=devices, loop=args.loop)
            exit(0)
        elif args.oobe:
            runner.only_pass_oobe(device_list=args.devices, oobe_type=args.oobe)
            exit(0)
        else:
            runner.start_bin()
            exit(0)
