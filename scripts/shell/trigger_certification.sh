#!/bin/bash
start_time=$(date +"%Y/%m/%d %H:%M:%S")
echo "Job start at: ${start_time}"
sleep 10

HOSTNAME=$(hostname -I | awk '{print $2}')
if ! command -v jq >/dev/null; then
    echo "jq command not found,Please use 'sudo apt install jq' to install jq"
    exit 1
fi
Test_UPSTEAM_PRJ_URL=$1
UPGRADE_MODE=$2
Test_TYPE=$3
Test_SERIES=$4
DUT_ADB_SN=$5
DUT_SERIAL_PORT=$6
POWER_RELAY_SERIAL_PORT=$7
work_powerRelay_dir=$8
DUT_SERIAL_PORT_BAUDRATE=921600
CERTIFICATION_TYPE=$(echo $JOB_URL | grep -oP '(?<=_)[A-Z]+(?=_Autotest)')
TESTPLAN="${Test_SERIES}_${CERTIFICATION_TYPE}"
echo "=======================  Parameterized FROM UPSTREAM  ======================="
printf "%24s%-s\n" "Test_UPSTEAM_PRJ_URL: " "$Test_UPSTEAM_PRJ_URL"
printf "%24s%-s\n" "Test_TYPE: " "$Test_TYPE"
printf "%24s%-s\n" "CERTIFICATION_TYPE: " "$CERTIFICATION_TYPE"
printf "%24s%-s\n" "Test_SERIES: " "$Test_SERIES"
printf "%24s%-s\n" "UPGRADE_MODE: " "$UPGRADE_MODE"
printf "%24s%-s\n" "DUT_ADB_SN: " "$DUT_ADB_SN"
printf "%24s%-s\n" "DUT_SERIAL_PORT: " "$DUT_SERIAL_PORT"
printf "%24s%-s\n" "POWER_RELAY_SERIAL_PORT: " "$POWER_RELAY_SERIAL_PORT"
printf "%24s%-s\n" "DOWNLOAD_PATH: " "$DOWNLOAD_PATH"
printf "%24s%-s\n" "AUTO_IMAGE: " "$AUTO_IMAGE"
printf "%24s%-s\n" "Test_NODE": "$HOSTNAME"
echo "============================================================================="
cd "$work_powerRelay_dir" || { echo "Failed to cd into $work_powerRelay_dir"; exit 1; }
#get image download url
if [[ $Test_UPSTEAM_PRJ_URL =~ 'jenkins' ]]; then
    echo "wget $Test_UPSTEAM_PRJ_URL -O Build.html"
    wget $Test_UPSTEAM_PRJ_URL -O Build.html
    echo "wget $Test_UPSTEAM_PRJ_URL/injectedEnvVars/api/json?pretty=true -O parameter.json"
    wget $Test_UPSTEAM_PRJ_URL/injectedEnvVars/api/json?pretty=true -O parameter.json
    Test_IMAGE_URL=$(grep -Eo "href=\"http:\S+Download Firmware" Build.html)
    Test_IMAGE_URL=${Test_IMAGE_URL#*\"}
    if [[ "$Test_SERIES" == "Android_U" ]]; then
        Test_IMAGE_URL=${Test_IMAGE_URL%\"*}'/signed_image/'
    else
        Test_IMAGE_URL=${Test_IMAGE_URL%\"*}'/'
    fi
    wget $Test_IMAGE_URL -O Download.html
    if [[ $UPGRADE_MODE =~ "fastboot" ]]; then
        if [[ $Test_SERIES =~ "Boreal" ]];then
            Test_Package=$(cat Download.html | grep -oP "boreal-fastboot-flashall-\S+?.zip" | head -n 1)
            Test_IMAGE_URL=$Test_IMAGE_URL$Test_Package
        fi
    elif [[ $UPGRADE_MODE =~ "adnl" ]]; then
        Test_Package=$(grep -oP "aml_upgrade_img-\S+?.tar.bz2" Download.html | head -n 1)
    fi
    echo "Test_Package:$Test_Package"
    Test_PROJECT_NAME=$(jq .envMap.BOARD parameter.json | sed 's/\"//g')
    Test_BUILD_ARCH=$(jq .envMap.BUILD_ARCH parameter.json | sed 's/\"//g')
    Test_BUILD_VARIANT=$(jq .envMap.BUILD_VARIANT parameter.json | sed 's/\"//g')
    Test_BUILD_TYPE=$(jq .envMap.BUILD_TYPE parameter.json | sed 's/\"//g')
    Test_BUILD_KERNEL_ARCH=$(jq .envMap.KERNEL_BUILD_ARCH parameter.json | sed 's/\"//g')
    Test_BUILD_NUMBER=$(jq .envMap.BUILD_NUMBER parameter.json | sed 's/\"//g')
    Test_BUILD_INFO=${Test_PROJECT_NAME}-${Test_BUILD_VARIANT}-android${Test_BUILD_ARCH}-kernel${Test_BUILD_KERNEL_ARCH}-${Test_BUILD_TYPE}-${Test_BUILD_NUMBER}
else
    echo "URL not supported yet! Please change URL!"
    exit 1
fi
# Power off/on DUT
if [[ $POWER_RELAY_SERIAL_PORT != "NULL" ]];then
    $WORKSPACE/AutoTestRes/bin/powerRelay $POWER_RELAY_SERIAL_PORT all off
    sleep 2
    $WORKSPACE/AutoTestRes/bin/powerRelay $POWER_RELAY_SERIAL_PORT all on
    if [[ ${Test_SERIES} =~ "Android" ]]; then
        sleep 90
    else
        sleep 60
    fi
fi

cd $WORKSPACE/

chmod 777 -R AutoTestRes/scripts
echo "AutoTestRes/scripts/shell/load_test_certification.sh -b ${BUILD_NUMBER} \
-d ${DUT_ADB_SN} \
-f ${Test_SERIES} \
-i ${Test_BUILD_INFO} \
-j ${UPGRADE_MODE} \
-m ${Test_IMAGE_URL} \
-n ${Test_BUILD_NUMBER} \
-o ${DUT_SERIAL_PORT_BAUDRATE} \
-p ${Test_PROJECT_NAME} \
-q ${JOB_URL} \
-r ${POWER_RELAY_SERIAL_PORT} \
-s ${DUT_SERIAL_PORT} \
-u ${TESTPLAN} \
-v ${Test_BUILD_VARIANT} \
-y ${work_powerRelay_dir} \
-w ${WORKSPACE}"

bash AutoTestRes/scripts/shell/load_test_certification.sh -b ${BUILD_NUMBER} \
-d ${DUT_ADB_SN} \
-f ${Test_SERIES} \
-i ${Test_BUILD_INFO} \
-j ${UPGRADE_MODE} \
-m ${Test_IMAGE_URL} \
-n ${Test_BUILD_NUMBER} \
-o ${DUT_SERIAL_PORT_BAUDRATE} \
-p ${Test_PROJECT_NAME} \
-q ${JOB_URL} \
-r ${POWER_RELAY_SERIAL_PORT} \
-s ${DUT_SERIAL_PORT} \
-u ${TESTPLAN} \
-v ${Test_BUILD_VARIANT} \
-y ${work_powerRelay_dir} \
-w ${WORKSPACE}

cd $WORKSPACE/

end_time_seconds=$(date +%s)
end_time=$(date +"%Y/%m/%d %H:%M:%S")
echo "Job the first board end at: ${end_time}"
