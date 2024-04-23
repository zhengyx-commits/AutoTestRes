from lib.common.checkpoint.HdmiCheck import HdmiCheck

hdmiCheck = HdmiCheck()
hdcp_file_path = '/home/amlogic/hdcp/'


def test_031_HDCP():
    assert hdmiCheck.get_tx_hdmi_authenticated() == '1'
    if not hdmiCheck.check_tx_22():
        hdmiCheck.write_to_tx_22_key(hdcp_file_path)
    assert hdmiCheck.get_tx_hdcp_mode() in ['22', '14'], 'HDCP mode not match 2.2'
    assert hdmiCheck.get_edid_parsed() == "ok"

