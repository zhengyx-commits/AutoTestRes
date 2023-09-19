#!/bin/bash
device_id=$1


echo "----------------------------------------------"
adb -s $device_id reboot bootloader
sleep 10
fastboot -s $device_id flashing unlock_critical
fastboot -s $device_id flashing unlock
echo "----------------------------------------------"
echo "Fastboot unlock"
echo "Now Reboot and disable AVB"
echo "----------------------------------------------"
fastboot -s $device_id reboot
echo "Waiting to Starting root and disable AVB"
echo "----------------------------------------------"

while true
do
    adb -s $device_id root >/dev/null 2>&1
    if [ $? = 0 ]
    then    
        break
    else
        sleep 5
    fi

done
sleep 10

adb -s $device_id disable-verity
echo "Finished and reboot."
adb -s $device_id reboot
echo "Waiting and Starting disable SELinux."
while true
do
    adb -s $device_id root >/dev/null 2>&1
    if [ $? = 0 ]
    then    
        break
    else
        sleep 5
    fi

done

sleep 10

adb -s $device_id shell setenforce 0
adb -s $device_id remount
