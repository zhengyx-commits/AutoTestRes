import pytest
from lib.common.playback.DRM import DRM
import time
import logging
from lib.OTT.S905X4.Exoplayer_json_read import read_json
from tests.OTT_Sanity_Ref import config_yaml

drm = DRM()
res = read_json()
p_video_info = config_yaml.get_note('conf_secure_os')
p_video_name = p_video_info['name']

logging.info(f'p_video_name : {p_video_name}')


class Test_057_Secure_OS:

    # @pytest.mark.skip
    def test_playback(self):
        # back
        drm.set_ott_flag()
        drm.playback()
        drm.permission.permission_check()
        drm.wait_and_tap('SETTINGS', 'text')
        drm.keyevent(23)
        time.sleep(2)
        drm.wait_and_tap("ExoPlayer", 'text')
        drm.keyevent(23)
        time.sleep(2)
        drm.u().d2(text="SAMPLE EXOPLAYER").click()
        time.sleep(2)
        for video_name, video_samples in res.items():
            drm.listed = False
            drm.skip_video = False
            if video_name not in p_video_name:
                continue
            for video_sample in video_samples:
                if drm.skip_video is True:
                    break
                drm.during_video = False
                video_sample_name = video_sample['name']
                video_sample_vdec = video_sample['vdec']
                if not drm.player(video_name, video_sample_name, video_sample_vdec):
                    logging.info(f'{video_name} : {video_sample_name}  play error !!!')
                    assert False

        # back to home
        drm.back()
