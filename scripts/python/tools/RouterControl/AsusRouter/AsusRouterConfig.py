#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/10/18 16:08
# @Author  : chao.li
# @Site    :
# @File    : AsusRouterConfig.py
# @Software: PyCharm

class AsusRouterConfig:
    '''
    asus router setting config
    '''

    BAND_LIST = ['2.4 GHz', '5 GHz']
    WIRELESS_MODE = ['自动', 'AX only', 'N/AC/AX mixed', 'Legacy']
    BANDWIDTH_2_LIST = ['20/40 MHz', '20 MHz', '40 MHz']
    AUTHENTICATION_METHOD_DICT = {
        'Open System': '1',
        'WPA2-Personal': '2',
        'WPA3-Personal': '3',
        'WPA/WPA2--Personal': '4',
        'WPA2/WPA3--Personal': '5',
        'WPA2-Enterprise': '6',
        'WPA/WPA2-Enterprise': '7',
    }

    AUTHENTICATION_METHOD_LEGCY_DICT = {
        'Open System': '1',
        'Shared Key': '2',
        'WPA2-Personal': '3',
        'WPA3-Personal': '4',
        'WPA/WPA2-Personal': '5',
        'WPA2/WPA3-Personal': '6',
        'WPA2-Enterprise': '7',
        'WPA/WPA2-Enterprise': '8',
        'Radius with 802.1x': '9',
    }

    PROTECT_FRAME = {
        '停用': 1,
        '非强制启用': 2,
        '强制启用': 3
    }

    WEP_ENCRYPT = {
        'WEP-64bits': '1',
        'WEP-128bits': '2'
    }

    WPA_ENCRYPT = {
        'AES': 1,
        'TKIP+AES': 2
    }

    PASSWD_INDEX_DICT = {
        '1': '1',
        '2': '2',
        '3': '3',
        '4': '4'
    }


class ConfigError(Exception):
    def __str__(self):
        return 'element error'


class Asus86uConfig(AsusRouterConfig):
    '''
    asus 86u router setting config
    '''

    BANDWIDTH_5_LIST = ['20 MHz']

    CHANNEL_5_DICT = {
        'auto': '1',
        '36': '2',
        '40': '3',
        '44': '4',
        '48': '5',
        '52': '6',
        '56': '7',
        '60': '8',
        '64': '9',
        '100': '10',
        '104': '11',
        '108': '12',
        '112': '13',
        '116': '14',
        '120': '15',
        '124': '16',
        '128': '17',
        '132': '18',
        '136': '19',
    }

    CHANNEL_2_DICT = {
        'auto': '1',
        '1': '2',
        '2': '3',
        '3': '4',
        '4': '5',
        '5': '6',
        '6': '7',
        '7': '8',
        '8': '9',
        '9': '10',
        '10': '11',
        '11': '12',
        '12': '13',
        '13': '14',
    }


class Asus88uConfig(AsusRouterConfig):
    '''
    asus 88u router setting config
    '''

    BANDWIDTH_5_LIST = ['20/40/80 MHz', '20 MHz', '40 MHz', '80 MHz']

    CHANNEL_5_DICT = {
        'auto': '1',
        '36': '2',
        '40': '3',
        '44': '4',
        '48': '5',
        '52': '6',
        '56': '7',
        '60': '8',
        '64': '9',
        '100': '10',
        '104': '11',
        '108': '12',
        '112': '13',
        '116': '14',
        '120': '15',
        '124': '16',
        '128': '17',
        '132': '18',
        '136': '19',
        '140': '20',
        '144': '21',
        '149': '22',
        '153': '23',
        '157': '24',
        '161': '25',
        '165': '26'
    }

    CHANNEL_2_DICT = {
        'auto': '1',
        '1': '2',
        '2': '3',
        '3': '4',
        '4': '5',
        '5': '6',
        '6': '7',
        '7': '8',
        '8': '9',
        '9': '10',
        '10': '11',
        '11': '12',
    }
