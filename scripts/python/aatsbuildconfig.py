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
from collections import OrderedDict
import json
import logging
import os
from baseConfigParser import get_target_json_data
from tools.yamlTool import yamlTool
logging.basicConfig(level=logging.DEBUG)

AATS_TESTS_DIR_NAME = "tests"


class AATSBuildConfig:
    aats_test_cases_config = OrderedDict()
    aats_test_cases_full_config = OrderedDict()
    aats_test_cases = OrderedDict()
    aats_test_cases_project = OrderedDict()

    def __init__(self, args):
        self.args = args
        self.module_source_map = OrderedDict()
        self.module_project_map = OrderedDict()
        self.module_group_map = OrderedDict()

        # prepare testcases.json
        prj = ''
        target_json = get_target_json_data("target")
        if target_json:
            prj = target_json.get("prj")
        if prj == 'wifi':
            testcase = yamlTool(os.getcwd() + '/config/config_wifi.yaml').get_note('test_config')['config']
            path = f'config/testcases_{testcase}.json'
        else:
            path = f'config/testcases_{prj}.json'

        self.testcases_json_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), path)
        self._load_test_cases(self.testcases_json_file)
        # print("self.module_project_map", self.module_project_map)
        # print("self.aats_test_cases_full_config", self.aats_test_cases_full_config)
        self.tests_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), AATS_TESTS_DIR_NAME)

        # for k, v in self.aats_test_cases_full_config.items():
        #     self.aats_test_cases[k] = v['pytest_args']

        if self.module_project_map:
            for k, v in self.module_project_map.items():
                self.aats_test_cases_project[k] = v

        if prj == 'tv_amazon':
            self.aats_test_cases_full_config = dict(sorted(self.aats_test_cases_full_config.items(),
                                                           key=lambda x: x[1]['group'][0]))
        else:
            self.aats_test_cases_full_config = dict(sorted(self.aats_test_cases_full_config.items(),
                                                           key=lambda x: x[1]['author'][0]))

        for k, v in self.aats_test_cases_full_config.items():
            if self.args.project:
                if 'project' in v:
                    if (self.args.project in v['project']) and (k in list(self.aats_test_cases_project.keys())):
                        self.aats_test_cases_config[k] = v['pytest_args']
                        self.aats_test_cases[k] = v['pytest_args']
                else:
                    pass
            else:
                # if 'project' not in v:
                self.aats_test_cases_config[k] = v['pytest_args']
                self.aats_test_cases[k] = v['pytest_args']

        # print("run aats_test_cases", len(self.aats_test_cases))

    def _load_test_cases(self, config_file):

        if not self.path_exists(config_file):
            return None

        with open(config_file) as test_cases_json:
            try:
                data = json.load(test_cases_json)
            except ValueError as e:
                logging.error("Unable to load json from {} {}".format(config_file, e))
                logging.error(test_cases_json.read())
                return None

        for testcase in data['testcases']:
            testcase_path = testcase['path']
            if not os.path.exists(
                    os.path.join(os.path.dirname(os.path.realpath(__file__)), testcase_path)):
                continue

            # create a full dictionary from testcases.json, excludes testsuite not in path
            pytest_args = ""
            for arg in testcase.get('arg_list', []):
                if arg.startswith("-"):
                    arg = " {}".format(arg)
                pytest_args = "{}{}".format(testcase_path, arg)
            if not pytest_args:
                pytest_args = testcase_path
            testcase['pytest_args'] = pytest_args
            if 'source_module' in testcase:
                self.module_source_map[testcase['name']] = testcase['source_module']
            if 'project' in testcase:
                self.module_project_map[testcase['name']] = testcase['project']
            if 'group' in testcase:
                self.module_group_map[testcase['name']] = testcase['group']
            self.aats_test_cases_full_config[testcase['name']] = testcase

    def get_config_entries(self):
        """Provide config entries
        Returns:
        A list of strings representing config entries,
        content of entries should be transparent to caller
        """
        return list(self.aats_test_cases_config)

    def get_config_case_entries(self):
        """Provide config entries
        Returns:
        A list of strings representing config entries,
        content of entries should be transparent to caller
        """
        return list(self.aats_test_cases)

    def get_entry_path(self, entry):
        return self.aats_test_cases_config.get(entry, None)

    @staticmethod
    def path_exists(path):
        if not os.path.exists(path):
            logging.debug("{} does not exist".format(path))
            return False
        return True
