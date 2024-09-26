import logging
import os
import re
import time

from lib.common.system.ADB import ADB
from util.Decorators import set_timeout


class Antutu(ADB):
    '''
    antutu apk test lib

    Attributes:
        PACKAGE_NAME : antutu package name
        OSD_RESOLUTION_COMMAND : osd res command

        _path : current path
        antutu_apk : apk path name
        antutu_plugin : plugin in apk path name
        result : test result
        resolution : resolution

    '''

    PACKAGE_NAME = 'com.antutu.ABenchMark'
    OSD_RESOLUTION_COMMAND = 'wm size'

    def __init__(self, serialnumber=''):
        ADB.__init__(self, 'Antutu', unlock_code="", stayFocus=True)
        self._path = os.getcwd()
        self.antutu_apk = self.res_manager.get_target('apk/antutu-benchmark-v573.apk')
        self.antutu_plugin = self.res_manager.get_target('apk/antutu-v5-3d-plugin.apk')
        self.result = 'Pass'
        self.resolution = ''

    def timeout(self):
        self.result = 'Fail'

    def setup(self):
        '''
        test set up , install antutu if not exists
        @return: None
        '''
        self.popen('root')
        if not self.check_apk():
            self.install_apk()
        self.reset_apk_status()
        # self.resolution = self.check_resolution()

    @set_timeout(15, timeout)
    def start_apk(self):
        '''
        start apk
        @return: None
        '''
        self.run_shell_cmd(f'monkey -p {self.PACKAGE_NAME} 1')
        time.sleep(10)
        self.u2.d.xpath('//*[@resource-id="com.antutu.ABenchMark:id/negative_btn"]').click()
        # self.wait('Cancel')
        # self.wait('Cancel')

    def reset_apk_status(self):
        '''
        kill apk package , back to home
        @return: None
        '''
        self.app_stop(self.PACKAGE_NAME)
        self.home()

    def apk_get_resolution(self):
        '''
        get resolution over antutu ui info
        @return: None
        '''
        self.start_apk()
        self.u2.wait('Info') or self.u2.wait('信息')
        res = self.u2.d.xpath("//android.widget.TextView[@text='1920 x 1080']").get_text()
        self.resolution = self.check_resolution(res)

    def cmd_get_resolution(self):
        '''
        get resolution over command
        @return: None
        '''
        res = self.run_shell_cmd(self.OSD_RESOLUTION_COMMAND)[1]
        res = re.findall(r'Physical size: (\S*)', res, re.S)[0]
        logging.info('Physical size:{}'.format(res))
        self.resolution = self.check_resolution(res)

    def check_resolution(self, res):
        '''
        check res is 1080p or not
        @param res: res
        @return: result : int
        '''
        if res == '1920x1080':
            logging.info(f'当前ui mode 为{res}')
            # self.reset_apk_status()
            return 1
        else:
            raise EnvironmentError('ui mode 错误，退出测试')

    def install_apk(self, **kwargs):
        '''
        install antutu
        @param **kwargs:
        @return: None
        '''
        logging.info('Installing antutu apk')
        self.popen(f'install {self.antutu_apk}')
        self.popen(f'install {self.antutu_plugin}')
        while not self.check_apk():
            time.sleep(1)

    def check_apk(self):
        '''
        check if apk exists
        @return: None
        '''
        res = ''.join(self.popen('ls /data/app/').stdout.readlines())
        return True if 'com.antutu.ABenchMark' in res else False

    @set_timeout(360)
    def run(self):
        '''
        run antutu test
        @return: None
        '''
        self.start_apk()
        if self.u2.d.exists(resourceId="com.antutu.ABenchMark:id/retest_text"):
            self.u2.d(resourceId="com.antutu.ABenchMark:id/retest_text").click()
        if self.u2.d.exists(resourceId="com.antutu.ABenchMark:id/start_test_text"):
            self.u2.d(resourceId="com.antutu.ABenchMark:id/start_test_text").click()
        self.u2.wait('Details')
        self.u2.d(resourceId='com.antutu.ABenchMark:id/close_img_view').click()
