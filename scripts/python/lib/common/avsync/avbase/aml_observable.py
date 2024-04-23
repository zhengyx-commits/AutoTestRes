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
# d

from abc import ABCMeta, abstractmethod


class AMLObservable(metaclass=ABCMeta):
    '''
    abstract class for observer control
    '''

    @abstractmethod
    def register_observer(self, observer):
        ...

    @abstractmethod
    def remove_observer(self, observer):
        ...

    @abstractmethod
    def notify_observers(self):
        ...
