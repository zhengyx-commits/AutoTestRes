#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/3/10 下午14:00
# @Author  : jun.yang
# @Site    : SH #5
# @File    : GooglePlayMoviesCheck_Keywords.py
# @Email   : jun.yang1@amlogic.com
# @Software: PyCharm
import pytest


class GooglePlayMoviesCheckKeywords:

    # seek
    SEEK_KEYWORDS = ["pause:350", "reset:398", "start:358"]
    SEEK_KEYWORDS_LOG = ["03-11 13:51:15.426   538  8925 V AmlogicVideoDecoderAwesome2: [22]pause:350",
                     "03-11 13:51:15.428   538  8925 V AmlogicVideoDecoderAwesome2: [22]reset:398",
                    "03-11 13:51:15.460   538  8925 V AmlogicVideoDecoderAwesome2: [22]start:358"]

    # Home to play
    HOME_PLAY_KEYWORDS = ["com.google.android.videos's active state now is : false", "com.google.android.videos's active state now is : true"]
    HOME_PLAY_KEYWORDS_LOG = ["03-13 16:05:56.385  2564  2564 D WargCastTvAppManager: com.google.android.videos's active state now is : false LaunchAppState : null AttachToAppState : ATTACHED",
                            "03-13 16:06:40.748  2564  2564 D WargCastTvAppManager: com.google.android.videos's active state now is : true LaunchAppState : null AttachToAppState : WAITING_FOR_ACTIVATE_STATE"]

    SEEK_LOGCAT = "logcat -s AmlogicVideoDecoderAwesome2"
    HOME_PLAY_LOGCAT = "logcat -s WargCastTvAppManager"


