from lib.common.system.HdmiOut import HdmiOut
from lib.common.checkpoint.HdmiCheck import HdmiCheck
import logging
from tests.OTT_Sanity_Ref import config_yaml

hdmi = HdmiCheck()
hdmiout = HdmiOut()
p_ration_list = config_yaml.get_note('conf_hdmi_display')
logging.info(f'p_ration_list: {p_ration_list}')


def test_display_hdmiout():
    assert hdmi.check_tx_mode() == '1', 'TX is not connected'
    hdmiout.run_shell_cmd(hdmiout.ENABLE_DEBUG_COMMAND)
    hdmiout.switch_resolution(ration_list=p_ration_list)
    hdmiout.run_shell_cmd(hdmiout.DISABLE_DEBUG_COMMAND)
    assert hdmiout.resolution
    logging.debug('total switch{},failed{}, failed to switch{}'.format(hdmiout.switch_times, hdmiout.switch_error_times
                                                                       , hdmiout.switch_error_list))
    logging.debug('cannot switch{}, failed{}'.format(hdmiout.switch_fail_list, hdmiout.switch_fail_times))
    assert hdmiout.switch_error_times == 0
    assert hdmiout.switch_fail_times == 0
