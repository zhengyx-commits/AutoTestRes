#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/3/10 下午14:00
# @Author  : jun.yang
# @Site    : SH #5
# @File    : GooglePlayMoviesCheck_Keywords.py
# @Email   : jun.yang1@amlogic.com
# @Software: PyCharm
import pytest


class ExoplayerCheckKeywords:

    # seek
    SEEK_KEYWORDS = ["seekStarted", "isPlaying"]
    SEEK_KEYWORDS_LOG = ["03-14 15:33:53.337  9398  9398 D EventLogger: seekStarted [eventTime=498.67, mediaPos=586.26, window=0, period=0]",
                     "03-14 15:33:53.344  9398  9398 D EventLogger: isPlaying [eventTime=498.68, mediaPos=599.73, window=0, period=0, false]"]

    # Home to play
    HOME_PLAY_KEYWORDS = ["LauncherX to foreground. The context is com.google.android.apps.tv.launcherx.home.HomeActivity"]
    HOME_PLAY_KEYWORDS_LOG = ["03-15 10:57:31.514  1569  1716 W BootModeAppToForeground: LauncherX to foreground. The context is com.google.android.apps.tv.launcherx.home.HomeActivity."]

    SEEK_LOGCAT = "logcat -s EventLogger"
    HOME_PLAY_LOGCAT = "logcat -s BootModeAppToForeground"


