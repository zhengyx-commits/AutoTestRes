#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/03/26 19:39
# @Author  : A.T.
# @Site    :
# @File    : __init__.py.py
# @Software: PyCharm

import logging
from tests.OTT_Hybrid import *

p_conf_wifi = config_yaml.get_note('conf_wifi')

# p_conf_wifi_repeat_count = p_conf_wifi['repeat_count']
# p_conf_wifi_test_time = p_conf_wifi['test_time']
# p_conf_wifi_AP1 = p_conf_wifi['AP1']
# p_conf_wifi_AP2 = p_conf_wifi['AP2']
# p_conf_wifi_AP3 = p_conf_wifi['AP3']
# p_conf_wifi_AP4 = p_conf_wifi['AP4']
# p_conf_wifi_AP5 = p_conf_wifi['AP5']
# p_conf_wifi_incorrectPsk = p_conf_wifi['incorrectPsk']
# p_conf_wifi_hiddenSSID = p_conf_wifi['hiddenSSID']
# p_conf_wifi_specialSSID = p_conf_wifi['specialSSID']
#
# logging.info(f'wifi init p_conf_wifi_repeat_count:{p_conf_wifi_repeat_count}')
# logging.info(f'wifi init p_conf_wifi_test_time:{p_conf_wifi_test_time}')
# logging.info(f'wifi init p_conf_wifi_AP1:{p_conf_wifi_AP1}')
# logging.info(f'wifi init p_conf_wifi_AP2:{p_conf_wifi_AP2}')
# logging.info(f'wifi init p_conf_wifi_AP3:{p_conf_wifi_AP3}')
# logging.info(f'wifi init p_conf_wifi_AP4:{p_conf_wifi_AP4}')
# logging.info(f'wifi init p_conf_wifi_AP5:{p_conf_wifi_AP5}')
# logging.info(f'wifi init p_conf_wifi_incorrectPsk:{p_conf_wifi_incorrectPsk}')
# logging.info(f'wifi init p_conf_wifi_hiddenSSID:{p_conf_wifi_hiddenSSID}')
# logging.info(f'wifi init p_conf_wifi_specialSSID:{p_conf_wifi_specialSSID}')