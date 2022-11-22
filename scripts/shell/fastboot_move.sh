#!/bin/bash

pwd=$(pwd)
fastboot_img=$(ls ~/Downloads/ |grep "tgz" |head -n 1)
ota_bin=$(ls ~/Downloads/ |grep "bin" |head -n 1)
mv ~/Downloads/$fastboot_img $pwd/image
sed -i  's!\("fastboot_location":\).*!"fastboot_location": "'.image/"$fastboot_img"'",!g' $pwd/../python/config/config_tv_amazon.json
sed -i  's!\("ota_location":\).*!"ota_location": "'.image/"$ota_bin"'",!g' $pwd/../python/config/config_tv_amazon.json

grep "fastboot_location" $pwd/config/config_tv_amazon.json
grep "ota_location" $pwd/config/config_tv_amazon.json

date_base=$(cat ~/date.txt | sed -n '1p')
today_date=`date "+%Y%m%d"`
date_gap=$((($(date +%s ) - $(date +%s -d $date_base))/86400))
ugrad_tgz_base=$(cat ~/date.txt | sed -n '3p')
update_tgz=$(cat ~/date.txt | sed -n '4p')
if [[ $update_tgz == $ugrad_tgz_base ]];then
    echo "--- Today's version is not compiled or updated "
    echo $date_base > ~/date.txt
    echo $date_gap >> ~/date.txt
    echo $ugrad_tgz_base >> ~/date.txt

else
    echo " --- The latest version is : $update_tgz"
    echo $today_date > ~/date.txt
    echo $date_gap >> ~/date.txt
    echo $update_tgz >> ~/date.txt
fi