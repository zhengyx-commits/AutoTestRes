#!/bin/bash
# Copyright 2012 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

 
SERIAL=$1
# Add path to fastboot (if not already added)
export PATH=$PATH:"$SYSTEMROOT/System32"

 

adb -s "$SERIAL" reboot bootloader
fastboot -s "$SERIAL" flashing unlock
fastboot -s "$SERIAL" flash bootloader bootloader.img
fastboot -s "$SERIAL" reboot-bootloader
sleep 5
fastboot -s "$SERIAL" flashing unlock
fastboot -s "$SERIAL" erase env
fastboot -s "$SERIAL" erase misc
fastboot -s "$SERIAL" erase param
fastboot -s "$SERIAL" erase tee
fastboot -s "$SERIAL" erase frp
fastboot -s "$SERIAL" erase userdata
fastboot -s "$SERIAL" erase metadata

 

fastboot -s "$SERIAL" flash bootloader bootloader.img
fastboot -s "$SERIAL" flash boot boot.img
fastboot -s "$SERIAL" flash vendor_boot vendor_boot.img
fastboot -s "$SERIAL" flash dtbo dtbo.img
fastboot -s "$SERIAL" flash vbmeta vbmeta.img
fastboot -s "$SERIAL" flash vbmeta_system vbmeta_system.img
fastboot -s "$SERIAL" reboot-bootloader
sleep 5
fastboot -s "$SERIAL" flashing unlock

 

fastboot -s "$SERIAL" reboot-fastboot
sleep 10
fastboot -s "$SERIAL" wipe super
fastboot -s "$SERIAL" flash system system.img
if [ -e system_ext.img ]; then
  fastboot -s "$SERIAL" flash system_ext system_ext.img
fi
fastboot -s "$SERIAL" flash product product.img
fastboot -s "$SERIAL" flash vendor vendor.img
if [ -e vendor_dlkm.img ]; then
  fastboot -s "$SERIAL" flash vendor_dlkm vendor_dlkm.img
fi
fastboot -s "$SERIAL" flash odm odm.img
if [ -e odm_dlkm.img ]; then
  fastboot -s "$SERIAL" flash odm_dlkm odm_dlkm.img
fi

 

fastboot -s "$SERIAL" reboot-bootloader
sleep 5
fastboot -s "$SERIAL" flashing lock
fastboot -s "$SERIAL" reboot

 

#echo "Press any key to exit..."
#read -rsn1
exit
