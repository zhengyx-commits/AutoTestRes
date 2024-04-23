from tests.OTT_Sanity_Ref import *

amplayer_package = "com.droidlogic.exoplayer2.demo"
amplayer_activity = "com.droidlogic.exoplayer2.demo/com.droidlogic.videoplayer.MoviePlayer"


def get_uuid():
    adb.root()
    uuid = adb.run_shell_cmd("ls /mnt/media_rw/")[1]
    return uuid


uuid = get_uuid()


def create_play_audio_cmd(uuid, audio):
    play_cmd = f"am start -a com.google.android.exoplayer.demo.action.VIEW -d file:/storage/{uuid}/audio/{audio}"
    return play_cmd


def get_audio_list():
    if not uuid:
        assert False, "Can't find uuid,please plug U disk"
    audio_file = adb.run_shell_cmd(f'ls /storage/{uuid}/audio/')[1]
    audio_file_list = audio_file.split("\n")
    audio_info_list = []
    for audio in audio_file_list:
        info_tuple = (audio, audio.split('.')[-1])
        audio_info_list.append(info_tuple)
    logging.info(f"audio_info_list: {audio_info_list}")
    return audio_info_list