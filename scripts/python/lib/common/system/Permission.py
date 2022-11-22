import logging

import uiautomator2 as u2

from lib.common.system.ADB import ADB


class Permission:
    '''
    Apk permission lib

    '''

    def permission_check(self, text="Allow", uiautomator_type="u2"):
        '''
        check permission dialog
        @param text: dialog text info
        @return: None
        '''
        self.adb = ADB()
        logging.info('Check permission')
        try:
            if uiautomator_type == "u1":
                self.adb.u(type=uiautomator_type).d1(text=text).click()
            else:
                self.adb.u().d2(text=text).click()
        except u2.exceptions.UiObjectNotFoundError as e:
            logging.warning(e)
        except OSError as e:
            logging.warning(e)
