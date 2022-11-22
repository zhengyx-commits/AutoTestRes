import pytest
import time
from lib.common.playback.MultiMediaPlayer import MultiPlayer
from lib.common.checkpoint.PlayerCheck import PlayerCheck

g_config_device_id = pytest.config['device_id']
multi = MultiPlayer(g_config_device_id)


class Common_Playcontrol_Case:
    def __init__(self, playerNum=1):
        self.player_check = PlayerCheck(playerNum=playerNum)
        
    def switch_pip_2_window(self):
        # switch window
        cmd = 'am broadcast -a multimediaplayer.test ' + '--es command ' + 'switch_window' + ' --ei source_window_id ' + '0 ' + '--ei target_window_id ' + '1'
        print(cmd)
        multi.send_cmd(cmd)
        assert self.player_check.check_switchWindow(logFilter="logcat -s AmlMultiPlayer", focused_playerNum=2)[0], "switch window failed"
        cmd = 'am broadcast -a multimediaplayer.test ' + '--es command ' + 'switch_window' + ' --ei source_window_id ' + '1 ' + '--ei target_window_id ' + '0'
        multi.send_cmd(cmd)
        # switch window to 1
        assert self.player_check.check_switchWindow(logFilter="logcat -s AmlMultiPlayer", focused_playerNum=1)[0], "switch window failed"

    def switch_pip_4_window(self):
        p_window_target = 1
        while p_window_target < 4:
            p_window_base = 0
            cmd = 'am broadcast -a multimediaplayer.test ' + '--es command ' + 'switch_window' + ' --ei source_window_id ' + f'{p_window_base} ' + '--ei target_window_id ' + f'{p_window_target} '
            logFilter = "logcat -s AmlMultiPlayer"
            print(cmd)
            multi.send_cmd(cmd)
            assert self.player_check.check_switchWindow(logFilter=logFilter, focused_playerNum=p_window_target,
                                                               replace_window=p_window_base)[0], "switch window failed"
            time.sleep(1)
            cmd = 'am broadcast -a multimediaplayer.test ' + '--es command ' + 'switch_window' + ' --ei source_window_id ' + f'{p_window_target} ' + '--ei target_window_id ' +     f'{p_window_base} '
            print(cmd)
            multi.send_cmd(cmd)
            assert self.player_check.check_switchWindow(logFilter=logFilter, focused_playerNum=p_window_base,
                                                               replace_window=p_window_target)[
                0], "switch window failed"
            p_window_target += 1
    
    def pause_resume_seek_stop(self):
        # pause
        pause_cmd = multi.PAUSE_CMD
        multi.send_cmd(pause_cmd)
        assert self.player_check.check_pause()[0], "playback pause failed"
    
        # resume
        resume_cmd = multi.RESUME_CMD
        multi.send_cmd(resume_cmd)
        assert self.player_check.check_resume()[0], "playback resume failed"
    
        # seek
        seek_cmd = multi.SEEK_CMD
        multi.send_cmd(seek_cmd)
        assert self.player_check.check_seek()[0], "playback seek failed"
    
        # stop
        stop_cmd = multi.STOP_CMD
        multi.send_cmd(stop_cmd)
        assert self.player_check.check_stopPlay()[0], "stop playback failed"

