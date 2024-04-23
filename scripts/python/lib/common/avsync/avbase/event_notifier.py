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

import sys
import logging


def event_listener(*events):
    def wrapped_f(f):
        f.events = events
        return f

    return wrapped_f


class EventData(object):
    _EVENTS = []

    def __init__(self, name):
        self._name = name
        self._callbacks = []
        EventData._EVENTS.append(self)

    def __iadd__(self, cb):
        self._callbacks.append(cb)
        return self

    def __call__(self, *args, **kwargs):
        for cb in self._callbacks:
            try:
                cb(*args, **kwargs)
            except:
                ex = sys.exc_info()
                logging.debug(f"EventData cb error, function:{cb.__name__} {ex}")

    def __repr__(self):
        return 'EventData %s' % self._name

    @classmethod
    def clear(cls):
        for event in cls._EVENTS:
            event._cb = []
