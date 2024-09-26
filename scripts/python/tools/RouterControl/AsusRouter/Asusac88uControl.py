#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/3/22 16:17
# @Author  : chao.li
# @Site    :
# @File    : Asusac88uControl.py
# @Software: PyCharm


import logging
import time
from collections import namedtuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from tools.RouterControl.RouterControl import RouterTools
from tools.RouterControl.AsusRouter.AsusRouterConfig import Asus88uConfig, ConfigError


class Asusac88uControl():
    '''
    Asus ac88u router

    Attributes:

    '''

    def __init__(self):
        self.router_control = RouterTools('asus_88u')

    def login(self):
        '''
        login in router
        :return: None
        '''
        self.driver = webdriver.Chrome()
        self.driver.get(self.ADDRESS)
        self.driver.find_element(By.ID, 'login_username').send_keys(self.ACCOUNT)
        self.driver.find_element(By.NAME, 'login_passwd').click()
        self.driver.find_element(By.NAME, 'login_passwd').send_keys(self.PASSWD)
        self.driver.find_element(By.XPATH, '//*[@id="login_filed"]/div[8]').click()

        # 等待加载成功
        WebDriverWait(driver=self.driver, timeout=10, poll_frequency=0.5).until(
            EC.presence_of_element_located((By.ID, 'helpname')))
        time.sleep(1)

    def change_setting(self, router):
        '''
        set up wifi envrioment
        @param router: Router instance
        @return: status : boolean
        '''
        logging.info('Try to set router')
        try:
            self.router_control.login()
            self.router_control.driver.find_element(By.ID, 'Advanced_Wireless_Content_menu').click()
            # Wireless - General
            WebDriverWait(driver=self.router_control.driver, timeout=5, poll_frequency=0.5).until(
                EC.presence_of_element_located((By.ID, 'FormTitle')))

            # 修改 band
            if (router.band):
                if router.band not in Asus88uConfig.BAND_LIST: raise ConfigError('band element error')
                self.router_control.change_band(router.band)

            # 修改 wireless_mode
            if (router.wireless_mode):
                if router.wireless_mode not in Asus88uConfig.WIRELESS_MODE: raise ConfigError(
                    'wireless mode element error')
                self.router_control.change_wireless_mode(router.wireless_mode)

            # 修改 ssid
            if (router.ssid):
                self.router_control.change_ssid(router.ssid)

            # 修改 ssid 是否隐藏
            if (router.hide_ssid):
                if (router.hide_ssid) == '是':
                    self.router_control.driver.find_element(By.XPATH, ".//input[@type='radio' and @value='1']").click()
                elif (router.hide_ssid) == '否':
                    self.router_control.driver.find_element(By.XPATH, ".//input[@type='radio' and @value='0']").click()
            else:
                self.router_control.driver.find_element(By.XPATH, ".//input[@type='radio' and @value='0']").click()

            # 修改 channel //*[@id="WLgeneral"]/tbody/tr[11]/td/select
            # //*[@id="WLgeneral"]/tbody/tr[11]/td/select/option[1] 2.4G Auto
            # //*[@id="WLgeneral"]/tbody/tr[11]/td/select/option[14] 2.4G 13
            # //*[@id="WLgeneral"]/tbody/tr[11]/td/select/option[1] 5G Auto
            # //*[@id="WLgeneral"]/tbody/tr[11]/td/select/option[6] 5G 165
            if (router.channel):
                channel = str(router.channel)
                try:
                    channel_index = (
                        Asus88uConfig.CHANNEL_2_DICT[channel] if router.band == '2.4 GHz' else
                        Asus88uConfig.CHANNEL_5_DICT[channel])
                except ConfigError:
                    raise ConfigError('channel element error')
                # //*[@id="WLgeneral"]/tbody/tr[11]/td/select/option[22]
                self.router_control.change_channel(channel_index)

            # 修改 bandwidth
            if (router.bandwidth):
                if router.bandwidth not in \
                        {'2.4 GHz': Asus88uConfig.BANDWIDTH_2_LIST, '5 GHz': Asus88uConfig.BANDWIDTH_5_LIST}[
                            router.band]: raise ConfigError('bandwidth element error')
                self.router_control.change_bandwidth(router.bandwidth)

            # 修改 authentication_method
            # //*[@id="WLgeneral"]/tbody/tr[13]/td/div[1]/select/option[1]
            # //*[@id="WLgeneral"]/tbody/tr[13]/td/div[1]/select/option[5]
            if (router.authentication_method):
                try:
                    index = (Asus88uConfig.AUTHENTICATION_METHOD_DICT[router.authentication_method]
                             if router.wireless_mode != 'Legacy' else
                             Asus88uConfig.AUTHENTICATION_METHOD_LEGCY_DICT[router.authentication_method])
                except ConfigError:
                    raise ConfigError('authentication method element error')
                self.router_control.change_authentication_method(index)

            # 修改 wep_encrypt
            if (router.wep_encrypt):
                if router.wep_encrypt not in Asus88uConfig.WEP_ENCRYPT: raise ConfigError('wep encrypt elemenr error')
                self.router_control.change_wep_encrypt(Asus88uConfig.WEP_ENCRYPT[router.wep_encrypt])

            # 修改 wpa_encrypt
            if (router.wpa_encrypt):
                if router.wpa_encrypt not in Asus88uConfig.WPA_ENCRYPT: raise ConfigError('wpa encrypt elemenr error')
                self.router_control.change_wpa_encrypt(Asus88uConfig.WPA_ENCRYPT[router.wpa_encrypt])

            # 修改 passwd_index
            # //*[@id="WLgeneral"]/tbody/tr[17]/td/select/option[1]
            if (router.passwd_index):
                if router.passwd_index not in Asus88uConfig.PASSWD_INDEX_DICT: raise ConfigError(
                    'passwd index element error')
                self.router_control.change_passwd_index(router.passwd_index)

            # 修改 wep_passwd
            if (router.wep_passwd):
                self.router_control.change_wep_passwd(router.wep_passwd)

            # 修改 wpa_passwd
            if (router.wpa_passwd):
                self.router_control.change_wpa_passwd(router.wpa_passwd)

            # 修改 受保护的管理帧
            # //*[@id="WLgeneral"]/tbody/tr[26]/td/select/option[1]
            if (router.protect_frame):
                if router.protect_frame not in Asus88uConfig.PROTECT_FRAME: raise ConfigError(
                    'protect frame element error')
                self.router_control.change_protect_frame(self.PROTECT_FRAME[router.protect_frame])

            time.sleep(5)
            # 点击apply
            self.router_control.apply_setting()
            try:
                self.router_control.driver.switch_to.alert.accept()
                self.router_control.driver.switch_to.alert.accept()
            except Exception as e:
                ...
            WebDriverWait(self.router_control.driver, 20).until_not(
                #     //*[@id="loadingBlock"]/tbody/tr/td[2]
                EC.visibility_of_element_located((By.XPATH, '//*[@id="loadingBlock"]/tbody/tr/td[2]'))
            )
            time.sleep(2)
            logging.info('Router setting done')
            return True
        except Exception as e:
            logging.info('Router change setting with error')
            logging.info(e)
            return False
        finally:
            self.router_control.driver.quit()


# fields = ['band', 'ssid', 'wireless_mode', 'channel', 'bandwidth', 'authentication_method', 'wep_encrypt',
#           'passwd_index', 'wep_passwd', 'wpa_passwd', 'protect_frame', 'wpa_encrypt', 'hide_ssid']
# Router = namedtuple('Router', fields, defaults=[None, ] * len(fields))
# router = Router(band='5 GHz', ssid='ATC_ASUS_AX88U_5G', wireless_mode='Legacy', channel='100', bandwidth='20 MHz',
#                 authentication_method='Shared Key', hide_ssid='否', wep_encrypt='WEP-64bits', wep_passwd='12345')
# control = Asusac88uControl()
# # control.change_setting(router)
# control.router_control.login()
# control.router_control.reboot_router()
