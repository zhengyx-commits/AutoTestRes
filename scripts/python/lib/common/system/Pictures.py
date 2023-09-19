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

import os
import pytest
import logging
from tools.resManager import ResManager
from lib.common.system.ADB import ADB

PICTURES_RESOURCE = "/sdcard/Pictures"
NATIVEIMAGEPLAYERA_APP_NAME = "com.droidlogic.imageplayer"
NATIVEIMAGEPLAYERA_APP_ACTIVITY_NAME = "com.droidlogic.imageplayer/.FullImageActivity"
RESOLUTION = {"4k": "3840x2160", "1080p": "1920x1080"}


class Pictures(ADB):

    def __init__(self, device):
        ADB.__init__(self, "NativeImagePlayer", unlock_code="", logdir=pytest.result_dir, stayFocus=True)
        self.resManager = ResManager()
        self.res_pictures = self.resManager.get_target("pictures/")
        # path = os.getcwd()
        # self.res_pictures = f'{path}/res/pictures/'

    def push_pictures_res(self):
        self.push(self.res_pictures, PICTURES_RESOURCE)

    def check_image_player_apk_exist(self):
        rc, out = self.run_shell_cmd('pm list packages', 2)
        packagelist = out.split()
        if len(packagelist) > 0:
            for item in packagelist:
                logging.debug(item)
                if NATIVEIMAGEPLAYERA_APP_NAME in item:
                    return True
                continue
            return False
        return False

    def picture_path_config(self, type="jpg", resolution="4k"):
        path = f"file://{PICTURES_RESOURCE}/pictures/{type}/{type}_{RESOLUTION[resolution]}_test.{type}"
        logging.debug(path)
        return path

    def show_picture(self, path):
        if path is None:
            pytest.fail("picture path  none.")

        cmd = (f'am start -S -a android.intent.action.VIEW -d {path} -t image/* -n'
               f' {NATIVEIMAGEPLAYERA_APP_ACTIVITY_NAME}')

        logging.debug(cmd)

        self.shell(cmd)

    def stop_picture(self):
        cmd = f'am force-stop {NATIVEIMAGEPLAYERA_APP_NAME}'
        self.shell(cmd)
