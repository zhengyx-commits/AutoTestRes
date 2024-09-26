import pytest
import logging
from lib.common.playback.LocalPlayer import LocalPlayer
from lib.common.tools.LoggingTxt import log
from .. import config_yaml


p_conf_localplay_config = config_yaml.get_note('conf_localplay')
p_conf_uuid = p_conf_localplay_config.get('uuid')
p_conf_path = p_conf_localplay_config.get('path')

# @pytest.mark.skip
@pytest.mark.flaky(reruns=3)
def test_localplay():
    logging.info('test_localplay start')

    # create LocalPlayer
    local_player = LocalPlayer(p_conf_uuid, p_conf_path, play_from_list=True)
    if pytest.target.get("prj") == "iptv_product_line_p_yuv" or pytest.target.get("prj") == "iptv_product_line_r_yuv":
        local_player.install_apk('apk/VideoPlayerP.apk')
    else:
        local_player.install_apk('apk/VideoPlayer.apk')
    local_player.set_up(yuv_able=True, drop_check_able=False, video_player_monitor_enable=True, random_seek_enable=False,
                      play_3d_enable=False, av_sync_chk_enable=False)

    # start play
    local_player.startPlay()

    # close yuv
    if local_player.yuv_enable:
        local_player.video_player_monitor.yuv.close_yuv()

    logging.info('test_localplay finish')
    assert True if log.check_result_error() == 'Pass' else False
