import pytest
from lib.common.playback.DRM import DRM
import time
import logging
from lib.OTT.S905X4.Exoplayer_json_read import read_json

drm = DRM()
res = read_json()


class Test_057_Secure_OS:

    # @pytest.mark.skip
    def test_playback(self):
        # back
        drm.back()
        drm.set_ott_flag()
        drm.playback()
        drm.permission.permission_check()
        drm.u().d2(text="SAMPLE EXOPLAYER").click()
        time.sleep(2)
        for video_name, video_samples in res.items():
            drm.listed = False
            drm.skip_video = False
            for video_sample in video_samples:
                if drm.skip_video is True:
                    break
                drm.during_video = False
                video_sample_name = video_sample['name']
                video_sample_vdec = video_sample['vdec']
                if drm.player(video_name, video_sample_name, video_sample_vdec):
                    assert True
                else:
                    assert False
        # back to home
        drm.back()
