#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/4/19 2022/4/19
# @Author  : yongbo.shao
# @Site    : SH #5
# @File    : MediaCheck_Keywords.py
# @Email   : yongbo.shao@amlogic.com
# @Software: PyCharm

class MediaCheckKeywords:
    # start play
    START_KEYWORDS = ["[sourceffmpeg_info.cpp][get_ffmpeg_streaminfo][246 ]duration:332",
                      "AML_MP_PLAYER_EVENT_VIDEO_CHANGED"]
    START2PLAYER_KEYWORDS = ["[sourceffmpeg_info.cpp][get_ffmpeg_streaminfo][246 ]duration:332",
                             "[sourceffmpeg_info.cpp][get_ffmpeg_streaminfo][246 ]duration:332",
                             "AML_MP_PLAYER_EVENT_VIDEO_CHANGED",
                             "AML_MP_PLAYER_EVENT_VIDEO_CHANGED"]
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
                             "changeStatus:Prepared->Playing",
                             "changeStatus:Prepared->Playing",
                             "changeStatus:Prepared->Playing",
                             "changeStatus:Prepared->Playing"]
    # pause
    PAUSE_KEYWORDS = ["PauseVideoDecoding finished",
                      "PauseAudioDecoding finished"]

    # resume
    RESUME_KEYWORDS = ["ResumeVideoDecoding ResumeVideoDecoding finished",
                       "ResumeAudioDecoding finished"]

    # stop
    STOP_KEYWORDS = ["StopVideoDecoding end response", "StopAudioDecoding response"]

    # seek
    SEEK_KEYWORDS = ["ObFSM_SEEK_START::SeekOB_started", "ObLOOP_SEEK_COMPLETE::SeekOB_seek_started"]
    SEEK2_KEYWORDS = ["[MediaPlayerBase_1] changeStatus:Playing->Seeking"]
    SEEK3_KEYWORDS = ["[MediaPlayerBase_2] changeStatus:Playing->Seeking"]
    SEEK4_KEYWORDS = ["[MediaPlayerBase_3] changeStatus:Playing->Seeking"]

    # audio channelnum
    AUDIO_CHANNEL_NUM_KEYWORDS = ["amlsource: [ReportSTBOB.cpp:257][handle][ReportProbe] [STB-COMMON] Audio numChannels: 2"]

    # switch audio
    SWITCH_AUDIO_KEYWORDS = ["StopAudioDecoding in",
                             "StartAudioDecoding",
                             "[evt] AM_TSPLAYER_EVENT_TYPE_AUDIO_CHANGED"]

    # switch subtitle
    SWITCH_SUBTITLE_KEYWORDS = [
        "AmlMpPlayerImpl_0 [switchSubtitleTrack:578] new spid: 0x106, fmt:AML_MP_SUBTITLE_CODEC_DVB"]

    # switch channel
    SWITCH_CHANNEL_KEYWORDS = ["AML_MP_PLAYER_EVENT_VIDEO_CHANGED"]

    # speed
    SPEED_KEYWORDS = ["AmlMpPlayerImpl_1 [setPlaybackRate:543] rate:2.000000"]

    # v4lvideo
    V4LVIDEO_KEYWORDS = ["10-11 11:08:21.859     0     0 I [   70.404550@3]  v4lvideo: provider name: vdec.h265.00"]

    # stuck
    STUCK_KEYWORDS = ["get m_audiopolicy=4=HOLD",
                      "[AUT]playerNum:1;videoOutFps:24.93;videoDropFps:0.00[AUT_END]",
                      "[AUT]playerNum:1;outRealTime:957f2;r-c:58 ms;r-last:40 ms[AUT_END]",
                      "08-18 22:49:59.836  5125  5169 I AmCodecVDA: [AUT-INFO][tsplayer-checkin][id:1][pts:2328(100000us)][checkin-size:1626][offset:0x0]",
                      "08-18 22:49:59.967  5125  5170 I AmCodecVDA: [AUT-INFO][tsplayer-checkout][id:1][duration:c80][offset:2e5e)][pts:28b0a(166666)]",
                      "08-18 22:50:01.095     0     0 I [ 2658.739341@3]  vc: [0]received_cnt=6,new_cnt=1,i=0,z=0,omx_index=2, fence_fd=22, fc_no=882, index_disp=2,pts=13743895359070(0xc8000002e5e), index=771, video_id=1",
                      "09-29 15:53:54.621   390  3928 D MesonHwc: [updateVtBuffer] [0] [1043] mVtBufferFd(35) timestamp (11979308318 us) expectedPresentTime(11979315535 us) diffAdded(16644 us) shouldPresent:1, queueFrameSize:2",
                      "10-11 06:18:32.573 I/TsRenderer(  525): [AUT-INFO][mediasync-leave][id:18][pts:1ca3a7ddc(85419980411us)][timestampNs:53630091393us][count:302]",
                      "09-26 14:56:31.112   339  3439 W audio_hw_primary: [aml_alsa_output_write_new:954] format =0x24000000 alsa underrun",
                      "10-12 10:04:44.669 I/aml_audio_nonms12_render(  387): [AUT-TEST] pes_pts: 3480, frame_pts: 3480, pcm[len:4096, dur:21ms, total_dur:21ms].",
                      "08-18 22:49:59.947     0     0 W [ 2657.591051@0]  0: post_video_frame: index 0 poc 0 frame_type 8 dur 3200 type 9000 pts 0(0x0), pts64 13743895347206(0xc8000000006) ts 0(0x0) video_id 1",
                      "10-19 10:43:33.469 W/[14741.911784@0]  0(    0): [prepare_display_buf] pts: 64100000028 video_id 10",
                      "10-11 15:18:58.012 I/aml_audio_nonms12_render(  387): [AUT-TEST] frame_pts:3480, output_pts:1eb4, latency:62 ms."]

    # switch window when playerNum = 2
    FOCUSED2PLAYER_KEYWORDS = ["[MediaPlayerProxy_1] surfaceChanged: SurfaceHolder@20615340; width=1920; height=1080",
                               "[MediaPlayerProxy_0] surfaceChanged: SurfaceHolder@198126720; width=640; height=360"]
    FOCUSED1PLAYER_KEYWORDS = ["[MediaPlayerProxy_0] surfaceChanged: SurfaceHolder@20615340; width=1920; height=1080",
                               "[MediaPlayerProxy_1] surfaceChanged: SurfaceHolder@198126720; width=640; height=360"]

    # switch window when playerNum = 4
    FOCUSED_PLAYER_KEYWORDS_2_1 = ["[MediaPlayerProxy_1] surfaceChanged: SurfaceHolder@20615340; width=1280; height=720",
                                   "[MediaPlayerProxy_0] surfaceChanged: SurfaceHolder@198126720; width=640; height=360"]
    FOCUSED_PLAYER_KEYWORDS_1_2 = ["[MediaPlayerProxy_0] surfaceChanged: SurfaceHolder@20615340; width=1280; height=720",
                                   "[MediaPlayerProxy_1] surfaceChanged: SurfaceHolder@198126720; width=640; height=360"]
    FOCUSED_PLAYER_KEYWORDS_3_1 = ["[MediaPlayerProxy_2] surfaceChanged: SurfaceHolder@20615340; width=1280; height=720",
                                   "[MediaPlayerProxy_0] surfaceChanged: SurfaceHolder@198126720; width=640; height=360"]
    FOCUSED_PLAYER_KEYWORDS_1_3 = ["[MediaPlayerProxy_0] surfaceChanged: SurfaceHolder@20615340; width=1280; height=720",
                                   "[MediaPlayerProxy_2] surfaceChanged: SurfaceHolder@198126720; width=640; height=360"]
    FOCUSED_PLAYER_KEYWORDS_4_1 = ["[MediaPlayerProxy_3] surfaceChanged: SurfaceHolder@20615340; width=1280; height=720",
                                   "[MediaPlayerProxy_0] surfaceChanged: SurfaceHolder@198126720; width=640; height=360"]
    FOCUSED_PLAYER_KEYWORDS_1_4 = ["[MediaPlayerProxy_0] surfaceChanged: SurfaceHolder@20615340; width=1280; height=720",
                                   "[MediaPlayerProxy_3] surfaceChanged: SurfaceHolder@198126720; width=640; height=360"]
    NO_AUDIO_KEYWORDS = ["get m_audiopolicy=4=HOLD"]
    ################################
    MEDIASYNC_KEYWORDS = ["[AUT]playerNum:1;avDiff:45;audioDiff:94;[AUT_END]"]
    R_MEDIASYNC_KEYWORDS = ["NU-AmNuPlayerRenderer: video late by 145333616 us (145.33 secs)"]
    TSYNC_KEYWORDS = [
        "I kernel  :  [68704.991449@0] VIDEO_TSTAMP_DISCONTINUITY failed, vpts diff is small, param:0x736cd4, oldpts:0x7366f8, pcr:0x916671"]
    ABNORMAL_KEYWORDS = ["binder: undelivered transaction 3137485, process died",
                         "newStatus=Error",
                         "get_buffer() failed",
                         "VID: store VD0 path_id changed",
                         "dim: err",
                         "tombstoned: received crash request for pid",
                         "amcodec : call AMSTREAM_IOC_GET_MVDECINFO failed",
                         "MadDecoder: decoding error",
                         "Unexpected EOF",
                         "Kernel panic - not syncing:",
                         "PC is at dump_throttled_rt_tasks",
                         "AML_MP_PLAYER_EVENT_DATA_LOSS"]

    ONE_WAY_IN_TWO_DISPLAY = ['0', '0', '1920', '1080']
    TWO_WAY_IN_TWO_DISPLAY = ['1260', '700', '1900', '1060']

    MULTIPLAYER_LOGCAT = "logcat -s AmlMultiPlayer"
    AMP_LOGCAT = "logcat -s Aml_MP"
    PAUSE_RESUME_LOGCAT = "logcat -s TsPlayer"
    STOP_LOGCAT = "logcat -s TsPlayer"
    SEEK_LOGCAT = "logcat -s amlsource AmlMultiPlayer"
    SWITCH_CHANNEL_LOGCAT = "logcat -s Aml_MP AmlMultiPlayer"
    SWITCH_AUDIO_LOGCAT = "logcat -s Aml_MP TsPlayer amlsource"
    AUDIO_CHNUM_LOGCAT = "logcat -s amlsource"
    TSPLAYER_LOGCAT = "logcat -s TsPlayer"
    MULTI_TAG_LOGCAT = "logcat -b all"
    MEDIASYNC_LOGCAT = "logcat -s AmMediaSync"
    KERNEL_LOGCAT = "logcat -b kernel"
    AMLSOURCE_LOGCAT = "logcat -s amlsource"

