from lib.common.system.ADB import ADB
from lib.common.system.HdmiOut import HdmiOut

adb = ADB()
hdmiout = HdmiOut()


def test_030_hdmi_color_space():
    color_spaces = ["rgb,8bit", "rgb,10bit", "rgb,12bit"]

    for color_space in color_spaces:
        output = adb.run_shell_cmd(f'meson_display_client -s "HDMI Color ATTR" {color_space} -c 1080p60hz')[1]
        assert color_space in output
