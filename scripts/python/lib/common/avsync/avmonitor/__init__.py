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
from abc import ABCMeta, abstractmethod
from queue import Queue


class BaseMonitor(metaclass=ABCMeta):
    """
    Base class for avsync monitor communicators.
    """

    def __init__(self):
        self.monitor_queue = Queue()

    @abstractmethod
    def start_monitor(self):
        pass

    @abstractmethod
    def stop_monitor(self):
        pass
