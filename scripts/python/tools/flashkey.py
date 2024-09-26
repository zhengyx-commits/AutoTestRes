#!/usr/bin/env python
# Copyright 2020 Amlogic.com, Inc. or its affiliates. All rights reserved.
#
# AMLOGIC PROPRIETARY/CONFIDENTIAL
#
# You may not use this file except in compliance with the terms and conditions
# set forth in the accompanying LICENSE.TXT file.
#
# THESE MATERIALS ARE PROVIDED ON AN "AS IS" BASIS. AMLOGIC SPECIFICALLY
# DISCLAIMS, WITH RESPECT TO THESE MATERIALS, ALL WARRANTIES, EXPRESS,
# IMPLIED, OR STATUTORY, INCLUDING THE IMPLIED WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.
#
import regex
import logging
from lib.common.system.ADB import ADB

keytype = ["hdcp", "hdcp2_rx", "widevinekeybox", "usid", "PlayReadykeybox25", "prpubkeybox", "prprivkeybox",
           "attestationdevidbox", "attestationkeybox"]

boot_write_command = {"hdcp": "fatload usb 0 12000000 hdcp14key.bin;keyman write hdcp 308 12000000;"
                              "keyman query exist hdcp",
                      "hdcp2_rx": "fatload usb 0 12000000 hdcp22_fw_private.bin;keyman write hdcp2_rx 32 12000000;"
                                  "keyman query exist hdcp2_rx",
                      "widevinekeybox": "fatload usb 0 12000000 widevinekeybox.bin;keyunify init 0;"
                                        "keyunify write widevinekeybox 0x12000000 128;"
                                        "keyman query exist widevinekeybox",
                      "usid": "keyman write usid str {};keyman query exist usid",
                      "PlayReadykeybox25": "keyunify init 0;fatload usb 0 12000000 playreadykeybox25.bin;"
                                           "keyunify write PlayReadykeybox25 0x12000000 7760;"
                                           "keyman query exist PlayReadykeybox25",
                      "prpubkeybox": "keyunify init 0;fatload usb 0 12000000 bgroupcert.dat;"
                                     "keyunify write prpubkeybox 0x12000000 1596;keyman query exist prpubkeybox",
                      "prprivkeybox": "fatload usb 0 12000000 zgpriv_protected.dat;"
                                      "keyunify write prprivkeybox 0x12000000 48;keyman query exist prprivkeybox",
                      "attestationdevidbox": "fatload usb 0 1080000 id_attestation.xml;"
                                             "keyman write attestationdevidbox 329 0x1080000;"
                                             "keyman query exist attestationdevidbox",
                      "attestationkeybox": "fatload usb 0 1080000 AMLS905XP212BT00000.keybox;"
                                           "keyman write attestationkeybox 8952 1080000;"
                                           "keyman query exist attestationkeybox"}

linux_write_bin_command = "echo 1 > /sys/class/unifykeys/attach;echo 1 > /sys/class/unifykeys/lock;" \
                      "echo {} > /sys/class/unifykeys/name;dd if={} of=/sys/class/unifykeys/write;" \
                      "cat /sys/class/unifykeys/exist;echo 0 > /sys/class/unifykeys/lock"

linux_write_str_command = "echo 1 > /sys/class/unifykeys/attach;echo 1 > /sys/class/unifykeys/lock;" \
                      "echo {} > /sys/class/unifykeys/name;echo \"{}\" > /sys/class/unifykeys/write;" \
                      "cat /sys/class/unifykeys/exist;echo 0 > /sys/class/unifykeys/lock"

linux_read_command = "echo 1 > /sys/class/unifykeys/attach;echo 1 > /sys/class/unifykeys/lock;" \
                     "echo {} > /sys/class/unifykeys/name;cat /sys/class/unifykeys/read;" \
                     "echo 0 > /sys/class/unifykeys/lock"

boot_check_command = "keyman query exist {}"
linux_check_command = "echo 1 > /sys/class/unifykeys/attach;echo 1 > /sys/class/unifykeys/lock;" \
                      "echo \"{}\" > /sys/class/unifykeys/name;cat /sys/class/unifykeys/exist;"\
                      "echo 0 > /sys/class/unifykeys/lock"
usb_command = "usb start"
save_command = "save"
erase_command = "store disprotect key;store erase key"
root_command = "root"


class Flashkey(ADB):

    def __init__(self, device=None, serialnum=None, supported=None, usid='1234567890'):
        ADB.__init__(self,"FlashUnifykey",unlock_code="", logdir=None, stayFocus=True)
        self._device = device
        self.usid = usid
        if supported == 'true':
            self._supported = True
        else:
            self._supported = False
        if self._device:
            self._device.enter_bootloader(timeout=20)

    def check_usb(self):
        usbnumber = 0
        rc, out = self._device.shell(usb_command)
        outlist = str(out).split('\n')
        for output in outlist:
            if output.find("Storage Device(s) found") != -1:
                res = regex.findall(r"\d", output)
                # print(res[0])
                usbnumber = res[0]
                break
        if usbnumber == '1':
            pass
        else:
            raise Exception("flashkey:Mount usb device error, please check.")

    def is_key_exist(self, name=None):
        if self._device:
            rc, out = self._device.shell(boot_check_command.format(name))
            if 'NOT Exist' in out:
                logging.debug("{} key not exist.".format(name))
                return False
            else:
                logging.debug("{} key exist.".format(name))
                return True
        else:
            rc, out = self.run_shell_cmd(linux_check_command.format(name))
            if 'none' in out:
                logging.debug("{} key not exist.".format(name))
                return False
            else:
                logging.debug("{} key exist.".format(name))
                return True

    def write_key(self, name=None, keyvalue=None):
        if self._device:
            self.check_usb()
            if name == 'usid':
                rc, out = self._device.shell(boot_write_command[name].format(keyvalue))
            else:
                rc, out = self._device.shell(boot_write_command[name])

            if 'NOT Exist' in out:
                logging.debug("{} key not exist.".format(name))
                raise RuntimeError('write key error.')
            else:
                logging.debug("{} key exist.".format(name))
                return True
        else:
            if name == 'usid':
                rc, out = self.run_shell_cmd(linux_write_str_command.format(name, keyvalue), 2)
            else:
                rc, out = self.run_shell_cmd(linux_write_bin_command.format(name, keyvalue), 2)

            if 'none' in out:
                logging.debug("{} key not exist.".format(name))
                raise RuntimeError('write key error.')
            else:
                logging.debug("{} key exist.".format(name))
                return True

    def read_key(self, name):
        if self._device:
            # TODO. to read key value in boot status
            pass
        else:
            rc, out = self._device.shell(linux_read_command.format(name))
            if out is not "":
                return out

    def setup_save(self, name=None):
        if self._device:
            self._device.shell(save_command)
        else:
            self.run_shell_cmd(cmd=root_command, timeout=20)

    # def flash_all_key(self):
    #     if self._supported:
    #         for key in keytype:
    #             rc, out = self._device.shell(check_command.format(key))
    #             if 'NOT Exist' in out:
    #                 self.check_usb()
    #                 if key == "usid":
    #                     rc, out = self._device.shell(boot_write_command[key].format(self.usid))
    #                     if 'NOT Exist' in out:
    #                         raise Exception("{} key write error.")
    #                     else:
    #                         print("{} write successful.".format(key))
    #                 else:
    #                     rc, out = self._device.shell(boot_write_command[key])
    #                     if 'NOT Exist' in out:
    #                         raise Exception("{} key write error.")
    #                     elif 'Unable to read file' in out:
    #                         print("{} not found in USB device, please check".format(key))
    #                         continue
    #                     else:
    #                         print("{} write successful.".format(key))
    #                 self.setup_save()
    #             else:
    #                 print("{} is exist.".format(key))
    #                 pass
    #     else:
    #         print("skip support drm.")
    #         pass

    def erase_all_key(self):
        self._device.shell(erase_command)
        self.setup_save()
