import os
from tests.OTT_Hybrid import config_yaml


p_conf_multiplayer = config_yaml.get_note("conf_multiplayer")
p_conf_play_time_after_restore_network = p_conf_multiplayer.get("play_time_after_restore_network")
p_conf_offline_network_time = p_conf_multiplayer.get("offline_network_time")


