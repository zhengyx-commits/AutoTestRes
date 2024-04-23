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
import logging


class CatNode(object):
    '''
    adb control
    '''
    def __init__(self):
        self._device = pytest.device

    def cat_node(self, node_path):
        logging.debug("enter cat_node")
        rc = -1
        output = None
        if node_path is not None:
            cmd = f'cat {node_path}'
            rc, output = self._device.shell(cmd)
        return rc, output
