class KTKeywords:
    # pause, tsplayer
    PAUSE_KEYWORDS = ["PauseVideoDecoding mVdNonTunnelMode->Pause() finished"]

    # resume, tsplayer
    RESUME_KEYWORDS = ["ResumeVideoDecoding mVdNonTunnelMode->Resume finished"]

    # stop, tsplayer
    STOP_KEYWORDS = ["TSP_onMessageReceived kWhatStopVideo mEsDataHandler->StopVideoFilter"]

    # switch channel, Aml_MP
    SWITCH_CHANNEL_KEYWORDS = ["AM_TSPLAYER_EVENT_TYPE_FIRST_FRAME"]

    # seek, Aml_MP
    SEEK_KEYWORDS = ["Aml_MP  : AmlMpPlayerImpl_0 [flush:"]

    TS_LOGCAT = "logcat -s TsPlayer"
    AMP_LOGCAT = "logcat -s Aml_MP"
