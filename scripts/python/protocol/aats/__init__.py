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
import time
import logging
from .aats_target.aats_adb_target import AATSADBTarget
from .aats_target.aats_serial_target import AATSSerialTarget
from .exceptions import AATSDeviceNotFoundError


# log = logging.getLogger(__name__)

class AATS(object):
    """
    Class for interaction with AATS
    """

    @staticmethod
    def get_serial_target(serial_port, baudrate, username="", password=""):
        params = dict(target=AATSSerialTarget.__name__, serial_port=serial_port, baudrate=baudrate)
        logging.debug(params)
        return AATSSerialTarget.get_target(serial_port, baudrate, username, password)

    @staticmethod
    def get_adb_target(device_id, adbpath=None):
        params = dict(target=AATSADBTarget.__name__, device_id=device_id, adbpath=adbpath)
        logging.debug(params)
        return AATSADBTarget.get_target(device_id, adbpath=adbpath)


def get_device_object(device_conf):
    """
    :param device_conf:
    :return:
    """

    """
    =====================================================================================================
    Need to setup connect type before run Auto-Test in config/config.json,
    following are reference type for device connecting
    @connect_type:
    "adb"
    "serial"
    "ssh"
    =====================================================================================================
    """
    connect_type = "adb"
    device_id = device_conf['device_id']
    serial_port = device_conf['serial_port']
    # baudrate = device_conf.get('baudrate', 115200)
    # ipaddr = device_conf.get('ipaddr', "")
    # sshport = device_conf.get('sshport', 22)

    target = None

    logging.info(f"[get_device_object]connect_type:{connect_type}\n")
    # if connect_type.startswith('adb'):
    target = AATS.get_adb_target(device_id)
    # elif connect_type.startswith('serial'):
    #     target = AATS.get_serial_target(serial_port, baudrate)
    #     if not target:
    #         raise AATSDeviceNotFoundError("No aats enabled device at: %s" % serial_port)
    #     # Send newline to clear out any previously sent input
    #     target._serial_device.write(b'\n')
    #     # For some reason, it's taking a second to
    #     # clear out pre-existing input
    #     # without this, the output of the next command executed through
    #     # .shell includes garbage output
    #     time.sleep(1)
    #     target._read()
    # else:
    #     target = AATS.get_adb_target(device_id)

    if not target:
        raise AATSDeviceNotFoundError("No target device found.")

    logging.debug("Target is: {}".format(type(target).__name__))
    return target
