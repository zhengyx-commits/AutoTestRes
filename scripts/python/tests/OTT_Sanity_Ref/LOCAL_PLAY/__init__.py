from tests.OTT_Sanity_Ref import *

localPlayer = LocalPlayer(play_from_list=True)
amplayer_package = localPlayer.LOCALPLAYER_AMPLAYER_PACKAGE_TUPLE[0]
amplayer_activity = f"{localPlayer.LOCALPLAYER_AMPLAYER_PACKAGE_TUPLE[0]}/{localPlayer.LOCALPLAYER_AMPLAYER_PACKAGE_TUPLE[1]}"
p_conf_local_playback = config_ott_sanity_yaml.get_note('conf_local_playback')
p_conf_amplayer_path = p_conf_local_playback['amplayer_path']
if is_sz_server():
    p_conf_uuid = p_conf_local_playback['sz_uuid']
else:
    p_conf_uuid = p_conf_local_playback['sh_amplayer_uuid']

amplayer_app_name = f'{localPlayer.LOCALPLAYER_AMPLAYER_PACKAGE_TUPLE[0]}'


def get_uuid():
    localPlayer.root()
    uuid = localPlayer.run_shell_cmd("ls /mnt/media_rw/")[1]
    return uuid


uuid = get_uuid()


def get_video_list():
    if not uuid:
        assert False, "Can't find uuid,please plug U disk"
    video_file = localPlayer.run_shell_cmd(f'ls /storage/{uuid}/amplayer/')[1]
    video_file_list = video_file.split("\n")
    video_info_list = []
    for video in video_file_list:
        info_tuple = (video, video.split('.')[-1])
        video_info_list.append(info_tuple)
    return video_info_list


def create_play_video_cmd(uuid, video):
    play_cmd = f"am start -n {amplayer_activity} -d file:/storage/{uuid}/amplayer/{video}"
    return play_cmd