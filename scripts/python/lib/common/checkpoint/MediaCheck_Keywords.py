#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/4/19 2022/4/19
# @Author  : yongbo.shao
# @Site    : SH #5
# @File    : MediaCheck_Keywords.py
# @Email   : yongbo.shao@amlogic.com
# @Software: PyCharm
import pytest


class MediaCheckKeywords:
    # start play, amp
    START_KEYWORDS = ["[sourceffmpeg_info.cpp][get_ffmpeg_streaminfo][246 ]duration:332",
                      "AM_TSPLAYER_EVENT_TYPE_FIRST_FRAME"]
    START2PLAYER_KEYWORDS = ["[sourceffmpeg_info.cpp][get_ffmpeg_streaminfo][246 ]duration:332",
                             "[sourceffmpeg_info.cpp][get_ffmpeg_streaminfo][246 ]duration:332",
                             "AM_TSPLAYER_EVENT_TYPE_FIRST_FRAME",
                             "AM_TSPLAYER_EVENT_TYPE_FIRST_FRAME"]
    START3PLAYER_KEYWORDS = ["[sourceffmpeg_info.cpp][get_ffmpeg_streaminfo][246 ]duration:332",
                             "[sourceffmpeg_info.cpp][get_ffmpeg_streaminfo][246 ]duration:332",
                             "[sourceffmpeg_info.cpp][get_ffmpeg_streaminfo][246 ]duration:332",
                             "changeStatus:Prepared->Playing",
                             "changeStatus:Prepared->Playing",
                             "changeStatus:Prepared->Playing"]
    START4PLAYER_KEYWORDS = ["[sourceffmpeg_info.cpp][get_ffmpeg_streaminfo][246 ]duration:332",
                             "[sourceffmpeg_info.cpp][get_ffmpeg_streaminfo][246 ]duration:332",
                             "[sourceffmpeg_info.cpp][get_ffmpeg_streaminfo][246 ]duration:332",
                             "[sourceffmpeg_info.cpp][get_ffmpeg_streaminfo][246 ]duration:332",
                             "AM_TSPLAYER_EVENT_TYPE_FIRST_FRAME",
                             "AM_TSPLAYER_EVENT_TYPE_FIRST_FRAME",
                             "AM_TSPLAYER_EVENT_TYPE_FIRST_FRAME",
                             "AM_TSPLAYER_EVENT_TYPE_FIRST_FRAME"]
    # pause, tsplayer
    PAUSE_KEYWORDS = ["PauseVideoDecoding finished",
                      "PauseAudioDecoding finished"]

    # resume, tsplayer
    RESUME_KEYWORDS = ["ResumeVideoDecoding ResumeVideoDecoding finished",
                       "ResumeAudioDecoding finished"]

    # stop, tsplayer
    STOP_KEYWORDS = ["StopVideoDecoding end response", "StopAudioDecoding response"]

    # seek, amlsource
    SEEK_KEYWORDS = ["ObFSM_SEEK_START::SeekOB_started", "ObLOOP_SEEK_COMPLETE::SeekOB_seek_started"]
    SEEK2_KEYWORDS = ["[MediaPlayerBase_1] changeStatus:Playing->Seeking"]
    SEEK3_KEYWORDS = ["[MediaPlayerBase_2] changeStatus:Playing->Seeking"]
    SEEK4_KEYWORDS = ["[MediaPlayerBase_3] changeStatus:Playing->Seeking"]

    # audio channelnum, amp
    AUDIO_CHANNEL_NUM_KEYWORDS = ["Audio numChannels"]

    # switch audio
    SWITCH_AUDIO_KEYWORDS = ["[SwitchAudioTrack]",
                             "new apid: 0x",
                             "StopAudioDecoding in",
                             "Am_AudioHalWrapper_OnStart ok"]

    # switch subtitle
    SWITCH_SUBTITLE_KEYWORDS = ["switchSubtitleTrack"]

    # switch channel
    SWITCH_CHANNEL_KEYWORDS = ["AM_TSPLAYER_EVENT_TYPE_FIRST_FRAME"]

    # speed
    SPEED_KEYWORDS = ["AmlMpPlayerImpl_1 [setPlaybackRate:543] rate:2.000000"]

    # v4lvideo
    V4LVIDEO_KEYWORDS = ["10-11 11:08:21.859     0     0 I [   70.404550@3]  v4lvideo: provider name: vdec.h265.00"]

    # black screen
    DATA_LOSS_KEYWORDS = ["AML_MP_PLAYER_EVENT_DATA_LOSS"]

    # stuck
    STUCK_KEYWORDS = {"audio_hold": "get m_audiopolicy=4=HOLD",
                      "tsplayer_checkin": "CheckinPtsSize -->size",
                      "tsplayer_checkout": "CheckoutPtsOffset -->offset",
                      "hwcomposer": ("updateVtBuffer", "shouldPresent:1"),
                      "mediasync": "onDrainTunnelVideoQueue (rend)",
                      "decoder_h264": "post_video_frame:index",
                      "decoder_h265": ("post_video_frame(type", "pts(", "video_id"),
                      "decoder_mpeg": "prepare_display_buf",
                      "audio_alsa": "alsa underrun",
                      "audio_pes_pts": ("pes_pts", "frame_pts"),
                      "audio_output_pts": ("frame_pts", "output_pts")
                      }

    STUCK_KEYWORDS_OTT = {"In PTS": ("AmlogicVideoDecoderAwesome", "In PTS"),
                          "EBD": "OMXNodeInstance: EBD",
                          "emptyBuffer": ("OMXNodeInstance", "emptyBuffer"),
                          "Out PTS": ("AmlogicVideoDecoderAwesome", "Out PTS", "TunnelMode"),
                          "FBD": "OMXNodeInstance: FBD",
                          "MediaCodec": ("[onReleaseOutputBuffer] render timeus", "drop pts"),
                          "VideoTunnelWraper": ("queueBuffer", ", count:")
                          }

    # switch window when playerNum = 2
    FOCUSED2PLAYER_KEYWORDS = ["[MediaPlayerProxy_1] surfaceChanged",
                               "[MediaPlayerProxy_0] surfaceChanged"]
    FOCUSED1PLAYER_KEYWORDS = ["[MediaPlayerProxy_0] surfaceChanged",
                               "[MediaPlayerProxy_1] surfaceChanged"]

    # switch window when playerNum = 4
    FOCUSED_PLAYER_KEYWORDS_2_1 = ["[MediaPlayerProxy_1]",
                                   "[MediaPlayerProxy_0]"]
    FOCUSED_PLAYER_KEYWORDS_1_2 = ["[MediaPlayerProxy_0]",
                                   "[MediaPlayerProxy_1]"]
    FOCUSED_PLAYER_KEYWORDS_3_1 = ["[MediaPlayerProxy_2]",
                                   "[MediaPlayerProxy_0]"]
    FOCUSED_PLAYER_KEYWORDS_1_3 = ["[MediaPlayerProxy_0]",
                                   "[MediaPlayerProxy_2]"]
    FOCUSED_PLAYER_KEYWORDS_4_1 = ["[MediaPlayerProxy_3]",
                                   "[MediaPlayerProxy_0]"]
    FOCUSED_PLAYER_KEYWORDS_1_4 = ["[MediaPlayerProxy_0]",
                                   "[MediaPlayerProxy_3]"]
    NO_AUDIO_KEYWORDS = ["get m_audiopolicy=4=HOLD"]
    ################################
    MEDIASYNC_KEYWORDS = ["[AUT]playerNum:1;avDiff:45;audioDiff:94;[AUT_END]"]
    OTT_MEDIASYNC_KEYWORDS = ["NU-AmNuPlayerRenderer: video late by 145333616 us (145.33 secs)"]
    TSYNC_KEYWORDS = [
        "I kernel  :  [68704.991449@0] VIDEO_TSTAMP_DISCONTINUITY failed, vpts diff is small, param:0x736cd4, oldpts:0x7366f8, pcr:0x916671"]
    ABNORMAL_KEYWORDS = ["newStatus=Error",
                         "get_buffer() failed",
                         "dim: err",
                         "tombstoned: received crash request for pid",
                         "Unexpected EOF",
                         "Kernel panic - not syncing:",
                         "PC is at dump_throttled_rt_tasks",
                         "OmxComponent::emptyThisBuffer failed",
                         "decoding failed"]

    ONE_WAY_IN_TWO_DISPLAY = ['0', '0', '1920', '1080']
    TWO_WAY_IN_TWO_DISPLAY = ['1260', '700', '1900', '1060']

    MULTIPLAYER_LOGCAT = "logcat -s AmlMultiPlayer"
    AMP_LOGCAT = "logcat -s Aml_MP"
    PAUSE_RESUME_LOGCAT = "logcat -s TsPlayer"
    STOP_LOGCAT = "logcat -s TsPlayer"
    SEEK_LOGCAT = "logcat -s amlsource AmlMultiPlayer"
    SWITCH_CHANNEL_LOGCAT = "logcat -s Aml_MP AmlMultiPlayer"
    SWITCH_AUDIO_LOGCAT = "logcat -s Aml_MP TsPlayer amlsource AmAudioHalWrapper"
    AUDIO_CHNUM_LOGCAT = "logcat -s amlsource"
    TSPLAYER_LOGCAT = "logcat -s TsPlayer"
    MULTI_TAG_LOGCAT = "logcat -b all"
    MEDIASYNC_LOGCAT = "logcat -s AmMediaSync"
    KERNEL_LOGCAT = "logcat -b kernel"
    AMLSOURCE_LOGCAT = "logcat -s amlsource"
