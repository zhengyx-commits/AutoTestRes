#!/usr/bin/env python
# Copyright 2021 Amlogic.com, Inc. or its affiliates. All rights reserved.
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
import pytest


def get_device():
    device_list = []
    if isinstance(pytest.serialnumber, list):
        device_ids = pytest.serialnumber
        for device_id in device_ids:
            device_list.append(device_id)
    else:
        device_id = pytest.config['device_id']
        device_list.append(device_id)
    return device_list


def get_read_buffer():
    outputValue_list = []
    if isinstance(pytest.device, list):
        for device_config in pytest.device:
            if device_config._adblogcat_reader._read_buffer:
                outputValue = device_config._adblogcat_reader._read_buffer.get()
                if outputValue:
                    outputValue_list.append(outputValue)
    else:
        if pytest.device._adblogcat_reader._read_buffer:
            outputValue = pytest.device._adblogcat_reader._read_buffer.get()
            if outputValue:
                outputValue_list.append(outputValue)
    return outputValue_list


class CheckAndroidVersion:
    def __init__(self):
        self.version = "ro.build.version.sdk"

    def get_android_version(self):
        android_version = self.version
        return android_version
