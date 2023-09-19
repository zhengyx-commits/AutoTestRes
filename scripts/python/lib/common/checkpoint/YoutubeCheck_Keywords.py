#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/3/10 下午14:00
# @Author  : jun.yang
# @Site    : SH #5
# @File    : YoutubeCheck_Keywords.py
# @Email   : jun.yang1@amlogic.com
# @Software: PyCharm
import pytest


class YoutubeCheckKeywords:

    # seek, amlsource
    SEEK_KEYWORDS = ["MediaSession setPlaybackState: PAUSED, position:", "MediaSession setPlaybackState: PLAYING, position:"]
    SEEK_KEYWORDS_LOG = ["03-09 16:43:32.909  7561  7561 I starboard_media: MediaSession setPlaybackState: PAUSED, position: 2239283 ms, speed: 0.000000 x",
                     "03-09 16:43:45.701  7561  7561 I starboard_media: MediaSession setPlaybackState: PLAYING, position: 2268969 ms, speed: 1.000000 x"]

    HOME_PLAY_KEYWORDS = ["LauncherX to foreground. The context is com.google.android.apps.tv.launcherx.home.HomeActivity"]
    HOME_PLAY_KEYWORDS_LOG = ["03-15 10:57:31.514  1569  1716 W BootModeAppToForeground: LauncherX to foreground. The context is com.google.android.apps.tv.launcherx.home.HomeActivity."]

    SEEK_LOGCAT = "logcat -s starboard_media"
    HOME_PLAY_LOGCAT = "logcat -s BootModeAppToForeground"


