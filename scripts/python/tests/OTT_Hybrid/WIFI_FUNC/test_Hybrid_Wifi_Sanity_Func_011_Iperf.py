import logging
import subprocess
import time
import _io
import os
import signal
import pytest

from lib.common.system.WIFI import WifiTestApk
from lib.common.playback.Youtube import YoutubeFunc
from . import *

wifi = WifiTestApk()
youtube = YoutubeFunc()
p_conf_wifi_test_time = p_conf_wifi['test_time']
test_time = p_conf_wifi_test_time * 60

p_conf_wifi_AP5 = p_conf_wifi['AP5']
p_conf_wifi_AP5_ssid = p_conf_wifi_AP5[0]['ssid']
p_conf_wifi_AP5_pwd = p_conf_wifi_AP5[0]['pwd']
# logging.info(f'test wifi play online p_conf_wifi_AP5_ssid:{p_conf_wifi_AP5_ssid}, p_conf_wifi_AP5_pwd:{p_conf_wifi_AP5_pwd}')

def checkoutput(command):
    logging.info(f'checkoutput {command}')
    return subprocess.check_output(command, shell=True, encoding='utf-8')


def server_on(command, adb):
    if adb:
        command = f'adb -s {adb} shell ' + command
    tx_log = open('tx_log.log', 'w')
    logging.info(f'server_on {command}')
    popen = subprocess.Popen(command.split(), stdout=tx_log)
    return popen, tx_log


def server_off(popen, file):
    if not isinstance(popen, subprocess.Popen):
        logging.warning('pls pass in the popen object')
        return 'pls pass in the popen object'
    if not isinstance(file, _io.TextIOWrapper):
        logging.warning('pls pass in the stream object')
        return 'pls pass int the stream object'
    os.kill(popen.pid, signal.SIGTERM)
    popen.terminate()
    file.close()


@pytest.fixture(scope='function', autouse=True)
def wifi_setup_teardown():
    wifi.wifi_setup()
    wifi.push('res/wifi/iperf', '/data/')
    wifi.checkoutput('chmod a+x /data/iperf')
    # wifi.connect_check('wpa2') if not wifi.check_reconnect('wpa2') else ...
    yield
    wifi.wifi_disconnect()


def test_PlayOnline():
    wifi.connect_check("wpaAndwpa2", p_conf_wifi_AP5_ssid, p_conf_wifi_AP5_pwd)
    time_ticks_begin = time.time()
    youtube.start_youtube()
    while True:
        localtime = time.asctime(time.localtime(time.time()))
        logging.info(f"local time is {localtime}")
        time_ticks_end = time.time()
        logging.info(f"time ticks is {time_ticks_end}")

        # rx test
        dut_ip = wifi.checkoutput('ifconfig wlan0 |egrep -o "inet [^ ]*"|cut -f 2 -d :').strip()
        logging.info(f'dut_ip:{dut_ip}')
        # pc_ip = checkoutput('ifconfig en7 |egrep -o "inet [^ ]*"|cut -f 2 -d " "').strip()
        pc_ip = pytest.config.get('broadlink').get('pc_ip')
        logging.info(f'pc_ip:{pc_ip}')
        popen, file = server_on(wifi.IPERF_SERVER, '')
        wifi.checkoutput('./data/' + wifi.IPERF_CLIENT.format(pc_ip))
        server_off(popen, file)
        res = checkoutput(f'cat {file.name} |tail -n 2')
        logging.info('-' * 50)
        logging.info(f'RX result {res}')

        # tx text
        popen, file = server_on('./data/' + wifi.IPERF_SERVER, wifi.serialnumber)
        checkoutput(wifi.IPERF_CLIENT.format(dut_ip))
        server_off(popen, file)
        res = checkoutput(f'cat {file.name} |tail -n 2')
        logging.info('-' * 50)
        logging.info(f'TX result {res}')

        if time_ticks_end - time_ticks_begin > test_time:
            break
    youtube.stop_youtube()
