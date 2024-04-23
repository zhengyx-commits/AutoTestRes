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

import logging
import inspect
from .event_notifier import EventData


class EventBase(object):
    '''
    count fun which has events attr
    event_listener tag fun
    '''

    def __init__(self):
        self.init_data_listeners()

    def init_data_listeners(self):
        '''
        useless
        @return:
        '''
        for listener_name, listener in inspect.getmembers(self, lambda f: hasattr(f, 'events')):
            for event in listener.events:
                event += listener

    def destroy(self):
        logging.debug('%s.destroy' % self.__class__.__name__)
        EventData.clear()
