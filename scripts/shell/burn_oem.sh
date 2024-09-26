#!/bin/bash
device=$1
workspace=$(pwd)
read -r OEM_MS12 <<< "$(find . -type f -name '*oem_ms12*' | head -1)"
read -r BOOT_DEBUG <<< "$(find . -type f -name '*boot-debug*' | head -1)"
read -r SYSTEM <<< "$(find . -type f -name '*system*' | head -1)"
if [[ -z "$OEM_MS12" ]]; then
    if [[ $workspace =~ "_VTS_Autotest" ]]; then
        echo "VTS test,go on!"
    else
        echo "oem_ms12.img not found,please copy it to workspace!"
        exit 1
    fi
fi
if [[ $workspace =~ "_VTS_Autotest" ]]; then
    if [[ -z "$BOOT_DEBUG" ]] || [[ -z "$SYSTEM" ]]; then
        echo "boot-debug.img or system.img not found,please copy it to workspace!"
        exit 1
    fi
fi
echo "Start to burn the image"
adb -s "$device" reboot bootloader
fastboot -s "$device" wait-for-device
fastboot -s "$device" flashing unlock_critical
fastboot -s "$device" flashing unlock
if [[ -n "$OEM_MS12" ]]; then
    fastboot -s "$device" flash oem "$OEM_MS12"
fi
if [[ $workspace =~ "_VTS_Autotest" ]]; then
    fastboot -s "$device" flash vendor_boot "$BOOT_DEBUG"
    fastboot -s "$device" reboot fastboot
    fastboot -s "$device" delete-logical-partition product_a
    fastboot -s "$device" delete-logical-partition product_b
    fastboot -s "$device" delete-logical-partition product
    fastboot -s "$device" flash system "$SYSTEM"
    fastboot -s "$device" reboot bootloader
    fastboot -s "$device" -w
    fastboot -s "$device" reboot
else
    fastboot -s "$device" flashing lock
    fastboot -s "$device" reboot
fi
sleep 180
exit 0