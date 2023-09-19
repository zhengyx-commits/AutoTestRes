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
import logging
import os
import json
import pytest

AATS_TARGET_FILE_NAME = "target.json"
AATS_CONFIG_JSON_PATH = "config/config.json"
OBFUSCATE_BLACK_LIST_KEYS = ["ssid", "psk"]


def get_device_config_by_device_id(devices):
    device_conf_list = []
    with open(AATS_CONFIG_JSON_PATH, 'r') as file:
        config_data = json.load(file)

    for device_conf in list(config_data['devices'].values()):
        for device_id in devices[0].split(','):
            pytest.multi_instance_devices.append(device_id)
            if device_id in device_conf['device_id'] and (device_id not in device_conf_list):
                device_conf_list.append(device_conf)
    return device_conf_list


def get_config_json():
    if os.environ.get('AATS_TEST_CONFIG_FILE'):
        return os.path.abspath(os.environ.get('AATS_TEST_CONFIG_FILE'))

    prj = ''
    pytest.target = get_target_json_data("target")
    if pytest.target:
        prj = pytest.target.get("prj")
    # path = f'config/config.json'
    return os.path.join(os.getcwd(), AATS_CONFIG_JSON_PATH), prj


def get_target_json_data(target):
    with open(os.path.join(os.getcwd(), AATS_TARGET_FILE_NAME)) as data_file:
        data = json.loads(data_file.read())

    collect_obfuscate_data(data[target])
    return data[target]


def get_config_json_data(config):
    path, prj = get_config_json()
    with open(path) as data_file:
        data = json.loads(data_file.read())

    collect_obfuscate_data(data[config][prj])
    return data[config][prj]


def get_config_data():
    file, prj = get_config_json()
    with open(file) as data_file:
        data = json.loads(data_file.read())
    return data, prj


def set_config_data(data):
    with open(get_config_json()[0], 'w') as data_file:
        json.dump(data, data_file)


def collect_obfuscate_data(data):
    # check if attribute exists
    if not hasattr(pytest, "obfuscate"):
        pytest.obfuscate = set()

    def collect_data(data_dict):
        # recursively collects and updates obfuscating data
        for key, val in data_dict.items():
            if isinstance(val, dict):
                collect_data(val)
            [pytest.obfuscate.add(str(val)) for obkey in
             OBFUSCATE_BLACK_LIST_KEYS if obkey in key]

    collect_data(data)
    pytest.obfuscate = set(filter(None, pytest.obfuscate))
