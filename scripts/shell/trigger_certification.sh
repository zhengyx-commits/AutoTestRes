#!/bin/bash
echo "=======================  Start time and test SITE  ======================="
time_start=$(date "+%Y.%m.%d_%H:%M:%S")
report_start=$(date "+%Y.%m.%d_%H.%M")
start_timestamp=$(date +%s)
TEST_SITE=$(echo "$JOB_URL" | grep -oP '(?<=_)[A-Z]+(?=/)')
if [ -z "$TEST_SITE" ]; then
    TEST_SITE="SH"
fi
echo "Current test SITE：${TEST_SITE}"
echo "Test start time:${time_start}"

function syncAutoTestRes() {
    echo "sync AutoTestRes"
    if [ -d "AutoTestRes" ]; then
        echo "cd AutoTestRes"
        cd "$WORKSPACE/AutoTestRes/" || return 1
        git checkout release
        git fetch --all
        git reset --hard origin/release
        git rebase
        git pull
    else
        git clone ssh://fae.autobuild@scgit.amlogic.com:29418/amlogic/tools/AutoTestRes -b release
        echo "git clone pass"
    fi
}
syncAutoTestRes

#get image download url
cd "$WORKSPACE"
if [[ $TEST_UPSTEAM_PRJ_URL =~ 'jenkins' ]]; then
    echo "wget $TEST_UPSTEAM_PRJ_URL -O Build.html"
    wget "$TEST_UPSTEAM_PRJ_URL" -O Build.html
    echo "wget $TEST_UPSTEAM_PRJ_URL/injectedEnvVars/api/json?pretty=true -O parameter.json"
    wget "$TEST_UPSTEAM_PRJ_URL"/injectedEnvVars/api/json?pretty=true -O parameter.json
    Test_Image_Url=$(grep -Eoi "href=\"http:\S+Download Firmware" Build.html)
    Test_Image_Url=${Test_Image_Url#*\"}
    build_manifest_url="${Test_Image_Url%\"*}/build-manifest.xml"
    echo "build_manifest_url:${build_manifest_url}"
    if [[ "$TEST_SERIES" == "Android_U" ]]; then
        Test_Image_Url=${Test_Image_Url%\"*}'/signed_image/'
    else
        Test_Image_Url=${Test_Image_Url%\"*}'/'
    fi
    wget "$Test_Image_Url" -O Download.html
    if [[ $UPGRADE_MODE =~ "fastboot" ]]; then
        test_package=$(grep -oP "${TEST_BOARD}-fastboot-\S+?.zip" Download.html | sed -n '1p')
    elif [[ $UPGRADE_MODE =~ "adnl" ]]; then
        test_package=$(grep -oP "aml_upgrade_\S+?.tar.bz2" Download.html | sed -n '1p')
    else
        echo "UPGRADE_MODE not supported yet! Please change UPGRADE_MODE!"
        exit 1
    fi
    vendor_boot_img=$(grep -oP "vendor_boot-\S+?.img" Download.html | sed -n '1p')
    vendor_boot_img_url=$Test_Image_Url$vendor_boot_img
    echo "TEST_Package:$test_package"
    Test_Image_Url=$Test_Image_Url$test_package
    if [[ $JOB_URL =~ "_VTS" ]]; then
        echo "vendor_boot_img_url:${vendor_boot_img_url}"
        wget -q -O vendor_boot-debug.img "${vendor_boot_img_url}"
    fi
    Test_Build_Kernel_Arch=$(jq .envMap.KERNEL_BUILD_ARCH parameter.json | sed 's/\"//g')
    TEST_BUILD_NUMBER=$(jq .envMap.BUILD_NUMBER parameter.json | sed 's/\"//g')
    regex=".*${Test_Build_Kernel_Arch}-\([^/]*\)-${TEST_BUILD_NUMBER}.*"
    TEST_BUILD_TYPE=$(echo $Test_Image_Url | sed -n "s/${regex}/\1/p")
    TEST_BUILD_INFO=$(grep -oP "${TEST_BOARD}-\S+?-${TEST_BUILD_NUMBER}" Download.html | sed -n '1p')
else
    echo "URL not supported yet! Please change URL!"
    exit 1
fi

#Configuring Test Node Information
TEST_NODE_IP="10.18.19.2"
TEST_NODE_PWD="Linux2017"

#Configuring Test Device Information
devices_json='{
  "XTS123456789": "/dev/device,/dev/powerRelay",
  "ohm5610190440080b": "/dev/device1,/dev/powerRelay1"
}'

#Configuring Test Project Information
TEST_TARGET="cts"

#Declare environment variables
export TEST_BUILD_NUMBER="$TEST_BUILD_NUMBER"   # AutoBuild Number
export TEST_NODE_IP="10.18.19.2"    # Test node ip
export TEST_NODE_PWD="Linux2017"    # Test node password
export TEST_BUILD_TYPE="$TEST_BUILD_TYPE"   # AutoBuild type,GTV or ATV
export TEST_BUILD_INFO="$TEST_BUILD_INFO"   # AutoBuild info
export TEST_SITE="$TEST_SITE"   # Test site,SH or XA or SZ
export TEST_TARGET="$TEST_TARGET"   # Test target,use it to change target.json
export TEST_IMAGE_URL="$Test_Image_Url"     # Parsed Download url
export TEST_START_TIMESTAMP="$start_timestamp"  # Test start timestamp
export TEST_DEVICES_JSON="$devices_json"    # Test devices info
export DUT_SERIAL_PORT_BAUDRATE=921600      # The serial port baud rate of Test devices
export TEST_WIFI_SSID="SE_AUT_5G"   # The wifi ssid that the test devices need to connect
export TEST_WIFI_PWD="aut12345678"  # The wifi password that the test devices need to connect
echo "=======================  Parameterized FROM UPSTREAM  ======================="
printf "%24s%-s\n" "TEST_BUILD_NUMBER: " "$TEST_BUILD_NUMBER"
printf "%24s%-s\n" "TEST_BOARD: " "$TEST_BOARD"
printf "%24s%-s\n" "TEST_BUILD_VARIANT: " "$TEST_BUILD_VARIANT"
printf "%24s%-s\n" "TEST_BUILD_TYPE: " "$TEST_BUILD_TYPE"
printf "%24s%-s\n" "TEST_BUILD_INFO: " "$TEST_BUILD_INFO"
printf "%24s%-s\n" "TEST_SERIES: " "$TEST_SERIES"
printf "%24s%-s\n" "TEST_TARGET: " "$TEST_TARGET"
printf "%24s%-s\n" "TEST_IMAGE_URL: " "$TEST_IMAGE_URL"
printf "%24s%-s\n" "UPGRADE_MODE: " "$UPGRADE_MODE"
printf "%24s%-s\n" "TEST_DEVICES_LIST: " "$TEST_DEVICES_JSON"
printf "%24s%-s\n" "DUT_SERIAL_PORT_BAUDRATE: " "$DUT_SERIAL_PORT_BAUDRATE"
printf "%24s%-s\n" "TEST_WIFI_SSID: " "$TEST_WIFI_SSID"
printf "%24s%-s\n" "TEST_WIFI_PWD: " "$TEST_WIFI_PWD"
printf "%24s%-s\n" "WORKSPACE: " "$WORKSPACE"
printf "%24s%-s\n" "TEST_NODE: " "$TEST_NODE_IP"
printf "%24s%-s\n" "TEST_NODE_USER: " "$USER"
echo "============================================================================="

cd "$WORKSPACE"
echo $TEST_NODE_PWD | sudo -S chmod +777 -R AutoTestRes/scripts
echo $TEST_NODE_PWD | sudo -S chmod +777 /dev/powerRelay*
echo $TEST_NODE_PWD | sudo -S chmod +777 /dev/device*
if [[ "$TEST_TARGET" == "cts" ]]; then
    echo $TEST_NODE_PWD | sudo -S chmod +777 /dev/ttyACM0
fi
bash AutoTestRes/scripts/shell/load_test_certification.sh
mkdir -p log
python3 AutoTestRes/scripts/python/localxts_runner.py --$TEST_TARGET -all

#Configure the remote file path
case $TEST_BOARD in
    ohm*) board="ohm";;
    planck*) board="planck";;
    oppen*) board="oppen";;
    boreal*) board="boreal";;
    adt4*) board="adt4";;
    *) board="unknown";;
esac
remote_path="/home/amlogic/FAE/AutoTest/AllureReport/XTS_Test/$TEST_SERIES/$TEST_SITE/${TEST_TARGET^^}/${board}"
sshpass -p "Linux2023" ssh amlogic@10.18.11.98 "mkdir -p \"$remote_path\""
sshpass -p "Linux2023" ssh amlogic@10.18.11.98 "mkdir -p \"$remote_path\"/history/\"$report_start\""

#Result comparison
mkdir -p "${TEST_BOARD}-build-manifests"
old_xml=$(./result_comparison/get_latest_file.sh "${TEST_BOARD}-build-manifests")
wget -q -O "${TEST_BOARD}-build-manifests/build-manifest-${TEST_BUILD_NUMBER}.xml" "$build_manifest_url"
new_xml="build-manifest-${TEST_BUILD_NUMBER}.xml"
cd result_comparison
echo "old_xml:${old_xml}"
echo "new_xml:${new_xml}"
bash xts_results_comparion.sh "${TEST_BOARD}-test_result_new.xml" \
"${TEST_BOARD}-test_result_old.xml" \
"${WORKSPACE}/${TEST_BOARD}-build-manifests/${new_xml}" \
"${WORKSPACE}/${TEST_BOARD}-build-manifests/${old_xml}"
execute_code=$?
if [ $execute_code -eq 0 ]; then
	echo "Results comparison file generate successfully!"
    latest_file=$(ls -t | grep '^Test_Result_Comparison.*\.html$' | head -n 1)
	cp "$latest_file" ../latest_comparion.html
    sshpass -p "Linux2023" scp ../latest_comparion.html amlogic@10.18.11.98:"$remote_path"/history/"$report_start"
fi

#Result upload server
cd $WORKSPACE
end_timestamp=$(date +%s)
duration=$((end_timestamp - start_timestamp))
hours=$(( (duration + 1800) / 3600 ))
log_url="http://aut.amlogic.com/AutoTest/AllureReport/XTS_Test/$TEST_SERIES/$TEST_SITE/${TEST_TARGET^^}/${board}/history/$report_start"
sshpass -p "Linux2023" scp -r ./last_report/*.tar amlogic@10.18.11.98:"$remote_path"/history/"$report_start"
rm last_report/*.tar
sshpass -p "Linux2023" scp -r ./last_report amlogic@10.18.11.98:"$remote_path"
scp_exit_code=$?
if [ $scp_exit_code -eq 0 ]; then
	echo "SCP files successfully!"
else
	echo "SCP file failed, please check!"
fi
echo "Test finished,Duration: about $hours hours!"
bash result_comparison/mail_html.sh "${log_url}"
sleep 10
end_time=$(date +"%Y/%m/%d %H:%M:%S")
echo "Job the first board end at: ${end_time}"
