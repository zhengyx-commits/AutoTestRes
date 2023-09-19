#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/4/24 14:24
# @Author  : chao.li
# @Site    :
# @File    : PrimeVideo.py
# @Software: PyCharm

from .OnlineParent import Online


class PrimeVideo(Online):
    '''
    Online video playback

    Attributes:
        PLAYERACTIVITY_REGU : player command regular
        PACKAGE_NAME : player package name
        PLAYTYPE : playback type
        VIDEO_TAG_LIST : play video info list [dict]
        VIDEOINFO : video info

    '''

    PLAYERACTIVITY_REGU = 'am start -a android.intent.action.MAIN -n com.amazon.avod/.playbackclient.FOS5TvPlaybackActivity --es asin {}'
    PACKAGE_NAME = 'com.amazon.amazonvideo.livingroom'
    PLAYTYPE = 'PrimeVideo'
    VIDEO_INFO = []

    VIDEO_TAG_LIST = [{'link': 'B0799QX8VZ', 'name': 'The Grand Tour S3:E1'},
                      {'link': 'B06VYH1DF2', 'name': 'The Marvelous Mrs. Maisel S1:E1'},
                      {'link': 'B07ZCLW1S3', 'name': 'Jack Ryan: Cargo S2:E1'},
                      {'link': 'B087WQGNHC', 'name': 'Jimmy O.Yang: Good Deal'},
                      {'link': 'B0875SXMPJ', 'name': 'Bosch: Good People on Both Sides S6:E2'},
                      {'link': 'B07NV6CM54', 'name': 'The Tick: Choose Love! S2:E10'},
                      {'link': 'B089XWNZ4W', 'name': 'Bosch, Season 1, EP.1'}]

    def __init__(self):
        super(PrimeVideo, self).__init__('PrimeVideo')
