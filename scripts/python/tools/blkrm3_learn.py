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
import os
import time
import json
import pytest
import broadlink as blkrm3

AATS_CONFIG_FILE_NAME = "config.json"

OBFUSCATE_BLACK_LIST_KEYS = ["ssid", "psk"]
keymap_path = os.path.abspath(os.path.join(os.path.split(os.path.abspath(__file__))[0], "../multimediaplayer"))


def get_config_json():
    if os.environ.get('AATS_TEST_CONFIG_FILE'):
        return os.path.abspath(os.environ.get('AATS_TEST_CONFIG_FILE'))
    return os.path.join(keymap_path, AATS_CONFIG_FILE_NAME)


def get_config_json_data(config):
    with open(get_config_json()) as data_file:
        data = json.loads(data_file.read())

    collect_obfuscate_data(data[config])
    return data[config]


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


if __name__ == '__main__':
    res = False
    error_message = ""
try:
    base_config = get_config_json_data("config")
    broadlinkconfig = base_config.get("broadlink")
    ipaddr = broadlinkconfig.get("ipaddr")
    broadcast_addr = broadlinkconfig.get("broadcast_addr")
    host = broadlinkconfig.get("host")

    code_name = input("Please input a key_code, eg: tv_ref_menu -> ")
    time.sleep(5)
    device = blkrm3.hello(host=host, timeout=5, local_ip_address=ipaddr)
    print(device.is_locked)
    ret = device.auth()
    print(ret)
    device.enter_learning()
    print('Enter learning mode...')
    time.sleep(5)
    print('Terminated learning...')
    time.sleep(5)
    ir_packet = device.check_data()
    if ir_packet:
        print(ir_packet, len(ir_packet), type(ir_packet))
        print('Ready to send packet via mini3...')
        time.sleep(1)
        myhex_str = bytes.hex(ir_packet)
        print(myhex_str)
        try:
            with open(code_name + '.txt', 'w') as f:
                f.write(myhex_str)
        finally:
            pass

    res = True

except Exception as e:
    error_message = "{}".format(e)
finally:
    assert res, error_message
