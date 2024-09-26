import logging
import os
import time

from lib.common.system.ADB import ADB
from tools.resManager import ResManager


class FactoryReset(ADB):
    '''
    factory reset over command

    Attributes:
        TESTFILE : reset test file path
        TESTSH : reset test shell file path

        res : ResManager instacne

    '''
    TESTFILE = '/data/local/FileForFactory.txt'
    TESTSH = '/data/recovery.sh'

    def __init__(self):
        super(FactoryReset, self).__init__()
        self.res = ResManager()

    def setup(self):
        '''
        set up test enviroment
        1. root device
        2. check test file
        3. push test shell
        @return:
        '''
        self.popen('root')
        self.check_test_file()
        self.pushRecoverySh()

    def run_recovery(self):
        '''
        run test shell
        :return: None
        '''
        self.run_shell_cmd(f'sh {self.TESTSH}')

    def check_test_file(self):
        '''
        check if test file exist
        :return: exist status : boolean
        '''
        logging.info('Stert checking')
        result = self.popen(f'shell ls {self.TESTFILE} 2>&1').stdout.readlines()[0]
        if 'No such file or directory' in result:
            logging.info('Not exists , create it ')
            self.root()
            self.run_shell_cmd(f'touch {self.TESTFILE}')
            return True
        else:
            return False

    def pushRecoverySh(self):
        '''
        check if exist test shell
        :return: None
        '''
        result = self.popen(f'shell ls {self.TESTSH} 2>&1').stdout.readlines()[0]
        if 'No such file or directory' in result:
            logging.info('Not exists , create it ')
            self.root()
            # self.push(f'{os.getcwd()}/res/sh/recovery.sh', '/data/')
            self.push(f"{self.res.get_target('sh/recovery.sh')}", '/data/')
            self.run_shell_cmd(f'chmod a+x {self.TESTSH}')

    def run_factory_reset(self):
        '''
        factory reset
        1. set up enviroment
        2. run test shell
        3. check test file
        @return: test resul : boolean
        '''
        self.setup()
        self.run_recovery()
        self.wait_devices()
        time.sleep(10)
        result = self.check_test_file()
        self.home()
        logging.info("Factory Reset:{}".format("Pass" if result else "Fail"))
        return result
