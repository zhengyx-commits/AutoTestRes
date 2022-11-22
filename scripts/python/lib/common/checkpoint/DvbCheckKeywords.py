#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/6/16
# @Author  : kejun.chen
# @Site    :
# @File    : DvbCheckKeywords.py
# @Email   : kejun.chen@amlogic.com
# @Software: PyCharm


class DvbCheckKeywords:
    # for check_search_ex
    SEARCH_EX_FILTER = 'logcat -s DtvkitDvbtSetup dtvkitserver'
    SEARCH_EX_KEYWORDS = ['DtvkitDvbtSetup: command = Dvbc.startSearchEx, args = \["network","KDG",true,"AUTO",0,0,0\]',
                          'dtvkitserver: IPC--> {"command": "Dvbc.startSearchEx", "json": \["network","KDG",true,"AUTO",0,0,0\]}']

    # for check_manual_search_by_freq
    MANUAL_SEARCH_BY_FREQ_FILTER = 'logcat -s DtvkitDvbtSetup dtvkitserver'
    MANUAL_SEARCH_BY_FREQ_KEYWORDS = ['DtvkitDvbtSetup: command = Dvbc.startManualSearchByFreq, args = \[true,false',
                                      'dtvkitserver: IPC--> {"command": "Dvbc.startManualSearchByFreq", "json": \[true,false']

    # for check_manual_search_by_id
    MANUAL_SEARCH_BY_ID_FILTER = 'logcat -s DtvkitDvbtSetup dtvkitserver'
    MANUAL_SEARCH_BY_ID_KEYWORDS = ['DtvkitDvbtSetup: command = Dvbc.startManualSearchById, args = \[true,0\]',
                                    'dtvkitserver: IPC--> {"command": "Dvbc.startManualSearchById, json:\[true,0\]']

    # for check_quick_scan
    QUICK_SCAN_FILTER = 'logcat -s DtvkitDvbtSetup dtvkitserver'
    QUICK_SCAN_KEYWORDS = ['DtvkitDvbtSetup: command = Dvbc.startSearchEx, args = \["quick","KDG",true,"AUTO",0,0,0\]',
                          'dtvkitserver: IPC--> {"command": "Dvbc.startSearchEx", "json": \["quick","KDG",true,"AUTO",0,0,0\]}']

    # for check_search_process
    SEARCH_PROCESS_FILTER = 'logcat -s DtvkitDvbtSetup'
    SEARCH_PROCESS_FILTER_DRIVER = 'echo state > /sys/class/dtvdemod/attr'
    SEARCH_PROCESS_KEYWORDS = ['DtvKitDvbtSetup：Search status “Searching 10%”']
    SEARCH_PROCESS_KEYWORDS_DRIVER = ['Lock Status: Unlocked']

    # for check_search_result
    SEARCH_RESULT_FILTER = 'logcat -s DtvkitDvbtSetup EpgSyncJobService DTVKIT_LOG'
    SEARCH_RESULT_FILTER_DRIVER = 'cat /sys/class/cxd2856/cxd2856_debug'
    # SEARCH_RESULT_KEYWORDS = [r'DTVKIT_LOG: TunerTask:\d+ 0: LOCKED',
    SEARCH_RESULT_KEYWORDS = [r'DTVKIT_LOG: ControlTuning\(0\): Tuning, TUNE LOCKED',
                              r'EpgSyncJobService: Finally getChannels size=\d+']
                              # r'DTVKIT_LOG: ADB_GetNumServicesInList:\d+ num_serv = \d+ \(ANALOG:0 TV:\d+ RADIO:\d+ data: 0\)']
    SEARCH_RESULT_KEYWORDS_DRIVER = ['Lock Status: Locked']

    # for check_whether_search_missing
    SEARCH_CHANNEL_NUMBER_FILTER = 'logcat -s EpgSyncJobService | grep getChannels'
    # video = '/home/amlogic/video/DVB/gr1.ts'
    # VIDEO_CHANNEL_NUMBER_FILTER = f'ffprobe -show_format {video} | grep nb_programs'
    VIDEO_CHANNEL_NUMBER_FILTER = f'ffprobe -show_format'

    # for check_switch_channel
    # channelid need to modify
    SWITCH_CHANNEL_FILTER = 'logcat -s MainActivity Aml_MP'
    SWITCH_CHANNEL_KEYWORDS = [r'MainActivity: saveChannelIdForAtvDtvMode dtvkit com.droidlogic.dtvkit.inputsource/.DtvkitTvInput/HW19, channelid = \d+',
                               'AML_MP_PLAYER_EVENT_VIDEO_CHANGED']
                               # 'AM_TSPLAYER_EVENT_TYPE_FIRST_FRAME']

    # for check_av_match after switch channel
    AV_MATCH_FILTER = 'cat /sys/class/dmx/dump_filter | grep type'
    AV_MATCH_KEYWORDS = ['']

    # for check_start_pvr_recording
    START_PVR_FILTER = 'logcat -s Aml_MP DvrManager'
    START_PVR_KEYWORDS = ['Aml_MP  : AmlDVRRecorder Call DVRRecorderStart',
                          'DvrManager: Adding scheduled recording of channel']
    START_PVR_FILTER_DRIVER = 'cat /sys/class/dmx/dum_filter'

    # for check_stop_pvr_recording
    STOP_PVR_FILTER = 'logcat -s Aml_MP DvrManager'
    STOP_PVR_KEYWORDS = ['Aml_MP  : AmlDVRRecorder Call DVRRecorderStop',
                         'DvrManager: stopRecording ScheduledRecording']

    # for check_pvr_auto_stop_recording
    PVR_AUTO_STOP_FILTER = 'logcat -s Aml_MP DvrManager'
    PVR_AUTO_STOP_KEYWORDS = ['Aml_MP  : AmlDVRRecorder Call DVRRecorderStop']

    # for check_timed_recording
    TIMED_RECORDING_FILTER = 'logcat -s TimerActivity'
    TIMED_RECORDING_KEYWORDS = ['TimerActivity: addTimerAction: mStartContent =']

    # for check_delete_recording_timer
    DELETE_TIMED_RECORDING_FILTER = 'logcat -s TimerActivity'
    DELETE_TIMED_RECORDING_KEYWORDS = ['TimerActivity: delete timer']

    # for check_pvr_start_play
    PVR_START_PALY_FILTER = 'logcat -s DvrPlayer DTVKIT_LOG libdvr Aml_MP'
    PVR_START_PALY_KEYWORDS = ['DvrPlayer: prepare\(\)',
                               'DTVKIT_LOG: STB_PVRStartPlaying: start_playback \[1\]',
                               'AML_MP_PLAYER_EVENT_VIDEO_CHANGED']
    PVR_START_PALY_FILTER_DRIVER = 'cat /sys/class/dmx/dump_filter'

    # for check_pvr_ff
    PVR_FF_FILTER = 'logcat -s DvrPlayer Aml_MP'
    PVR_FF_KEYWORDS = ['DvrPlayer: fastForward\(\)',
                       r'DvrPlayer: Let\'s play with speed: \d',
                       r'Aml_MP  : AmlDVRPlayer \[setPlaybackRate:\d+\] rate:\d.000000']

    # for check_pvr_fb
    PVR_FB_FILTER = 'logcat -s DvrPlayer Aml_MP'
    PVR_FB_KEYWORDS = ['DvrPlayer: rewind\(\)',
                       r'DvrPlayer: Let\'s play with speed: \d',
                       r'Aml_MP  : AmlDVRPlayer \[setPlaybackRate:\d+\] rate:\d.000000']

    # for check_pvr_seek
    PVR_SEEK_FILTER = 'logcat -s DvrPlayer Aml_MP'
    PVR_SEEK_KEYWORDS = ['DvrPlayer: seekTo\(\)',
                         # 'DvrPlayer: Now: 6745, shift to: 745',
                         r'Aml_MP  : AmlDVRPlayer \[seek:\d+\]']

    # for check_pvr_seek_pos
    PVR_SEEK_POS_FILTER = 'logcat -s libdvr'
    # PVR_SEEK_POS_KEYWORDS = [r'libdvr  : wrapper dvr_wrapper_seek_playback 2138: playback\(sn:\d+\) seeked\(off:\d+\) \(0\)']
    PVR_SEEK_POS_KEYWORDS = [
        r'libdvr  : into seek time=0, offset=0 time--\d+']

    # for check_pvr_current_seek_pos
    PVR_CURRENT_SEEK_POS_FILTER = 'logcat -s libdvr'
    PVR_CURRENT_SEEK_POS_KEYWORDS = [r'libdvr  : wrapper dvr_wrapper_seek_playback 2138: playback\(sn:\d+\) seeked\(off:\d+\) \(0\)',
                                     r'libdvr  : wrapper process_generatePlaybackStatus 2798: warning not change start time :ctx->playback.tf_full\[\d+\]id\[\d+\] \[\d+\] cur\[\d+\]']

    # for check_pvr_pause
    PVR_PAUSE_FILTER = 'logcat -s DvrPlayer Aml_MP'
    PVR_PAUSE_KEYWORDS = ['DvrPlayer: pause\(\)',
                          r'Aml_MP  : AmlDVRPlayer \[pause:\d+\]']

    # for check_pvr_resume
    PVR_RESUME_FILTER = 'logcat -s DvrPlayer Aml_MP'
    PVR_RESUME_KEYWORDS = [r'Aml_MP  : AmlDVRPlayer \[resume:\d+\]']

    # for check_pvr_stop
    PVR_STOP_FILTER = 'logcat -s DvrPlayer Aml_MP'
    PVR_STOP_KEYWORDS = ['DvrPlayer: reset\(\)']
                         # r'Aml_MP  : AmlDVRPlayer \[stop:\d+\]']  # This log appears occasionally

    # for check_timeshift_start
    TIMESHIFT_START_FILTER = 'logcat -s Aml_MP DTVKIT_LOG TunableTvView'
    TIMESHIFT_START_KEYWORDS = [r'Aml_MP  : AmlDVRRecorder \[AmlDVRRecorder:\d+\]',
                                r'Aml_MP  : AmlDVRRecorder location:/mnt/media_rw/.*',
                                r'DTVKIT_LOG: STB_PVRRecordStart:\d+ Starting timeshift recording \w+ for \d+ secs/0 B',
                                'TunableTvView: toggleTimeShift: true']

    # for check_timeshift_ff
    TIMESHIFT_FF_FILTER = 'logcat -s TimeShiftManager Aml_MP'
    TIMESHIFT_FF_KEYWORDS = ['TimeShiftManager: PlayController fastForward',
                             r'Aml_MP  : AmlDVRPlayer \[setPlaybackRate:\d+\] rate:\d.000000']
    # for check_timeshift_fb
    TIMESHIFT_FB_FILTER = 'logcat -s TimeShiftManager Aml_MP'
    TIMESHIFT_FB_KEYWORDS = ['TimeShiftManager: PlayController rewind',
                             r'Aml_MP  : AmlDVRPlayer \[setPlaybackRate:\d+\] rate:\d.000000']

    # for check_timeshift_pause
    TIMESHIFT_PAUSE_FILTER = 'logcat -s TimeShiftManager Aml_MP'
    TIMESHIFT_PAUSE_KEYWORDS = ['TimeShiftManager: PlayController pause']
                                # r'Aml_MP  : AmlDVRPlayer \[pause:\d+\]']

    # for check_timeshift_seek
    TIMESHIFT_SEEK_FILTER = 'logcat -s TimeShiftManager Aml_MP'
    TIMESHIFT_SEEK_KEYWORDS = ['TimeShiftManager: PlayController seekTo = ',
                               r'Aml_MP  : AmlDVRPlayer \[seek:\d+\]']

    # for check_timeshift_stop
    TIMESHIFT_STOP_FILTER = 'logcat -s TunableTvView DTVKIT_LOG Aml_MP'
    TIMESHIFT_STOP_KEYWORDS = ['TunableTvView: toggleTimeShift: false',
                               'DTVKIT_LOG: STB_DPStopRecording\(1\)',
                               # r'DTVKIT_LOG: STB_PVRRecordStop:\d+\ Stopping recording',
                               'Aml_MP  : AmlDVRRecorder Call DVRRecorderStop']

    # for check channel number from tv.db
    SELECT_SQL = 'sqlite3 /data/data/com.android.providers.tv/databases/tv.db "select count(*) from channels where ' \
                 'package_name = \'com.droidlogic.dtvkit.inputsource\'" '

    # for get channel id
    GET_CHANNEL_ID = 'sqlite3 /data/data/com.android.providers.tv/databases/tv.db "select _id from channels where ' \
                     'package_name = \'com.droidlogic.dtvkit.inputsource\'" '

    # for check is video playing through frame count
    FRAME_COUNT = 'cat /sys/class/video_composer/receive_count'

    # for check aspect ratio
    ASPECT_RATIO_FILTER = 'logcat -e setAspectRatio'
    CHECK_ASPECT_RATIO_AUTO = ['SettingsManager: setAspectRatio:0']
    CHECK_ASPECT_RATIO_4_3 = ['SettingsManager: setAspectRatio:1']
    CHECK_ASPECT_RATIO_PANORAMA = ['SettingsManager: setAspectRatio:2']
    CHECK_ASPECT_RATIO_16_9 = ['SettingsManager: setAspectRatio:3']
    CHECK_ASPECT_RATIO_DOT_BY_DOT = ['SettingsManager: setAspectRatio:4']

    # for check audio track is switch
    AUDIO_TRACK_SWITCH_FILTER = 'logcat -s MainActivity Aml_MP'
    AUDIO_TRACK_SWITCH_KEYWORDS = [r'MainActivity: updateAudioSettings found \d+']
                                   # r'Aml_MP  : AmlMpPlayerImpl_0 setAudioParams apid: \d+']

    # for get recorded video pid
    VIDEO_TRACK_COMPARE_FILTER = 'logcat -s DTVKIT_LOG'
    VIDEO_TRACK_COMPARE_KEYWORDS = [r'DTVKIT_LOG: STB_DPSetPCRPID\(0\): pid: .*']

    # for count record video track number
    VIDEO_TRACK_NUMBER_FILTER = 'logcat -s Glue'
    # VIDEO_TRACK_NUMBER_KEYWORDS = [r'DTVKIT_LOG: \[GetReqdAudioPid\] loop stream: \[stream_rec: .*\]\[audio_pid: \d+\]',
    #                                r'DTVKIT_LOG: PMT: 1 subtitle entries, PID = \d+']
    # VIDEO_TRACK_NUMBER_KEYWORDS = [r'Glue    : request : Player.getListOfTeletextStreams , reply :',
    #                                r'Glue    : request : Player.getListOfAudioStreams , reply :']
    VIDEO_TRACK_NUMBER_KEYWORDS = [r'\"pid\" : \d+']

    # for get current subtitle language
    SUBTITLE_CURRENT_LANGUAGE_FILTER = 'logcat -s SubtitleServer'
    SUBTITLE_CURRENT_LANGUAGE_KEYWORDS = [r'SubtitleServer: setSubPid ss=\S+ pid=\d+']

    # for get switch subtitle language
    SUBTITLE_SWITCH_LANGUAGE_FILTER = 'logcat -s LiveTVTest'
    SUBTITLE_SWITCH_LANGUAGE_KEYWORDS = [r'.*Bundle\[mParcelledData.dataSize']
