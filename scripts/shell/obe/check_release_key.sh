#!/bin/bash
url=$1
build_number=$(basename "$url" | grep -oE '[0-9]+')
devices=("ohm0000000031" "ohm0000000032" "ohm0000000033" "ohm0000000034" "ohm0000000035" "ohm0000000036")
check_count=0
if [ -f "./update-devices.txt" ]; then
    rm "./update-devices.txt"
fi
for device in "${devices[@]}"; do
    release_key=$(adb -s ${device} shell getprop | grep finger| head -n 1)
    if [[ $release_key =~ $build_number ]]; then
        echo "${device} update image successfully!"
        check_count=$((check_count+1))
        echo ${device} >> ./update-devices.txt
    else
        echo "${device} update image failed!"
    fi
done
if [ $check_count -eq 6 ]; then
    echo "All devices updated successfully"
    exit 0
else
    echo "Some devices may not be updated successfully!"
    exit 1
fi