# !/usr/bin python3
# -*- coding: utf-8 -*-
# @author     : jianhua.huang
# @software   : PyCharm
# @file       : test_OTT_Smoking_Func_01_DDR.py
# @Time       : 2023/1/03

from typing import List, Any
from lib.common.system.MemInfo import MemInfo
from tests.OTT_Sanity_Ref import *

adb = ADB()
mem = MemInfo()
p_conf_freeinfo = config_ott_sanity_yaml.get_note('conf_freeinfo')
p_conf_freeinfo_reference_totalmemory = p_conf_freeinfo['reference_totalmemory']
p_result_path = f'{pytest.result_dir}/../../ddr_emmc_info.log'


def test_020_ddrinfo():
    Free_info = mem.get_free_info()
    logging.info(Free_info)
    free_list: List[Any] = re.findall(r'(\d+\.?\d+)', Free_info, re.S)
    logging.debug(free_list)
    if free_list:
        logging.info(f'free_total_memory: {free_list[0]}G')
    free_number = float(free_list[0])
    f = open(p_result_path, 'a')
    f.write(f'ddr_free_number: {free_number}G')
    f.write('\n')
    f.close()
    assert (free_number > p_conf_freeinfo_reference_totalmemory)
