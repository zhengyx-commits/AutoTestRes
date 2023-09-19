#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2021/11/4 14:28
# @Author  : chao.li
# @Site    :
# @File    : xtsAnalyer.py
# @Software: PyCharm
import os
import subprocess
import xml.etree.ElementTree as ET
import json
from collections import defaultdict


class Analyzer():
    ROOT_PATH = f'{os.getcwd()}/vts_result/'

    def __init__(self, type):
        self.type = type.upper()

        # self.analyze_xml()
        # self.print_result()

    def analyze_xml(self):
        self.result = {}
        self.latest_path = self._get_latest_path()
        self.latest_report = self.ROOT_PATH + self.latest_path + '/test_result.xml'
        # print('Latest report : ', self.latest_report)
        self.tree = ET.parse(self.latest_report)
        self.root = self.tree.getroot()
        for module in self.root.iter('Module'):
            self.result[module.attrib['name']] = {'Done': module.attrib['done']}
            for case in module.iter('Test'):
                self.result[module.attrib['name']][case.attrib['name']] = case.attrib['result']
        with open('../vts.json', 'w') as f:
            f.write(str(self.result))

    def print_result(self):
        self.pretty_table_data = []
        self.count = defaultdict(int)
        for k, v in self.result.items():
            res_pass, res_skip, res_fail, res_error, res_assumption_fail = 0, 0, 0, 0, 0
            if v['Done'] == 'true':
                for res in v:
                    if v[res] == 'pass':
                        res_pass += 1
                    elif v[res] == 'IGNORED':
                        res_skip += 1
                    elif v[res] == 'ASSUMPTION_FAILURE':
                        res_assumption_fail += 1
                    else:
                        res_fail += 1
            else:
                res_error = 1
            # print(f'Module name : {k} Pass : {res_pass} Fail : {res_fail} Error : {res_error}')
            self.pretty_table_data.append([k, self.type, res_pass, res_fail, res_skip, res_error, '-', self.latest_report])
            self.count['modules'] += 1
            if res_error != 0:
                self.count['errors'] += 1
            elif res_fail != 0:
                self.count['failures'] += 1
            elif res_pass != 0:
                self.count['passes'] += 1
            else:
                self.count['skipped'] += 1

    def _get_latest_path(self):
        # print("ls -l %s |tail -n 1|awk '{print $NF}'" % self.ROOT_PATH)
        return subprocess.check_output("ls -l %s |tail -n 1|awk '{print $NF}'" % self.ROOT_PATH, shell=True,
                                       encoding='utf-8').strip()

# analyzer = Analyzer('vts')
