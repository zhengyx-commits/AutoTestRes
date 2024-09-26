#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2021/7/12 11:02
# @Author  : chao.li
# @Site    :
# @File    : test_OTT-Sanity_Func_079-082_Netflix.py
# @Software: PyCharm

import pytest
from lib.common.playback.Netflix import Netflix
from lib.common.checkpoint.PlayerCheck_Base import PlayerCheck_Base
from tests.OTT_Hybrid import config_yaml
import logging

netflix = Netflix()
playerCheck = PlayerCheck_Base()
apk_exist = netflix.check_Netflix_exist()

p_conf_online = config_yaml.get_note('conf_online')
p_conf_check_seek_enable = p_conf_online['check_seek_enable']


# logging.info(f'netflix p_conf_check_seek_enable:{p_conf_check_seek_enable}')

@pytest.fixture(scope='module', autouse=True)
def setup_teardown():
    # 开启omx 打印
    netflix.netflix_setup()
    yield
    netflix.close_omx_info()
    netflix.home()


@pytest.mark.skipif(condition=(1 - apk_exist), reason='apk not exist')
def test_online_video():
    assert netflix.netflix_play(seekcheck=p_conf_check_seek_enable), 'playback not success'