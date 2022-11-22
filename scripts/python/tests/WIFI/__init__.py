from lib.common.system.ADB import ADB
import os
from tools.yamlTool import yamlTool
from collections import namedtuple
from lib.common.system.WIFI import WifiTestApk
import logging
import time
from tools.resManager import ResManager

adb = ADB()
# 禁止凌晨待机
adb.subprocess_run('settings put secure sys.settings.autoshutdown_time -1')

RUN_SETTING_ACTIVITY = 'am start -n com.android.tv.settings/.MainSettings'


def router_str(self):
    return f'{self.band} {self.ssid} {self.wireless_mode} {self.channel} {self.bandwidth} {self.authentication_method}'


fields = ['band', 'ssid', 'wireless_mode', 'channel', 'bandwidth', 'authentication_method', 'wpa_passwd', 'test_type',
          'protocol_type', 'wep_encrypt', 'passwd_index', 'wep_passwd', 'protect_frame', 'wpa_encrypt', 'hide_ssid']
Router = namedtuple('Router', fields, defaults=(None,) * len(fields))
Router.__str__ = router_str
# set install apk not be limited
if adb.run_shell_cmd('getprop sys.limit.install.app')[1] == "true":
    adb.run_shell_cmd('setprop sys.limit.install.app false')


def connect_wifi(router, type='', passwd='', hide=False):
    wifi = WifiTestApk()
    if 'com.example.wifiConnect' not in wifi.checkoutput('pm list package'):
        wifi.install_apk('apk/app-debug.apk')
        wifi.get_wifi_connect_permission()
    if int(wifi.getprop('ro.build.version.sdk')) >= 30 and type != 'NONE' and type != 'WEP':
        logging.info('use cmd wifi connect')
        if passwd == '':
            wifi.checkoutput(wifi.CMD_WIFI_CONNECT_OPEN.format(router.ssid))
        else:
            wifi.checkoutput(wifi.CMD_WIFI_CONNECT.format(router.ssid, type, passwd))
    else:
        logging.info('use apk connect')
        cmd = wifi.WIFI_CONNECT_COMMAND_REGU.format(router.ssid)
        if passwd:
            # logging.info(passwd)
            cmd += wifi.WIFI_CONNECT_PASSWD_REGU.format(passwd)
        if hide == True:
            cmd += ' --ez hide_ssid true'
        if type:
            cmd += f' -e type {type}'
        if not passwd and not type:
            cmd += ' -e type NONE'
        wifi.checkoutput(cmd)
    start = time.time()
    while not wifi.ping(hostname="192.168.50.1"):
        time.sleep(1)
        if time.time() - start > 60:
            raise TimeoutError('Connect over time')


def disconnect_wifi():
    wifi = WifiTestApk()
    wifi.checkoutput(wifi.WIFI_DISCONNECT_COMMAND)


def forget_wifi():
    wifi = WifiTestApk()
    wifi.checkoutput(wifi.WIFI_CONNECT_ACTIVITY + wifi.WIFI_FORGET_WIFI_STR)
    wifi.home()
    wifi.app_stop(wifi.WIFI_CONNECT_PACKAGE)
    time.sleep(3)


config_yaml = yamlTool(os.getcwd() + '/config/config_wifi.yaml')
