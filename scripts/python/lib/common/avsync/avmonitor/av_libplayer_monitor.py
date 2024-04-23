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
import time
import logging
from concurrent.futures.thread import ThreadPoolExecutor
from lib.common.avsync.avbase.aml_cat_node import CatNode
from lib.common.avsync.avbase.aml_observable import AMLObservable
from lib.common.avsync.avbase.aml_observer import AMLObserver
from lib.common.avsync.avbase.event_notifier import EventData, event_listener
from lib.common.avsync.avbase.eventbase import EventBase

from lib.common.avsync.avmonitor import BaseMonitor
from util.Decorators import singleton

disable_video = EventData('DISABLEVIDEO')
frame_count = EventData('FRAME_COUNT')
av_not_synced = EventData('AVNOTSYNCED')


@singleton
class AVLibplayerMonitor(BaseMonitor, AMLObserver, EventBase):
    '''
    Background detection control : check av sync and display frame
    '''

    CHECK_POINT = {"pts": ["0x0", "0xffffffff", "0x0"], "frame_count": 0}
    STATUS = {"avsync": 1, "frame_count": 0}
    AV_DIFF = 18000

    def __init__(self):
        BaseMonitor.__init__(self)
        AMLObserver.__init__(self)
        EventBase.__init__(self)
        self.executor = None
        self.process_message = True
        # logging.debug(self.executor)
        self.videoptscheck = VideoPtsCheck()
        self.videoframe = DisplayFrameCheck()

    @event_listener(frame_count)
    def set_frame_count(self, display_frame_count):
        logging.debug(display_frame_count)
        self.STATUS["frame_count"] = display_frame_count

    @event_listener(av_not_synced)
    def set_av_sync(self):
        self.STATUS["avsync"] = 0

    def update_check_point(self, key, value):
        logging.debug(f'key: {key}, value: {value}')
        change = False
        for (k, v) in self.CHECK_POINT.items():
            logging.debug(f'k: {k}, v: {v}')
            if key == k and value != v:
                change = True
                self.CHECK_POINT[k] = value

        logging.debug(key)
        if key == "pts" and change is True:
            logging.debug(value)
            if value[0] == "0x0":
                change = False
                return
            if abs(int(self.CHECK_POINT["pts"][0], 16) -
                   int(self.CHECK_POINT["pts"][1], 16)) > self.AV_DIFF:
                logging.debug("av_not_synced")
                av_not_synced()
                change = False

        if key == "frame_count" and change is True:
            logging.debug(value)
            logging.debug("call frame_count ")
            frame_count(value)
            change = False

    def monitor_process_data(self):
        logging.debug("monitor_process_data start")
        while self.process_message:
            item = self.monitor_queue.get()
            # logging.debug(item)
            if isinstance(item, dict):
                # logging.debug(item.keys())
                for key in item.keys():
                    logging.debug(f'key: {key}')
                    self.update_check_point(key, item[key])

    def start_monitor(self):
        self.process_message = True
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.videoptscheck.register_observer(self)
        self.videoframe.register_observer(self)
        if self.executor:
            self.executor.submit(self.videoptscheck.get_videopts)
            self.executor.submit(self.videoframe.getVideoFrameCounts)
            self.executor.submit(self.monitor_process_data)

    def stop_monitor(self):
        self.process_message = False
        self.monitor_queue.put("stop")
        self.videoptscheck.stop_video_ptscheck()
        self.videoframe.stop_video_frame_count_check()
        self.videoptscheck.remove_observer(self)
        if self.executor:
            self.executor.shutdown()

    @classmethod
    def _get_monitor(cls):
        monitor = cls()
        return monitor

    @classmethod
    def get_monitor(cls):
        return cls._get_monitor()

    def update(self, data):
        self.monitor_queue.put(data)
        # logging.debug(stat)

    def get_libplayer_status(self):
        return self.STATUS


@singleton
class VideoLayerCheck(AMLObservable, CatNode):
    '''
    videolayer check control
    '''

    NODE_PATH = "/sys/class/video/disable_video"

    def __init__(self):
        CatNode.__init__(self)
        self.run_flag = True
        self.video_layer = {"videolayer": 1}
        self._observer = []

    def register_observer(self, observer: AMLObserver):
        if observer not in self._observer:
            self._observer.append(observer)

    def remove_observer(self, observer: AMLObserver):
        try:
            self._observer.remove(observer)
        except ValueError:
            pass

    def notify_observers(self):
        for observer in self._observer:
            observer.update(self.video_layer)

    def stop_analyse_videolayer(self):
        self.run_flag = False
        self.video_layer["videolayer"] = 1

    def start_analyse_videolayer(self):
        self.run_flag = True

    def analyse_videolayer(self, interval=1):

        while self.run_flag:
            rc, output = self.cat_node(self.NODE_PATH)
            logging.debug(f'output = {int(output)}, videolayer = {self.video_layer["videolayer"]}')
            if int(output) != self.video_layer["videolayer"]:
                self.video_layer["videolayer"] = int(output)
                self.notify_observers()
            time.sleep(interval)


@singleton
class VideoPtsCheck(AMLObservable, CatNode):
    '''
    pts check control
    '''
    VIDEO_PTS = "/sys/class/tsync/pts_*"

    def __init__(self):
        CatNode.__init__(self)
        self.run_flag = True
        self._observer = []
        self.pts = {"pts": ["0x0", "0xffffffff", "0x0"]}

    def register_observer(self, observer: AMLObserver):
        if observer not in self._observer:
            self._observer.append(observer)

    def remove_observer(self, observer: AMLObserver):
        try:
            self._observer.remove(observer)
        except ValueError:
            pass

    def notify_observers(self):
        for observer in self._observer:
            observer.update(self.pts)

    def get_videopts(self, interval=1):
        while self.run_flag:
            pts_rc, pts_output = self.cat_node(self.VIDEO_PTS)
            pts_list = pts_output.split("\n")
            length = len(pts_list)

            # logging.debug(length)
            if length == 7:
                if pts_list[5] != self.pts["pts"][0] or pts_list[0] != self.pts["pts"][1] or \
                        pts_list[3] != self.pts["pts"][2]:
                    self.pts["pts"][0] = pts_list[5]
                    self.pts["pts"][1] = pts_list[0]
                    self.pts["pts"][2] = pts_list[3]
                    self.notify_observers()
                    logging.debug(pts_list)
            elif length == 4:
                if pts_list[3] != self.pts["pts"][0] or pts_list[0] != self.pts["pts"][1] or \
                        pts_list[2] != self.pts["pts"][2]:
                    self.pts["pts"][0] = pts_list[3]
                    self.pts["pts"][1] = pts_list[0]
                    self.pts["pts"][2] = pts_list[2]
                    self.notify_observers()
                    logging.debug(pts_list)
            else:
                logging.warning('Need to be handle')
                # TODO: add more action

            # logging.debug(f'video_pts: {pts_list}')
            # logging.debug(f'video_pts: {pts_list[5]} audio_pts: {pts_list[0]} pcrscr_pts: {pts_list[3]}')
            # logging.debug(self.pts)
            # logging.debug(f'video: {self.pts["pts"][0]}')

            time.sleep(interval)

    def stop_video_ptscheck(self):
        self.run_flag = False

    def start_video_ptscheck(self):
        self.run_flag = True


@singleton
class DisplayFrameCheck(AMLObservable, CatNode):
    '''
    frame check control
    '''
    DISPLAY_FRAME = "/sys/module/amvideo/parameters/display_frame_count"

    def __init__(self):
        CatNode.__init__(self)
        self.run_flag = True
        self._observer = []
        self.video_frame_count = {"frame_count": 0}

    def register_observer(self, observer: AMLObserver):
        if observer not in self._observer:
            self._observer.append(observer)

    def remove_observer(self, observer: AMLObserver):
        try:
            self._observer.remove(observer)
        except ValueError:
            pass

    def notify_observers(self):
        for observer in self._observer:
            observer.update(self.video_frame_count)

    def getVideoFrameCounts(self, interval=1):
        while self.run_flag:
            frame_rc, frame_output = self.cat_node(self.DISPLAY_FRAME)
            if self.video_frame_count["frame_count"] != frame_output:
                self.video_frame_count["frame_count"] = frame_output
                logging.debug(f'frame count change {self.video_frame_count["frame_count"]}')
                self.notify_observers()

            time.sleep(interval)

    def stop_video_frame_count_check(self):
        self.run_flag = False

    def start_video_frame_count_check(self):
        self.run_flag = True
