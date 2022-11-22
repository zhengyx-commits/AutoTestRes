#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2021/12/30 11:05
# @Author  : chao.li
# @Site    :
# @File    : RouterControl.py
# @Software: PyCharm


import time
from abc import ABCMeta, abstractmethod
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from tools.yamlTool import yamlTool
import os
from tools.RouterControl.AsusRouter.AsusRouterConfig import ConfigError


class RouterControl(metaclass=ABCMeta):

    def __init__(self):
        ...

    @abstractmethod
    def login(self):
        '''
        login in router
        :return: None
        '''
        ...

    @abstractmethod
    def change_setting(self, router):
        '''
        change the router setting
        @param router: router info
        @return:
        '''
        ...

    @abstractmethod
    def reboot_router(self):
        '''
        reboot router
        @return:
        '''
        ...


class RouterTools(RouterControl):

    def __init__(self, router_info):
        # self.yaml_info = yamlTool(os.getcwd() + f'/config/router_tool/{router_type.split("_")[0]}_xpath.yaml')
        self.router_type = router_info.split("_")[0]
        self.router_info = router_info
        self.yaml_info = yamlTool(
            f'/Users/coco/Automation/AutoTestRes/scripts/python/config/router_tool/{self.router_type}_xpath.yaml')
        self.driver = webdriver.Chrome()
        self.xpath = self.yaml_info.get_note(self.router_type)
        self.address = self.xpath['address']
        self.driver.get(self.address)

    def login(self):
        '''
        login in router
        @return:
        '''
        # input username
        self.driver.find_element(By.ID, self.xpath['username_element']).send_keys(self.xpath['account'])
        # input passwd
        self.driver.find_element(By.NAME, self.xpath['password_element']).click()
        self.driver.find_element(By.NAME, self.xpath['password_element']).send_keys(self.xpath['passwd'])
        # click login
        self.driver.find_element(By.XPATH, self.xpath['signin_element']).click()
        # wait for login in done
        WebDriverWait(driver=self.driver, timeout=10, poll_frequency=0.5).until(
            EC.presence_of_element_located((By.ID, self.xpath['signin_done_element'])))
        time.sleep(1)

    def change_setting(self, router):
        ...

    def reboot_router(self):
        '''
        reboot router
        @return:
        '''
        self.driver.execute_script('reboot()')
        self.driver.switch_to.alert.accept()
        if self.router_info == 'asus_86u':
            WebDriverWait(self.driver, 180).until(
                EC.visibility_of_element_located((By.XPATH, self.xpath['wait_reboot_element']['asus_86u']))
            )
        elif self.router_info == 'asus_88u':
            WebDriverWait(self.driver, 180).until(
                EC.visibility_of_element_located((By.XPATH, self.xpath['wait_reboot_element']['asus_88u']))
            )
        self.driver.quit()

    def change_band(self, band):
        '''
        select band
        @param band:
        @return:
        '''
        bind_select = Select(self.driver.find_element(By.XPATH, self.xpath['band_element']))
        bind_select.select_by_visible_text(band)

    def change_wireless_mode(self, mode):
        '''
        select mode
        @param mode:
        @return:
        '''
        wireless_mode_select = Select(
            self.driver.find_element(By.XPATH, self.xpath['wireless_mode_element']))
        wireless_mode_select.select_by_visible_text(mode)

    def change_ssid(self, ssid):
        '''
        set ssid
        @param ssid:
        @return:
        '''
        self.driver.find_element(By.ID, self.xpath['ssid_element']).clear()
        self.driver.find_element(By.ID, self.xpath['ssid_element']).send_keys(ssid)

    def change_hide_ssid(self, status):
        ...

    def change_channel(self, index):
        '''
        change channel
        @param index: should be html source code
        @return:
        '''
        print(index)
        self.driver.find_element(By.XPATH, self.xpath['channel_regu_element'].format(index)).click()

    def change_bandwidth(self, bandwidth):
        '''
        select bandwith
        @param bandwith:
        @return:
        '''
        bandwidth_select = Select(self.driver.find_element(By.XPATH, self.xpath['bandwidth_element']))
        bandwidth_select.select_by_visible_text(bandwidth)

    def change_authentication_method(self, index):
        '''
        change authentication_method
        @param index: should be html source code
        @return:
        '''
        self.driver.find_element(By.XPATH, self.xpath['authentication_method_regu_element'].format(index)).click()

    def change_wep_encrypt(self, index):
        '''
        change wep encrypt
        @param index:
        @return:
        '''
        self.driver.find_element(By.XPATH, self.xpath['wep_encrypt_regu_element'].format(index)).click()

    def change_wpa_encrypt(self, index):
        '''
        change wpa encrypt
        @param index:
        @return:
        '''
        self.driver.find_element(By.XPATH, self.xpath['wpa_encrypt_regu_element'].format(index)).click()

    def change_passwd_index(self, index):
        '''
        change passwd index
        @param passwd_index: should be html source code
        @return:
        '''
        self.driver.find_element(By.XPATH, self.xpath['passwd_index_regu_element'].format(index)).click()

    def change_wep_passwd(self, passwd):
        '''
        change wep passwd
        @param passwd:
        @return:
        '''
        self.driver.find_element(By.ID, self.xpath['wep_passwd_element']).clear()
        self.driver.find_element(By.ID, self.xpath['wep_passwd_element']).send_keys(passwd)

    def change_wpa_passwd(self, passwd):
        '''
        change wpa passwd
        @param passwd:
        @return:
        '''
        if self.router_info == 'asus_86u':
            self.driver.find_element(By.XPATH, self.xpath['wpa_passwd_element']['asus_86u']).clear()
            self.driver.find_element(By.XPATH, self.xpath['wpa_passwd_element']['asus_86u']).send_keys(passwd)
        elif self.router_info == 'asus_88u':
            self.driver.find_element(By.XPATH, self.xpath['wpa_passwd_element']['asus_88u']).clear()
            self.driver.find_element(By.XPATH, self.xpath['wpa_passwd_element']['asus_88u']).send_keys(passwd)
        else:
            raise ConfigError('No such router info')

    def change_protect_frame(self, frame):
        '''
        change protect frame
        @param frame: should be html source code
        @return:
        '''
        self.driver.find_element(By.XPATH, self.xpath['protect_frame_regu_element'].format(frame)).click()

    def apply_setting(self):
        '''
        click apply button
        @return:
        '''
        self.driver.find_element(By.ID, self.xpath['apply_element']).click()

    def click_alert(self):
        try:
            self.driver.switch_to.alert.accept()
        except Exception as e:
            ...

    def wait_setting_done(self):
        WebDriverWait(self.driver, 20).until_not(
            #     //*[@id="loadingBlock"]/tbody/tr/td[2]
            EC.visibility_of_element_located((By.XPATH, self.xpath['setting_load_element']))
        )
        time.sleep(2)

    # def __del__(self):
    #     self.driver.quit()
