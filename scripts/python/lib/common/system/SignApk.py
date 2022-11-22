#!/usr/bin/env python
#
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
import enum
import logging
import os

from tools.resManager import ResManager

signature_type = ['platform', 'media', 'networkstack', 'shared', 'verity', 'testkey']


class SignApkType(enum.Enum):
    SIGN_MANUFACTURER_TYPE = 0
    SIGN_API_LEVEL_TYPE = 1


class SignatureType(enum.Enum):
    PLATFORM = 0
    MEDIA = 1
    NETWORKSTACK = 2
    SHARED = 3
    VERITY = 4
    TESTKEY = 5


def check_signed_dir(path=None):
    if path is None:
        raise ValueError("param path is None.")
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def check_signature_dir_exists(manufacturer='DroidLogic', api_level=19, path=None):
    manufacturer_flag = 0
    api_level_flag = 0
    android_api = 'android{}'.format(api_level)
    if path is None:
        raise ValueError("param path is None.")
    dirlist = os.listdir(path)
    logging.info(dirlist)
    logging.info(manufacturer)
    logging.info(api_level)
    if manufacturer in dirlist:
        manufacturer_flag = 1
    if android_api in dirlist:
        api_level_flag = 1
    if manufacturer_flag == 1 and api_level_flag == 1:
        signtype = SignApkType.SIGN_MANUFACTURER_TYPE
        return signtype, manufacturer
    elif manufacturer_flag == 1 and api_level_flag == 0:
        # TODO : same action as api is 1
        signtype = SignApkType.SIGN_MANUFACTURER_TYPE
        return signtype, manufacturer
    elif manufacturer_flag == 0 and api_level_flag == 1:
        signtype = SignApkType.SIGN_API_LEVEL_TYPE
        return signtype, api_level
    else:
        raise EnvironmentError("device signature not found.")


def check_signature_file_exists(signtype=SignatureType.PLATFORM, signature_path=None):
    if signature_path is None:
        raise ValueError("param signature_path is None.")

    sign_type = signature_type[signtype]
    logging.info(sign_type)
    pem_file = signature_path + '{}.x509.pem'.format(sign_type)
    pk8_file = signature_path + '{}.pk8'.format(sign_type)

    if os.path.exists(pem_file) and os.path.exists(pem_file):
        return pem_file, pk8_file
    else:
        raise EnvironmentError('pem or pk8 not found, signature type not supported.')


class SignApk:

    def __init__(self):
        self.res_manager = ResManager()
        self._signature_path = self.res_manager.get_target("signature/")
        self._root_path = os.getcwd()
        self._tools_path = '{}/tools/signapk.jar '.format(self._root_path)
        self.cmd = 'java -jar {}'.format(self._tools_path)
        # self._out_path = '{}/res/signed/'.format(self._root_path)
        # check_signed_dir(self._out_path)

    def sign_apk(self, signtype=SignatureType.PLATFORM, manufacturer='DroidLogic', api_level=19, debug_apk_name=None,
                 out_path=None, out_apk_name=None):
        """
        method to sign apk
        Args:
            signtype: Type of signature required by apk
            manufacturer: Manufacturer of the device. eg:getprop ro.product.manufacturer
            api_level: Android Api level of the device. eg:getprop ro.build.version.sdk
            debug_apk_name: The full path of debug apk. eg:'/home/xxx/xxx/xx/MultiMediaPlayer_inside_1.0_debug.apk'
            out_path: The Address of output dir. eg:'/home/xxx/xxx/xx/'
            out_apk_name: The Name of signed apk. eg:'MultiMediaPlayer_inside_1.0_signed.apk'
        Raises:
            Exception if the sign fails.
        """
        if debug_apk_name is None or out_path is None or out_apk_name is None:
            raise ValueError("param debug_apk_name or out_path or out_apk_name is None.")
        sign_type, signdir = check_signature_dir_exists(manufacturer, api_level, self._signature_path)

        outpath = check_signed_dir(out_path)
        logging.info(outpath)
        if sign_type == SignApkType.SIGN_API_LEVEL_TYPE:
            signature_path = self._signature_path + 'android{}/'.format(api_level)
        elif sign_type == SignApkType.SIGN_MANUFACTURER_TYPE:
            signature_path = self._signature_path + '{}/'.format(manufacturer)
        logging.info(signature_path)
        pem, pk8 = check_signature_file_exists(signtype, signature_path)

        out_apk = outpath + out_apk_name
        cmd = 'java -jar {} {} {} {} {}'.format(self._tools_path, pem, pk8, debug_apk_name, out_apk)
        res = os.system(cmd)
        if res == 0:
            return out_apk
        else:
            raise EnvironmentError("sign apk fail.")
