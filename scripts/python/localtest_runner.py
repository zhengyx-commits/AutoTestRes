#!/usr/bin/env python
# Copyright 2020 Amlogic.com, Inc. or its affiliates. All rights reserved.
#
# AMLOGIC PROPRIETARY/CONFIDENTIAL
#
# You may not use this file except in compliance with the terms and conditions
# set forth in the accompanying LICENSE.TXT file.
#
# THESE MATERIALS ARE PROVIDED ON AN "AS IS" BASIS. AMLOGIC SPECIFICALLY
# DISCLAIMS, WITH RESPECT TO THESE MATERIALS, ALL WARRANTIES, EXPRESS,
# IMPLIED, OR STATUTORY, INCLUDING THE IMPLIED WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.
#
import platform
from __init__ import *
import glob
import os
import time
import fcntl
from lxml import etree as ET
from prettytable import PrettyTable
import re
import sys
import shlex
import subprocess
import logging
import argparse
from collections import defaultdict
from collections import OrderedDict
from tools.xtsAnalyer import Analyzer
from aatsbuildconfig import AATSBuildConfig
import datetime
from baseConfigParser import get_target_json_data

logging.basicConfig(level=logging.DEBUG)


class LocalTestRunner(object):
    _PRINT_WIDTH = 80

    def __init__(self, args):
        self.args = args
        self.build_config = AATSBuildConfig(args)
        self.module_name = None
        self.test_session = TestSession()
        self.valid_tests = {}
        self.module_bring_up_order = ["MEDIA", "PLAYBACK", "SYSTEM", "INPUT", "DRM", "WIFI", "NETWORK", "PICTURES",
                                      "IPTV"]
        self.retest_count = 0

    def print_section_log(self, log):
        header = f'[{self.module_name}] {log}'
        print(os.linesep, '*' * self._PRINT_WIDTH, os.linesep,
              '  {}  '.format(header).center(
                  self._PRINT_WIDTH, "*"), os.linesep,
              '*' * self._PRINT_WIDTH, os.linesep)

    @staticmethod
    def setup_test_environment():
        try:
            os.environ.pop("AATS_TESTER_SETUP_ERROR", "")
        except OSError:
            logging.exception("Exception while setting test environment")

    def teardown_device(self):
        """Restores configuration and device"""
        self.print_section_log("TEARDOWN ENVIRONMENT")
        # self.build_config.restore_header_files()
        # self.build_config.reset_endpoints()
        self.test_session.stop_testrun()

    def create_run_cmd(self, module_src_path, module_name, pytest_args=None):
        # Set HTML report file name
        html_result_path = None
        xml_result_path = None

        try:
            html_result_path = self.test_session.testrun.get_html()
            xml_result_path = self.test_session.testrun.get_xml()
        except OSError:
            logging.exception("Error while setting html file name")

        # Set run command
        module_exec_args = module_src_path
        if pytest_args:
            logging.info(f"Updating execution args: {module_exec_args}")
            module_exec_args = f"{module_exec_args} {pytest_args}"
        else:
            if module_name:
                pytest_args = self.build_config.aats_test_cases_full_config.get(
                    module_name, {}).get("pytest_args", "")
                if pytest_args:
                    logging.info(f"Updating execution args: {module_exec_args}")
                    module_exec_args = pytest_args
        pytest_run_cmd = f"{module_exec_args}"
        
        # If the user sets the "failure" flag in CLI
        if self.args.count:
            pytest_run_cmd += f" --count={self.args.count}"
        if self.args.markers:
            pytest_run_cmd += f" -k {' '.join(self.args.markers)}"
        if self.args.retry:
            pytest_run_cmd += f" --reruns {self.args.retry}"
        if self.args.stop_after_first_failure:
            pytest_run_cmd += " --exitfirst"
        if self.args.timeout:
            pytest_run_cmd += f" --timeout={self.args.timeout}"
        if self.args.piplineType:
            pytest_run_cmd += f" --piplineType={self.args.piplineType}"
        if self.args.multiInstance:
            pytest_run_cmd += f" --multiInstance={self.args.multiInstance}"
        if self.args.project:
            pytest_run_cmd += f" --project={self.args.project}"
        if html_result_path:
            pytest_run_cmd += f" --html={html_result_path} --self-contained-html"
            pytest_run_cmd += f" --junitxml={xml_result_path}"
        if self.args.conn_type:
            pytest_run_cmd += f" --conn_type={self.args.conn_type}"
        # run_cmd = f"/home/amlogic/work/AATS/pycharm_test/AATS/.tox/py36/bin/pytest -v -s {pytest_run_cmd}"
        run_cmd = f"tox -c {curPath}  -- {pytest_run_cmd}"
        logging.debug(f"Test Run command: {run_cmd}")
        return run_cmd

    def sort_modules_by_phase(self, modules):
        """Uses ordered list of bring-up phases and testcase labels to
        order testcases. Modules without a group label will be added to
        one of the UNSPECIFIED groups. Testcase groups can have a number
        X like "_#X" associated with them to indicate they should be in
        a separate build for size reasons, but they belong to the same
        group and the number does not impact ordering"""
        if not modules:
            return None

        ordered_modules = OrderedDict()
        phase_map = OrderedDict()
        unspecified_module_map = dict()

        for phase in self.module_bring_up_order:
            phase_map[phase] = []
            if phase.endswith("UNSPECIFIED"):
                general_phase = phase.split("_")
                general_phase.pop()
                general_phase = "_".join(general_phase)
                unspecified_module_map[general_phase] = phase

        for module in modules:
            group = self.build_config.module_group_map.get(module, None)
            if group and group.split("#")[0] in phase_map:
                trimmed_group_name = group.split("#")[0]
                phase_map[trimmed_group_name].append(module)
            else:
                if group:
                    logging.warning(
                        "Module {} has unknown group {}".format(module, group))
                inserted = False
                for general_phase in unspecified_module_map:
                    if general_phase in module:
                        phase_map[unspecified_module_map[general_phase]].append(
                            module)
                        inserted = True
                        break
                if not inserted:
                    logging.error("Module {} has no known group!".format(
                        module))
                    phase_map["UNKNOWN"].append(module)

        for phase, module_list in phase_map.items():
            for module in module_list:
                ordered_modules[module] = modules[module]

        if len(ordered_modules) != len(modules):
            logging.error("Not all modules added!")
            return modules

        return ordered_modules

    def execute_all(self):
        """Executes the entire list of tests configured in testcases.json"""
        valid_modules = self.__get_valid_modules_for_case()
        if hasattr(self.test_session, 'fail_case') and self.test_session.fail_case:
            logging.info('Already have test fail')
            # self.test_session.testrun.idCounter = 0
            for k in list(valid_modules.keys()):
                if k not in self.test_session.fail_case:
                    del valid_modules[k]
        if self.retest_count > 1 and len(self.test_session.fail_case) == 0:
            logging.info("test cases all pass")
            for k in list(valid_modules.keys()):
                if k not in self.test_session.fail_case:
                    del valid_modules[k]
        # valid_modules = self.sort_modules_by_phase(valid_modules)
        # 将恢复出厂放在最后执行
        if 'AATS_IPTV_CMCC_FACTORY_RESET' in valid_modules:
            valid_modules['AATS_IPTV_CMCC_FACTORY_RESET'] = valid_modules.pop('AATS_IPTV_CMCC_FACTORY_RESET')
        if 'AATS_OTT_FUNC_FACTORY_RESET' in valid_modules:
            valid_modules['AATS_OTT_FUNC_FACTORY_RESET'] = valid_modules.pop('AATS_OTT_FUNC_FACTORY_RESET')
        if 'AATS_OTT_FUNC_UPGRADE_FASTBOOT' in valid_modules:
            valid_modules['AATS_OTT_FUNC_UPGRADE_FASTBOOT'] = valid_modules.pop('AATS_OTT_FUNC_UPGRADE_FASTBOOT')
        total_modules = len(valid_modules)
        logging.info(f"Testing {total_modules} modules:\n{valid_modules}")
        for i, (name, path) in enumerate(valid_modules.items(), start=1):
            logging.info(f"Executing {i} of {total_modules}: {name}")
            self.execute_single_test_module(name, path)

    def execute_single_test_module(self, module_name, module_path,
                                   pytest_args=None):
        """Executes a single test module."""
        # Sets up testing environment for the module before building.
        self.setup_test_environment()
        self.set_runner_config_for_module(module_name, module_path)

        # Executes the test module and tears down environment afterwards.
        self.check_failure_option_and_run_test(module_name,
                                               module_path,
                                               pytest_args)
        self.teardown_device()

    def set_runner_config_for_module(self, module_name, module_path):
        """Sets various variables for the given module."""
        logging.info(f"Module name: {module_name} [path: {module_path}]")
        self.module_name = module_name
        self.test_session.start_testrun(module_name)
        os.environ["AATS_TESTER_MODULE"] = self.module_name

    def check_failure_option_and_run_test(self, module_name, module_path,
                                          pytest_args=None):
        """If the user passed the "--stop-after-first-failure" CLI argument,
        after one test failure the entire test run will be stopped.
        Otherwise, run tests normally without considering results.
        """
        self.print_section_log("STARTING TEST EXECUTION")
        if self.args.stop_after_first_failure and \
                self._run_cmd(command=self.create_run_cmd(module_path,
                                                          module_name,
                                                          pytest_args),
                              fileout=self.test_session.testrun.get_testlog(),
                              suppress_output=False):
            self.print_section_log("FINISHED TEST EXECUTION")
            self.teardown_device()
            raise RuntimeError(
                "Encountered a test failure; stopping test execution.")

        elif self._run_cmd(command=self.create_run_cmd(module_path,
                                                       module_name,
                                                       pytest_args),
                           fileout=self.test_session.testrun.get_testlog(),
                           suppress_output=False):
            if 'VTS' in module_name:
                self.test_session.xts = 'VTS'
                logging.info('正在测试 VTS ')
            if 'CTS' in module_name:
                self.test_session.xts = 'CTS'
                logging.info('正在测试 CTS ')
            if 'GTS' in module_name:
                self.test_session.xts = 'GTS'
                logging.info('正在测试 GTS ')

            logging.info("Tox returned with a non-zero exit code")
        self.print_section_log("FINISHED TEST EXECUTION")

    def _run_cmd(self, command, fileout="", suppress_output=False):
        cmd = shlex.split(command)
        cmd_info = f"cmd: {cmd}"
        if fileout:
            cmd_info = f"{cmd_info}\nFor details, see: {fileout}"
        logging.info(cmd_info)
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        fcntl.fcntl(process.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        return_output = ""
        while True:
            output = ""
            try:
                output = process.stdout.readline().decode('utf-8', errors='ignore')
            except IOError:
                pass
            if output == '' and process.poll() is not None:
                break
            if output and output.strip():
                return_output += output
                if fileout:
                    with open(fileout, 'a') as f:
                        f.write(output)
                if not suppress_output:
                    print(output.strip())
        rc = process.poll()
        logging.debug(f"cmd-rc: {rc}")
        return rc, return_output

    def __get_valid_modules_for_product(self):
        """Only returns the modules that are applicable for a product config"""
        valid_modules = OrderedDict()
        entries = self.build_config.get_config_entries()
        for name in entries:
            path = self.build_config.get_entry_path(name)
            if os.path.exists(
                    os.path.join(os.path.dirname(
                        os.path.realpath(__file__)), path)):
                valid_modules[name] = os.path.join(os.path.dirname(
                    os.path.realpath(__file__)), path)
            else:
                logging.error(
                    f"Invalid path for module: {name}. Skipping this module.")
        return valid_modules

    def __get_valid_modules_for_case(self):
        """Only returns the modules that are applicable for a product config"""
        valid_modules = OrderedDict()
        entries = self.build_config.get_config_case_entries()
        for name in entries:
            path = self.build_config.get_entry_path(name)
            if os.path.exists(
                    os.path.join(os.path.dirname(
                        os.path.realpath(__file__)), path)):
                valid_modules[name] = os.path.join(os.path.dirname(
                    os.path.realpath(__file__)), path)
            else:
                logging.error(
                    f"Invalid path for module: {name}. Skipping this module.")
        return valid_modules

    def list_tests(self):
        print("\nTESTS LIST:")
        print("=============\n")
        table = PrettyTable()
        table.field_names = ['#', 'TestPath', 'TestDirectory']
        table.align = "l"
        idx = 0
        for path, subdirs, files in os.walk("tests"):
            for name in files:
                if name.startswith("test_"):
                    idx += 1
                    table.add_row([idx, os.path.join(path, name), path])
        print(table)

    def list_modules(self):
        print("\nMODULES LIST:")
        print("=============\n")
        table = PrettyTable()
        table.field_names = ['#', 'Module', 'Author', 'Args']
        table.align = "l"
        for idx, module_name in enumerate(
                self.__get_valid_modules_for_product(), start=1):
            pytest_args = self.build_config.aats_test_cases_full_config.get(
                module_name, {}).get("pytest_args", "")
            author = self.build_config.aats_test_cases_full_config.get(
                module_name, {}).get("author", "")
            table.add_row([idx, module_name, author, pytest_args])
        print(table)

    def handle_test_modules(self):
        """Handles test module execution by checking cli options and passing
        the module(s) to the proper execution function.
        """
        try:
            # Validates the given test modules and creates
            # a dict of {module_name: module_path}
            for module_name, module_path \
                    in runner.__get_valid_modules_for_product().items():
                if any(module == module_name for module in args.modules):
                    self.valid_tests[module_name] = module_path

            for name, path in self.valid_tests.items():
                runner.execute_single_test_module(name, path)

        except RuntimeError as ex:
            logging.info(ex)


class TestRun(object):
    idCounter = 0

    def __init__(self, session_directory, test_name, test_count=0):
        TestRun.idCounter += 1

        folder_name = '{:03d}_{}_{}'.format(TestRun.idCounter, test_name,
                                            str(test_count)) if test_count != 0 else '{:03d}-{}'.format(
            TestRun.idCounter, test_name)
        self.session_directory = os.path.join(session_directory, folder_name)
        self.test_name = test_name

        TestSession.create_directory(self.session_directory)

        class Logger(object):
            def __init__(self, logfile):
                self.terminal = sys.stdout
                self.logfile = logfile

            def write(self, message):
                self.terminal.write(message)
                with open(self.logfile, 'a') as f:
                    f.write(message)

            def flush(self):
                pass

        sys.stdout = Logger(os.path.join(
            self.session_directory, "full_run_log.txt"))

    def get_testlog(self):
        return os.path.join(self.session_directory, "test_execution_log.txt")

    def get_html(self):
        return os.path.join(self.session_directory, f"{self.test_name}.html")

    def get_xml(self):
        return os.path.join(self.session_directory, f"{self.test_name}.xml")


class TestSession(object):
    RESULT_DIRECTORY = "results"
    TEST_SESSION_PATH_ENV = "AATS_TESTER_SESSION_RESULT_PATH"

    def __init__(self):
        self.terminal = sys.stdout
        self.test_dict = {}
        self.results_dir = self.RESULT_DIRECTORY
        self.session_id = datetime.datetime.now().strftime(
            "%Y.%m.%d_%H.%M.%S")
        self.session_directory = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            self.RESULT_DIRECTORY,
            self.session_id)
        self.test_results = {}
        self.fail_case = []


    @property
    def xts(self):
        if not hasattr(self, '_xts'):
            return ''
        return self._xts

    @xts.setter
    def xts(self, name):

        self._xts = Analyzer(name)

    def start_testrun(self, test_name):
        # test_result = self.test_dict.get(test_name)
        # if test_result:
        #     logging.warning(f"Test already exists. test_name={test_name}")
        # else:
        test_result = TestRun(self.session_directory, test_name, runner.retest_count)
        self.test_dict[test_name] = test_result
        self.testrun = test_result
        os.environ[self.TEST_SESSION_PATH_ENV] = test_result.session_directory
        self.update_pipe_output()
        return test_result

    def stop_testrun(self):
        sys.stdout = self.terminal
        self.update_pipe_output()
        os.environ[self.TEST_SESSION_PATH_ENV] = self.session_directory

    def update_pipe_output(self):
        root = logging.getLogger()
        root.handlers = []
        handler = logging.StreamHandler(sys.stdout)
        root.addHandler(handler)

    @staticmethod
    def create_directory(directory):
        try:
            if not os.path.isdir(directory):
                logging.info(f"Creating results directory: {directory}")
                os.makedirs(directory)
        except OSError:
            logging.exception("Unable to create result folder")

    def generate_result_summary(self, retest_count=0):

        def rm_empty(pattern, info):
            result = re.findall(pattern, info, re.S)
            return result[0] if result else 0

        table = PrettyTable()
        table.field_names = ['Module', 'Author', 'Pass', 'Fail', 'Skipped',
                             'Error', 'Time', 'Report Link']
        table.align['Module'] = "l"
        table.align['Report Link'] = "l"
        count = defaultdict(int)
        # self.fail_case = []

        if not self.xts:
            for file in glob.glob(os.path.join(self.session_directory,
                                               "**{}/*.html".format(
                                                   str(retest_count) if retest_count != 0 else ''))):
                f = open(file, 'r')
                result_total_info = f.read()
                test_passes = rm_empty(r'<span class="passed">(\d+)\s+passed</span>', result_total_info)
                test_skipped = rm_empty(r'<span class="skipped">(\d+)\s+skipped</span>', result_total_info)
                test_failures = rm_empty(r'<span class="failed">(\d+)\s+failed</span>', result_total_info)
                test_errors = rm_empty(r'<span class="error">(\d+)\s+errors</span>', result_total_info)
                test_time = rm_empty(r'tests ran in (\d+\.?\d+) seconds. </p>', result_total_info)
                count["modules"] += 1
                count["passes"] += int(test_passes)
                count["failures"] += int(test_failures)
                count["skipped"] += int(test_skipped)
                count["errors"] += int(test_errors)
                count["time"] += float('%.2f' % float(test_time))

                casename = os.path.basename(file).replace(".html", "")

                test_result = {'casename': casename,
                               'pass': int(test_passes),
                               'fail': int(test_failures),
                               'skip': int(test_skipped),
                               'error': int(test_errors),
                               'time': float('%.2f' % float(test_time)),
                               'report_link': file.replace(".xml", ".html")
                                   .replace(os.path.dirname(os.path.realpath(__file__)) + "/",
                                            "")}
                logging.debug(f"test_result: {test_result}")

                if int(test_failures) != 0:
                    self.fail_case.append(casename)
                    test_result['status'] = 'fail'
                elif int(test_errors) != 0:
                    self.fail_case.append(casename)
                    test_result['status'] = 'error'
                else:
                    test_result['status'] = 'pass'
                if casename in test_result:
                    if self.test_results[casename]['status'] == 'fail' or self.test_results[casename]['status'] == 'error':
                        self.test_results[casename] = test_result
                else:
                    self.test_results[casename] = test_result
                logging.debug(f"self.test_results: {self.test_results}")

                module_col_index = table.field_names.index('Module')
                module_column = [row[module_col_index] for row in table._rows]
                # print("self.test_results", self.test_results)
                for casename, value in self.test_results.items():
                    if casename not in module_column:
                        table.add_row([casename,
                                       runner.build_config.aats_test_cases_full_config[casename]['author'],
                                       value["pass"],
                                       value["fail"],
                                       value["skip"],
                                       value["error"],
                                       value["time"],
                                       value["report_link"]])
                    else:
                        # Find the index of the row to update
                        row_index = None
                        for i, row in enumerate(table._rows):
                            if row[0] == casename:  # Assuming casename is in the first column
                                row_index = i
                                break

                        if row_index is not None:
                            # Create a new row with updated values
                            updated_row = [
                                casename,
                                runner.build_config.aats_test_cases_full_config[casename]['author'],
                                value["pass"],
                                value["fail"],
                                value["skip"],
                                value["error"],
                                value["time"],
                                value["report_link"]
                            ]

                            # Replace the existing row with the updated row
                            table._rows[row_index] = updated_row

                f.close()
                if 'JENKINS_HOME' in os.environ or 'JENKINS_UPL' in os.environ or 'BUILD_ID' in os.environ:
                    logging.info('start insert result to db')
                    target_json = get_target_json_data("target")
                    if target_json:
                        prj = target_json.get("prj")
                    # if 'dvb' in prj:
                        from tools.DB import DB
                        with DB() as db:
                            db.insert_data_row(
                                "TEST_RESULTS",
                                prj,
                                test_result['casename'],
                                runner.build_config.aats_test_cases_full_config[casename]['author'],
                                test_result["pass"],
                                test_result["fail"],
                                test_result["skip"],
                                test_result["error"],
                                test_result["time"],
                                test_result["report_link"]
                            )
                    else:
                        logging.info('please build db environment first')
                else:
                    logging.info('Manually execute without recording the database')
                    pass
        else:
            self.xts.analyze_xml()
            self.xts.print_result()
            xts_report = self.xts.pretty_table_data
            table.add_rows(xts_report)
            count = self.xts.count
        # print(table.rows)

        pass_sum = sum(int(row[2]) for row in table._rows)  # 计算 Pass 列的总和
        fail_sum = sum(int(row[3]) for row in table._rows)  # 计算 Fail 列的总和
        skip_sum = sum(int(row[4]) for row in table._rows)  # 计算 Skipped 列的总和
        error_sum = sum(int(row[5]) for row in table._rows)  # 计算 Error 列的总和
        time_sum = sum(float(row[6]) for row in table._rows)  # 计算 Time 列的总和

        total_summary = "[RESULT_SUMMARY] passes:{} failures:{} skipped:{} errors:{} " \
                        "time:{} modules:{}".format(pass_sum,
                                                    fail_sum,
                                                    skip_sum,
                                                    error_sum,
                                                    time_sum,
                                                    len(self.test_results))

        prj = ''
        target_json = get_target_json_data("target")
        if target_json:
            prj = target_json.get("prj")
        if prj == 'tv_amazon':
            result_summary = "{}\n{}".format(table.get_string(sortby="Report Link"), total_summary)
        else:
            result_summary = "{}\n{}".format(table.get_string(sortby="Author"), total_summary)
        print(result_summary)
        with open(os.path.join(self.session_directory, "result_summary{}.txt".format(
                '_retest_count_' + str(retest_count) if retest_count != 0 else '')), 'w') as f:
            f.write(result_summary)
        with open(os.path.join(self.session_directory, "result_summary{}.html".format(
                '_retest_count_' + str(retest_count) if retest_count != 0 else '')), 'w') as f:
            f.write(table.get_html_string(sortby="Author"))
        with open(os.path.join(self.session_directory, "result_summary{}.html".format(
                '_retest_count_' + str(retest_count) if retest_count != 0 else '')), 'r') as f:
            result = re.findall(r'<tr>(.*?)</tr', f.read(), re.S)[1:]
        # print("result", result)
        for i in result:
            count_list = re.findall(r'<td>(\d+)</td>', i, re.S)
            if int(count_list[1]) > 0 or int(count_list[3]) > 0:
                temp = re.findall(r'(<td>AATS.*?</td>)', i, re.S)[0]
                target = temp.replace('<td>', '<td bgcolor="red">')
                logging.info(f"sed -i 's:{temp}:{target}:' {self.session_directory}/result_summary.html")
                os.system(f"sed -i 's:{temp}:{target}:' {self.session_directory}/result_summary.html")


def get_args():
    parser = argparse.ArgumentParser(description="Parsing the local test runner args")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('-l', "--list-modules", "--list-module",
                       action='store_true',
                       dest='list_modules',
                       help='list available test modules')
    group.add_argument("--list-tests", "--list-test",
                       action='store_true',
                       dest='list_tests',
                       help='list available test files')
    group.add_argument("--verify-test-setup",
                       dest='verify_test_setup',
                       action='store_true',
                       help='verify test setup by executing a list of tests')
    group.add_argument("--verify-device-sanity",
                       dest='verify_device_sanity',
                       action='store_true',
                       help='verify device state by executing sanity tests')
    group.add_argument("--flash-stress", type=int, default=0,
                       dest='flash_stress',
                       help="The number of flashes to stress")
    group.add_argument('-m', "--modules",
                       nargs='+',
                       help='executes a single module')
    group.add_argument("--all",
                       action='store_true',
                       help='executes all the modules from testcases.json')
    parser.add_argument("--noflash",
                        action='store_true',
                        help='run tests without building and flashing the device')
    parser.add_argument("--nobuild",
                        action='store_true',
                        help='run tests with custom flash script that utilizes prebuilt builds')
    parser.add_argument("--onebuild",
                        action='store_true',
                        help='build and flash device once before running given tests in succession')
    parser.add_argument("--continue-on-setup-failure",
                        action='store_true',
                        dest='continue_on_failure',
                        help='continue test execution even if build/flash fails')
    parser.add_argument("--suppress-script-output",
                        action='store_true',
                        dest='suppress_script_output',
                        help='logs script to file')
    parser.add_argument("--stop-after-first-failure",
                        action='store_true',
                        dest='stop_after_first_failure',
                        help='stops test run after the first test failure')
    parser.add_argument('-t', "--timeout",
                        metavar="TIMEOUT",
                        dest="timeout",
                        type=int,
                        default=None,
                        help='per module timeout. if not provided, default \
                              timeout defined in pytest.ini will be used.')
    parser.add_argument("--generate-baseline",
                        action='store_true',
                        dest='generate_baseline',
                        help='generate test baseline from given test module(s)')
    parser.add_argument("--compare-baseline",
                        nargs='+',
                        dest='compare_baseline',
                        help='compare test results or existing baseline against \
                              a specified baseline')
    parser.add_argument("--select",
                        nargs='+',
                        dest='select_marker_tests',
                        help='selects tests with given marker(s) for display or '
                             'execution (ex. bat_test, cert_test, etc)')
    parser.add_argument("--integration",
                        action='store_true',
                        dest='integration',
                        help='specify integration as test type for selected markers')
    parser.add_argument("--system",
                        action='store_true',
                        dest='system',
                        help='specify system as test type for selected markers')
    parser.add_argument("--display",
                        action='store_true',
                        dest='display_marker_tests',
                        help='displays test list with given marker(s) '
                             '(ex. bat_test, cert_test, etc)')
    parser.add_argument("--include",
                        nargs='+',
                        dest='include_paths',
                        help='includes specified directories/files only '
                             'for marker search')
    parser.add_argument("--exclude",
                        nargs='+',
                        dest='exclude_paths',
                        help='excludes specified directories/files '
                             'from marker search')
    parser.add_argument("--retry",
                        type=int,
                        help='open retry function')
    parser.add_argument("--retest",
                        type=int,
                        help='open retest function')
    parser.add_argument("--markers",
                        type=str,
                        nargs='+',
                        help='run markable test case,add in pytest.ini first')
    parser.add_argument("--count",
                        type=int,
                        help='cases execution times')
    parser.add_argument("--piplineType",
                        type=str,
                        help='set pipline type')
    parser.add_argument("--multiInstance",
                        type=str,
                        help='multi instance')
    parser.add_argument("--project",
                        type=str,
                        help='run specific project test cases')
    parser.add_argument("--conn_type",
                        type=str,
                        help='connect DUT with serial or adb')
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    runner = LocalTestRunner(args)

    if args.list_modules:
        runner.list_modules()
        exit(0)

    elif args.list_tests:
        runner.list_tests()
        exit(0)

    elif args.modules:
        runner.handle_test_modules()

    elif args.all:
        if args.retest:
            for i in range(args.retest+1 or 1):
                runner.retest_count = i + 1
                runner.execute_all()
                runner.print_section_log("TEST EXECUTION SUMMARY")
                runner.test_session.generate_result_summary(runner.retest_count)
        else:
            runner.execute_all()
    runner.print_section_log("TEST EXECUTION SUMMARY")
    runner.test_session.generate_result_summary()
    time.sleep(10)
