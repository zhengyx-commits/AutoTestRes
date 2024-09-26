import logging
import os
import re
import subprocess
from time import sleep

import allure
import pytest
from lib.common.playback.MultiMediaPlayer import MultiPlayer
from lib.common.checkpoint.PlayerCheck_Iptv import PlayerCheck_Iptv
from tools.yamlTool import yamlTool


multi = MultiPlayer()
config_yaml = yamlTool(os.getcwd() + '/config/config_ott_hybrid.yaml')
wifi = config_yaml.get_note("outside_wifi")
wifi_name = wifi["name"]
wifi_pwd = wifi["pwd"]


class Common_Playcontrol_Case:
    def __init__(self, playerNum=1):
        self.player_check = PlayerCheck_Iptv(playerNum=playerNum)
        self.forget_outside_wifi()

    @allure.step("Check switch window")
    def switch_pip_2_window(self):
        # switch window
        cmd = 'am broadcast -a multimediaplayer.test ' + '--es command ' + 'switch_window' + ' --ei source_window_id ' + '0 ' + '--ei target_window_id ' + '1'
        print(cmd)
        multi.send_cmd(cmd)
        assert self.player_check.check_switchWindow(logFilter="logcat -s AmlMultiPlayer", focused_playerNum=2)[
            0], "switch window failed"
        cmd = 'am broadcast -a multimediaplayer.test ' + '--es command ' + 'switch_window' + ' --ei source_window_id ' + '1 ' + '--ei target_window_id ' + '0'
        multi.send_cmd(cmd)
        # switch window to 1
        assert self.player_check.check_switchWindow(logFilter="logcat -s AmlMultiPlayer", focused_playerNum=1)[
            0], "switch window failed"

    @allure.step("Check switch window")
    def switch_pip_4_window(self):
        p_window_target = 1
        while p_window_target < 4:
            p_window_base = 0
            cmd = 'am broadcast -a multimediaplayer.test ' + '--es command ' + 'switch_window' + ' --ei source_window_id ' + f'{p_window_base} ' + '--ei target_window_id ' + f'{p_window_target} '
            logFilter = "logcat -s AmlMultiPlayer"
            multi.send_cmd(cmd)
            assert self.player_check.check_switchWindow(logFilter=logFilter, focused_playerNum=p_window_target,
                                                        replace_window=p_window_base)[0], "switch window failed"

            multi.send_cmd(cmd)
            assert self.player_check.check_switchWindow(logFilter=logFilter, focused_playerNum=p_window_base,
                                                        replace_window=p_window_target)[
                0], "switch window failed"
            p_window_target += 1

    def pause_resume_seek_stop(self, **kwargs):
        # pause
        pause_cmd = multi.PAUSE_CMD
        multi.send_cmd(pause_cmd)
        assert self.player_check.check_pause(**kwargs)[0], "playback pause failed"

        # resume
        resume_cmd = multi.RESUME_CMD
        multi.send_cmd(resume_cmd)
        assert self.player_check.check_resume(**kwargs)[0], "playback resume failed"

        # seek
        seek_cmd = multi.SEEK_CMD
        multi.send_cmd(seek_cmd)
        assert self.player_check.check_seek(**kwargs)[0], "playback seek failed"

        # stop
        stop_cmd = multi.STOP_CMD
        multi.send_cmd(stop_cmd)
        assert self.player_check.check_stopPlay(**kwargs)[0], "stop playback failed"

    def connect_outside_wifi(self):
        count = 0
        connect_network_cmd = f"cmd wifi connect-network {wifi_name} wpa2 {wifi_pwd}"
        while count < 3:
            rc, connect_network_res = multi.run_shell_cmd(connect_network_cmd)
            if "initiated" in connect_network_res:
                logging.debug("Connect wifi successfully!")
                break
            else:
                logging.info("Connect wifi failed! try again!")
                count += 1
        sleep(2)

    def set_wifi_disabled(self):
        wifi_disabled_cmd = "cmd wifi set-wifi-enabled disabled"
        multi.send_cmd(wifi_disabled_cmd)
        rc, wifi_disabled_res = multi.run_shell_cmd('ifconfig')
        if 'wlan0' not in wifi_disabled_res:
            logging.info("set wifi disabled successfully!")
        sleep(2)

    def set_wifi_enabled(self):
        wifi_enabled_cmd = "cmd wifi set-wifi-enabled enabled"
        multi.send_cmd(wifi_enabled_cmd)
        if 'wlan0' in multi.run_shell_cmd('ifconfig')[1]:
            self.connect_outside_wifi()
        check_wifi_count = 0
        while check_wifi_count <= 3:
            rc, wifi_enabled_res = multi.run_shell_cmd('ifconfig')
            id_address = re.findall(r'inet addr:(.*?)Bcast', wifi_enabled_res)
            if '10.18' in ''.join(i for i in id_address):
                logging.info("Outside wifi has connected!")
                break
            else:
                check_wifi_count += 1
                sleep(2)

    def forget_outside_wifi(self):
        list_networks_cmd = "cmd wifi list-networks"
        rc, networkID = multi.run_shell_cmd(list_networks_cmd)
        if networkID == "No networks":
            logging.info("has no wifi connect")
        else:
            network_Id = re.findall("\n(.*?) ", networkID)
            forget_wifi_cmd = "cmd wifi forget-network {}".format(int(network_Id[0]))
            rc, forget_wifi_res = multi.run_shell_cmd(forget_wifi_cmd)
            if "successful" in forget_wifi_res:
                logging.info(f"Network id {network_Id[0]} closed")
            else:
                logging.info(f"Network id {network_Id[0]} not found")
        sleep(5)
