from lib.common.system.ADB import ADB
from time import sleep
from util.Decorators import count_down
import logging


class HdmiOut(ADB):
    '''
    hdmi out test lib

    Attributes:
        GET_RATIO_COMMAND : get disaplay mode
        GET_RATIO_LIST_COMMAND : get resolution list
        SETTING_ACTIVITY_TUPLE : setting activity tuple
        ENABLE_DEBUG_COMMAND : open hdmi debug
        DISABLE_DEBUG_COMMAND : close hdmi debug
        SET_RATIO_COMMAND : set ratio command

        set_ration_command_list : set ration command list
        best_resolution : optimal resolution
        ratio_list : ratio list
        switch_times : switch times
        switch_error_times : switch error times ( not target resolution )
        switch_fail_times : switch fill times ( switch command fail )
        result : test result
        switch_fail_list : switch fail resolution list [str]
        switch_error_list : switch error resolution list [str]
    '''

    GET_RATIO_COMMAND = 'cat /sys/class/display/mode'
    GET_RATIO_LIST_COMMAND = 'cat /sys/class/amhdmitx/amhdmitx0/disp_cap'
    SETTING_ACTIVITY_TUPLE = "com.shcmcc.setting", ".activity.output.DisplayMessageActivity"
    ENABLE_DEBUG_COMMAND = 'echo 1 > /sys/class/display/debug'
    DISABLE_DEBUG_COMMAND = 'echo 0 > /sys/class/display/debug'
    SET_RATIO_COMMAND = ('echo stop14 > /sys/class/amhdmitx/amhdmitx0/hdcp_ctrl;'
                         'echo stop22 > /sys/class/amhdmitx/amhdmitx0/hdcp_ctrl;'
                         'echo 444,8bit > /sys/class/amhdmitx/amhdmitx0/attr;'
                         'echo null > /sys/class/display/mode;'
                         'echo {} > /sys/class/display/mode;'
                         'echo 2 > /sys/class/amhdmitx/amhdmitx0/hdcp_mode;'
                         'echo 2 > /sys/class/amhdmitx/amhdmitx0/cedst_policy;')
    SET_RATIO_ID = "dumpsys SurfaceFlinger | grep '{}' | cut -d '=' -f 2 | cut -d ',' -f 1"
    GET_RESOLUTION_TABLE = "dumpsys SurfaceFlinger | grep 'fps='"
    SET_RATIO_COMMAND_R = 'service call SurfaceFlinger 1035 i32 {}'

    def __init__(self):
        super(HdmiOut, self).__init__()
        self.set_ration_command_list = [i.strip() for i in self.SET_RATIO_COMMAND.split(';')][:-1]
        self.best_resolution = ''
        self.ratio_list = self.get_ratio_list()
        self.switch_times = 0
        self.switch_error_times = 0
        self.switch_fail_times = 0
        self.resolution = 0
        # self.radioList = ['480i60hz', '576i50hz', '480p60hz', '576p50hz', '720p60hz', '1080i60hz', '1080p60hz',
        #                   '720p50hz', '1080i50hz', '1080p50hz', '2160p30hz', '2160p25hz', '2160p24hz', 'smpte24hz',
        #                   'smpte25hz', 'smpte30hz', 'smpte50hz', 'smpte60hz', '2160p50hz', '2160p60hz']
        self.result = 'Pass'
        self.home()
        self.root()
        self.switch_fail_list = []
        self.switch_error_list = []
        self.version = "ro.build.version.sdk"

    def get_ratio_list(self):
        '''
        get resolution list
        @return: resolution list [str]
        '''
        resList = self.run_shell_cmd(self.GET_RATIO_LIST_COMMAND)[1]
        for i in resList.split('\n'):
            if '*' in i:
                self.best_resolution = i.replace('*', '').strip() if i.replace('*', '').strip() else '1080p60hz'
        return resList.replace('*', '').split('\n')[:-1]

    @count_down(90)
    def switch_resolution(self, ration_list):
        # self.start_activity(*self.settingResActivity)
        # self.run_shell_cmd(self.hdmidebug_cmd)
        self.resolution = self.get_ratio_list()
        resolution_table = self.run_shell_cmd(self.GET_RESOLUTION_TABLE)[1]
        if not self.resolution:
            raise EnvironmentError('Pls check hdmi status')
        if self.getprop(self.version) >= "30":
            logging.debug(f'ration_list : {ration_list}')
            for ration in ration_list:
                if ration in self.get_ratio_list() and ration_list[ration] in resolution_table:
                    logging.debug(f'ration : {ration}')
                    if self.check_hdmi():
                        logging.info('HDMI is ok,start to switch display')
                        logging.info(f'Switch -> {ration}')
                        self.switch_times += 1
                        display_mode_id = self.run_shell_cmd(self.SET_RATIO_ID.format(ration_list[ration]))[1]
                        logging.debug(f'ration id : {display_mode_id}')
                        self.run_shell_cmd(self.SET_RATIO_COMMAND_R.format(display_mode_id))
                        sleep(8)
                        current = self.run_shell_cmd(self.GET_RATIO_COMMAND)[1]
                        logging.info(f'Current radio: {current}')
                        self.screenshot(ration + str(self.switch_times))
                        if ration not in current:
                            logging.info(f'Switch -> {ration} failed')
                            self.switch_error_list.append(ration)
                            self.switch_error_times += 1
                            # self.result = 'Fail'
                    # else:
                    #     logging.info(f'Cannot Switch -> {ration}')
                    #     self.switch_fail_list.append(ration)
                    #     self.switch_fail_times += 1
        else:
            for i in self.get_ratio_list():
                if self.check_hdmi():
                    logging.info('HDMI is ok,start to switch display')
                    logging.info(f'Switch -> {i}')
                    self.switch_times += 1
                    for j in self.set_ration_command_list:
                        self.run_shell_cmd(j.format(i))
                    sleep(6)
                    current = self.run_shell_cmd(self.GET_RATIO_COMMAND)[1]
                    logging.info(f'Current radio: {current}')
                    self.screenshot(i + str(self.switch_times))
                    if i not in current:
                        logging.debug(f'Switch -> {i} failed')
                        self.switch_error_list.append(i)
                        self.switch_error_times += 1
                        # self.result = 'Fail'
                else:
                    logging.info(f'Cannot Switch -> {i}')
                    self.switch_fail_list.append(i)
                    self.switch_fail_times += 1
            self.run_shell_cmd('echo {} > /sys/class/display/mode'.format(self.best_resolution))

        # self.run_shell_cmd(self.hdmidebug_stop_cmd)
        # self.app_stop(self.settingResActivity[0])
        self.home()

    def check_hdmi(self):
        '''
        check hdmi status , wait for 60 seconds
        @return: hdmi status : boolean
        '''
        check_hdmi = True
        if not self.get_ratio_list():
            for _ in range(20):
                if self.get_ratio_list():
                    check_hdmi = True
                    break
                else:
                    logging.info('Please Check HDMI')
                    sleep(3)
                    check_hdmi = False
            return check_hdmi
        else:
            return check_hdmi
