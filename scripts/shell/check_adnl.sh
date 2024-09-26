#!/bin/bash
adb devices | while read line
do  
device=`echo $line | cut -d" " -f1 `
if [[ $device = 'List' ]];then
    continue
fi
if [[ $device = '' ]];then
    continue
fi
release_key=$(adb -s ${device} shell getprop  < /dev/null | grep finger| head -n 1)
echo ${device}:${release_key}
done
