#!/usr/bin/env python
#
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

"""Implements log obfuscation functionality """

import glob
import logging
import pytest
import re
import os


class LogCleaner(object):

    # keys to obfuscate
    OBFUSCATION_KEYS = ["ssid", "psk", "ip", "pwd", "mac"]

    def __init__(self, obf_set=set()):
        self.obf_set = obf_set

    def extract_obfuscate_data(self, data):
        """ Extracts obfuscation info from the data
        provided

        Args:
            data(dict) : dict of data to parse for
                         extraction
        """
        def _collect_data(data_dict):
            # recursively collect and extract data
            for key, val in data_dict.items():
                if isinstance(val, dict):
                    _collect_data(val)
                else:
                    [self.obf_set.add(str(val)) for obkey in
                     self.OBFUSCATION_KEYS if obkey in key]
        if data:
            _collect_data(data)
        self.obf_set = set(filter(None, self.obf_set))

    def obfuscate_logs(self, directory, obf_set=None):
        """
        obfuscates log files in the directory specified using the
        info provided.

        Args:
            directory(str) : directory to check the files
            obf_set(set, optional) : set of items to obfuscate

        Returns:
            None
        """
        if not obf_set:
            obf_set = self.obf_set
        if not os.path.exists(directory):
            logging.debug("Skipping log obfuscation")
            return

        # recursively get the list of files in directory
        files = [f for f in glob.glob(
            directory + "/**/*.*", recursive=True)]

        # obfuscate sensitive data in the files
        for fil in files:
            if os.path.isdir(fil):
                continue
            try:
                with open(fil, 'r+') as f:
                    text = f.read()
                    for item in obf_set:
                        text = re.sub(item, "xxxxx", text)
                    f.seek(0)
                    f.write(text)
                    f.truncate()
            except Exception as exp:
                logging.debug(
                    "Exception: {}, Could not obfuscate: {}, skipping".format(
                        exp, fil))
