#!/bin/bash
#/*
# * \file        aml_update_whole_package.sh
# * \brief
# *
# * \version     1.6
# * \date        2019/09/6
# * \author      Sam.Wu <yihui.wu@amlgic.com>
# * \edit        Updated by qinqi.shi@amlogic.com
# *
# * Copyright (c) 2017 Amlogic. All Rights Reserved.
# *
# */
#set -x  #expand and print cmd before execute
set -e  #exit if get error

shellDir=$(cd `dirname $0`; pwd)
PWD=`pwd`
printf "working dir [%s], shell dir[%s]\n" ${PWD} ${shellDir}

usage="Usage:$0 burnPkgPath <skipboot=true> <dev##> <secure=auto>"
###0, check parameters is valid
###0,######
if [ "$#" -lt "1" ]; then
    echo $usage
    exit 1
fi
burnPkgPath=$1
if [ ! -f  $burnPkgPath ];then
    printf "burnPkgPath(%s) in argv[1] invalid\n", ${burnPkgPath}
    exit 1
fi
##change path of burnPkgPath to absolute if relative
case ${burnPkgPath} in
    /*);; ##Already absolute
    *) burnPkgPath="${PWD}/${burnPkgPath}";;
esac

usrPath="$3"
if [ -z "$usrPath" ]; then
    devIndex="dev00"
fi

if [ -z  "$devIndex" ]; then
    devIndex=`echo $usrPath | sed -n "s/^\(dev[0-9]\{1,2\}\)$/\1/p"`
fi
if [ "4" -eq "${#devIndex}" ]; then
    devIndex="dev0${devIndex:3}"
fi
echo devIndex is ${devIndex:-null}

if [ -z  "$devPath" ]; then
    devPath=`echo $usrPath | sed -n "s/^\(path-Bus.*\)$/\1/p"`
fi
if [ -z "$chipid" ]; then
    devChipId=`echo $usrPath | sed -n "s/^\(chip-[0-9a-f]\{24\}\)$/\1/p"`
fi
if [ -z  "$devIndex" ] && [ -z "$devPath" ] && [ -z "$devChipId" ]; then
    echo "usrPath [${usrPath}] fmt err"
    exit 1
fi

devSecure=${4:-auto}
if [ "$devSecure" != false ] && [ "$devSecure" != true ] && [ "$devSecure" != auto ];then
    printf "argv[3] must be true/false/auto, (%s) invalid\n" ${devSecure}
    exit 1
fi

skipBoot=${2:-true}

update_tool=${shellDir}/update

pwdFile=${shellDir}/luan-password.bin
upgradeDutStatusLogFile=${shellDir}/upgradeDutStatuslLog.txt
unpack_tool=${shellDir}/aml_image_v2_packer
para4InitDDr=${shellDir}/usbbl2runpara_ddrinit.bin
para4runfFipImg=${shellDir}/usbbl2runpara_runfipimg.bin

if [ ! -f ${update_tool} ] || [ ! -f ${unpack_tool} ] ||
    [ ! -f ${para4InitDDr} ] || [ ! -f ${para4runfFipImg} ]; then
    ls -all ${shellDir}
    printf "some tool(s) not existed!!, Pls put it in the same tool with script file\n"
    exit 1
fi
chmod +x ${update_tool} ${unpack_tool}

#save update fail logs to file.
function f_save_update_log() {
    echo "$1 [lineno: $2]" >> $upgradeDutStatusLogFile
}

#1, check is there at least one WorldCup device
###Prompt user to plugin and make device into WorldCup mode
function f_get_devNum() {
    devNum=`${update_tool} scan \
        | awk -v FS="." \
        '/WorldCup\[/ {++devNum;} END { print devNum}'`
    if [ "0" -eq "$devNum" ]; then
        lsusb
        printf "There isn't Amlogic WorldCup device detected, pls plug usb cable to pc and make device in burning mode"
        f_save_update_log "Fail in burnning image: There isn't Amlogic WorldCup device detected, pls plug usb cable to pc and make device in burning mode" $LINENO;
        exit 1
    fi
    echo "update devNum to ${devNum}"
}

function f_find_devPath_via_devIndex() {
    echo "devIndex: ${devIndex:4}, devnum ${devNum}"
    if [ "${devIndex:4}" -ge "${devNum}" ]; then
        printf "devindex[%d] >= devnum[%d] is invalid\n" ${devindex:4} ${devNum}
        f_save_update_log "Fail in burnning image: devindex[%d] >= devnum[%d] is invalid\n ${devindex:4} ${devNum}" $LINENO;
        exit 1
    fi
    devPath=`${update_tool} scan  | \
        awk -v devIndex="WorldCup[${devIndex:3}]" -v FS="." \
        'devIndex == $1 {print "path-" $2}'`
    echo "find devPath[$devPath] via devIndex[$devIndex]"
}

function f_find_devIndex_via_devPath() {
    devIndex=$(
    ${update_tool} scan |\
        awk -v FS="[\]\[.]" -v path=${devPath:5} '$NF == path {print $2}'
    )
}

function f_get_fwVer() {
    echo "devPath is [$devPath]"
    fullVer=$(${update_tool} identify "${devPath}" |\
         awk '/This firm/ {print $NF}')
    if [ -z "$fullVer" ]; then
        echo "IdentifyHost fail, try again."
        sleep 3
        fullVer=$(${update_tool} identify "${devPath}" |\
             awk '/This firm/ {print $NF}')
        if [ -z "$fullVer" ]; then
            echo "fail in identifyHost"
            f_save_update_log "Fail in burnning image: Fail in identifyHost" $LINENO;
            exit 1
        fi
    fi
    fwVer=$( echo $fullVer | \
        awk -F- 'BEGIN{fwVer["0"]="romcode"; fwVer["8"]="spl"; fwVer["16"]="tpl"} \
        {v1=$NF; v2=$(NF-1); \
            if ( v1 in fwVer ) {if(8 == v1 && v2 == 1)print "spl-v2"; else print fwVer[v1];}}')
}

tempdir4Unpack=`cd $(mktemp -d); pwd`
flagAddr=0x7300000
flagFile=$(mktemp -p ${tempdir4Unpack})

function f_update_path_via_flag() { #find devices only on uboot stage
    thisTmp=${flagFile}.dump
    devPath=$(\
    ${update_tool} scan | awk -F. '/WorldCup/ {print $2}' |
    while read aLine; do
        thisPath="path-${aLine}"
        fwVer=`${update_tool} identify "${thisPath}" | awk '/firmware/ {print $NF}'`
        #echo "fwVer[${fwVer}] of path[${thisPath}]"
        if [ "16" != "${fwVer:6}" ]; then continue; fi
        #echo "update mread mem ${flagAddr} normal ${flagFileSz} ${thisTmp}"
        ${update_tool} mread "${thisPath}" mem ${flagAddr} normal ${flagFileSz} ${thisTmp} > /dev/null
        if cmp -s ${flagFile} ${thisTmp}; then 
            echo "$thisPath"; 
            #echo "find path [$devPath]"
            exit 0
        fi
    done;)
}

function f_find_devPath_via_chipid_() { #find devices only on bl1 / romboot stage
    chipid=0x${devChipId:5}
    echo "usr chipid is ${chipid}"
    devPath=$(lsusb | awk -v FS=" Amlogic," '/1b8e:c003/ {print $1}' |\
    while read aLine; do
        thisPath="path-${aLine}"
        fwVer=`${update_tool} identify "${thisPath}" | awk -F- '/firmware/ {print $NF}'`
        case "${fwVer}" in
            "0")
                thisChipId=$(${update_tool} chipid "${thisPath}" | \
                    awk -F: '/ChipID/ {print $2}' )
                if [ "$thisChipId" = "$chipid" ]; then 
                    echo ${thisPath}; 
                    break;
                fi
                ;;
            "16")
                thisChipId=0x$(${update_tool} bulkcmd "${thisPath}" "get_chipid"| \
                    awk -F: '/success:/ {print $NF}' )
                if [ "$thisChipId" = "$chipid" ]; then
                    echo ${thisPath};
                    break;
                fi
                ;;
            "*")
                ;;
        esac
            done;)
    # if [ -z "$devPath" ]; then
    #     echo "Fail in find dev path via chipid"
    #     f_save_update_log "Fail in burnning image: Fail in find dev path via chipid" $LINENO;
    #     exit 1
    # fi
}

function f_find_devPath_via_chipid() { #find devices only on bl1 / romboot stage
    chipid=0x${devChipId:5}
    echo "usr chipid is ${chipid}"
    devPath=$(\
    lsusb | awk -v FS=" Amlogic," '/Amlogic, Inc/ {print $1}' |\
    while read aLine; do
        thisPath="path-${aLine}"
        fwVer=`${update_tool} identify "${thisPath}" | awk '/firmware/ {print $NF}'`
        #echo "fwVer[${fwVer}] of path[${thisPath}]"
        if [ "0" != "${fwVer:6}" ]; then continue; fi
        #echo "update mread mem ${flagAddr} normal ${flagFileSz} ${thisTmp}"
        thisChipId=$(${update_tool} chipid "${thisPath}" | \
            awk -F: '/ChipID/ {print $2}' )
        if [ "$thisChipId" = "$chipid" ]; then
            echo ${thisPath};
            break;
        fi
    done;)
    if [ -z "$devPath" ]; then
        echo "fail in find dev path via chipid"
        f_save_update_log "Fail in burnning image: Fail in find dev path via chipid" $LINENO;
        exit 1
    fi
}

f_get_devNum

if [ -z "$devPath" ]; then
    if [ ! -z "$devIndex" ]; then
        f_find_devPath_via_devIndex
        if [ -z "$devPath" ]; then
            echo "Get devPath fail, sleep 5 seconds try again."
            sleep 5
            f_find_devPath_via_devIndex
        fi
    elif [ ! -z "$devChipId" ]; then
        f_find_devPath_via_chipid_
    else
        echo "exception!! cannot find devPath as index and chipid none"
    fi
    if [ -z "$devPath" ]; then
        echo "Fail in find devPath"
        f_save_update_log "Fail in burnning image: Fail in find devPath" $LINENO;
        exit 1
    fi
fi

f_get_fwVer
if [ -z "$fwVer" ]; then
    echo "fail in get fw version"
    f_save_update_log "Fail in burnning image: Fail in get fw version" $LINENO;
    exit 1
fi
echo fwVer is ${fwVer}
if [ "true" == "$skipBoot" ]; then
    until [ "romcode" == "$fwVer" ]; do
        echo sleep 3 and update_tool bulkcmd "${devPath}" "erase_bootloader"
        sleep 3
        ${update_tool} bulkcmd "${devPath}" "erase_bootloader"
        echo update_tool bulkcmd "${devPath}" "reset"
        ${update_tool} bulkcmd "${devPath}" "reset" | awk ''
        sleep 4
        f_find_devPath_via_devIndex
        f_get_fwVer
        ${update_tool} password "${pwdFile}"
    done
fi

echo "${unpack_tool} -d ${burnPkgPath} ${tempdir4Unpack}"
${unpack_tool} -d ${burnPkgPath} ${tempdir4Unpack}
if [ ! -f "${tempdir4Unpack}/image.cfg" ];then
    printf "Failed in unpack pkg(%s) to tempdir(%s)\n" ${burnPkgPath} ${tempdir4Unpack}
    f_save_update_log "Fail in burnning image: Failed in unpack pkg(%s) to tempdir(%s)\n ${burnPkgPath} ${tempdir4Unpack}" $LINENO;
    exit 1
fi

echo "para encrypt is ${devSecure}"
Encrypt_reg=`awk -F: '/Encrypt_reg/ {print $2}' ${tempdir4Unpack}/platform.conf`
if [ "$devSecure" == "auto" ] ; then
    #${update_tool} rreg "${devPath}" 4 ${Encrypt_reg}
    devSecure=`${update_tool} rreg "${devPath}" 4 ${Encrypt_reg} | \
        awk '$1 ~ "[0-9A-F]+:" {print "0x" $2}'`
    echo "Encrypt_reg[$Encrypt_reg], devSecure[$devSecure]"
    devSecure=`if (( devSecure & (1<<4) )); then echo true; else echo flase; fi`
    echo "change devSecure from auto to ${devSecure}"
fi

pkgSecure=false
if [ -f ${tempdir4Unpack}/_aml_dtb.PARTITITION ] && [ -f ${tempdir4Unpack}/meson1.dtb ]; then
    pkgSecure=true
fi
#for usb_dtb, if pakckage signed, both meson1.dtb and _aml_dtb.PARTITITION existed
##############else only _aml_dtb.PARTITITION existed
if [ "$devSecure" == true ] ; then
    USB_DTB=meson1_ENC
else
    USB_DTB=meson1
fi

if [ "romcode" == "$fwVer" ]; then
    tmp="DDR UBOOT"
    bootItems=""
    for item in $(echo $tmp); do
        if [ "true" == "${devSecure}" ]; then
            item="${item}_ENC"
        fi
        file=`awk -F[\"=] -v it="$item" '/file=/ {if (it==$9 && "USB"==$6) print $3;}' ${tempdir4Unpack}/image.cfg`
        item="${tempdir4Unpack}/${file}"
        bootItems="${bootItems},${item}"
    done
    printf "bootItems ${bootItems}\n"
    USB_DDR=`echo ${bootItems} | awk -F, '{print $2}'`
    USB_UBOOT=`echo ${bootItems} | awk -F, '{print $3}'`
    #USB_DTB=`echo {bootItems} | awk -F, '{print $4}' | sed -n 's/\(meson1*\.\)USB/\1dtb/p'`
    if [ ! -f ${USB_DDR} ] || [ ! -f ${USB_UBOOT} ];then
        printf "items for usb boot not enough, check your package\n"
        rm -rf ${tempdir4Unpack}
        f_save_update_log "Fail in burnning image: items for usb boot not enough, check your package" $LINENO;
        exit 1
    fi
    sramBase=`awk -F: '/DDRLoad/ {print $2}' ${tempdir4Unpack}/platform.conf`
    paraAddr=`awk -F= '/bl2ParaAddr/ {print $2}' ${tempdir4Unpack}/platform.conf`
    ddrSize=`awk -F: '/DDRSize/ {print $2}' ${tempdir4Unpack}/platform.conf`

    if [ -n "${paraAddr}" ];then
        echo "[cwr] \"${devPath}\" ${para4InitDDr} ${paraAddr}"
        ${update_tool} cwr "${devPath}"  ${para4InitDDr} ${paraAddr}
    elif [ -z "${devChipId}" ];then
        devChipId=$(${update_tool} chipid "${devPath}" | awk -F: '/ChipID/ {print $2}')
        devChipId="chip-${devChipId:2}"
        printf "get chipid %s\n" $devChipId
    fi
    echo "[write] \"${devPath}\"  ${USB_DDR} ${sramBase} ${ddrSize}"
    ${update_tool} write "${devPath}"  ${USB_DDR} ${sramBase} ${ddrSize}
    echo "[run] \"${devPath}\"  ${sramBase}"
    ${update_tool} run "${devPath}"  ${sramBase}
    f_get_fwVer

    if [ "spl-v2" == "$fwVer" ]; then
        echo "[bl2_boot] \"${devPath}\"  ${USB_UBOOT}"
        ${update_tool} bl2_boot "${devPath}"  ${USB_UBOOT}
        sleep 3 #wait for uboot plug-in
        f_find_devPath_via_chipid_

        if [ -z "$devPath" ]; then
            echo "Get devChipId fail, sleep 5 seconds try again."
            sleep 5
            f_find_devPath_via_chipid_
        fi

        if [ -z "$devPath" ]; then
            echo "Fail in find dev path via chipid"
            f_save_update_log "Fail in burnning image: Fail in find dev path via chipid" $LINENO;
            exit 1
        fi

    else
        cmdRunAddr=${sramBase}
        if [ "spl" == "$fwVer" ]; then
            echo "usb protocol is NEW"
            cmdRunAddr=${paraAddr}
            echo "[run] \"${devPath}\"  ${cmdRunAddr}"
            ${update_tool} run "${devPath}"  ${cmdRunAddr}
            sleep 1s
        else
            sleep 1s
            echo "[write] \"${devPath}\"  ${USB_DDR} ${sramBase}"
            ${update_tool} write "${devPath}"  ${USB_DDR} ${sramBase}
        fi

        echo "[write] \"${devPath}\"  ${para4runfFipImg} ${paraAddr}"
        ${update_tool} write "${devPath}"  ${para4runfFipImg} ${paraAddr}
        echo "[write] \"${devPath}\"  ${USB_UBOOT} 0x0200c000"
        ${update_tool} write "${devPath}"  ${USB_UBOOT} 0x0200c000

        ##setup unique flagFile before switch to uboot mode
        dd if=/dev/random of=${flagFile} bs=1 count=8
        echo "${update_tool} write ${flagFile} ${flagAddr}"
        ${update_tool} write "${devPath}" ${flagFile} ${flagAddr}

        echo "[run] \"${devPath}\"  ${cmdRunAddr}"
        ${update_tool} run "${devPath}"  ${cmdRunAddr}
        sleep 5
    fi
fi

flagFileSz=$(du -b ${flagFile} | awk '{print $1}')
echo "flagFileSz is ${flagFileSz}"
if [ "0" -lt "${flagFileSz}" ]; then
    f_update_path_via_flag
    echo "devPath is ${devPath}"
    if [ -z "$devPath" ]; then
        echo "Fail in update devPath"
        f_save_update_log "Fail in burnning image: Fail in update devPath" $LINENO;
        exit 1
    fi
    echo "update devPath to [$devPath]"
fi

####Init and erasing flash
dtbFile=`awk -v sub_type="${USB_DTB}" -F[=\"] '$9 == sub_type {print $3}' ${tempdir4Unpack}/image.cfg`
if [ -z "$dtbFile" ]; then
    printf "dtbFile not found\n"
    f_save_update_log "Fail in burnning image: dtbFile not found" $LINENO;
    exit 1
fi
dtbFile=${tempdir4Unpack}/${dtbFile}
echo "[mwrite] \"${devPath}\"  ${dtbFile} mem dtb normal"
${update_tool} mwrite "${devPath}"  ${dtbFile} mem dtb normal
sleep 3 
echo "[bulkcmd] \"${devPath}\"  "disk_initial 1""
${update_tool} bulkcmd "${devPath}"  "disk_initial 1"

#echo "[bulkcmd] \"${devPath}\"  "store erase boot 0 0x60000""
#${update_tool} bulkcmd "${devPath}"  "store erase boot 0 0x60000"

#echo "[bulkcmd] \"${devPath}\"  "store write data 0x1080000 0 0x6000000""
#${update_tool} bulkcmd "${devPath}"  "store write data 0x1080000 0 0x6000000"

cat ${tempdir4Unpack}/image.cfg | awk -v mainType="PARTITION" -v dir="${tempdir4Unpack}/" -F"[=\"]" \
    '$6 == mainType {partsPath[$9] = dir $3; partsFmt[$9] = NF > 12 ? $12 : "auto"} \
    END{for(partName in partsPath) \
    if ("bootloader" != partName) print partName "," partsPath[partName] "," partsFmt[partName];\
    if ("bootloader" in partsPath) print "bootloader" "," partsPath["bootloader"] "," partsFmt["bootloader"]}' \
    | while read aLine; do
        partName=`echo $aLine | awk -F, '{print $1}'`
        partImg=`echo $aLine | awk -F, '{print $2}'`
        fileType=`echo $aLine | awk -F, '{print $3}'`
        if [ "auto" == "fileType" ]; then fileType=""; fi
        printf "\nFlashing :"
        echo "[partition] \"${devPath}\"  ${partName} ${partImg} ${fileType}"
        ${update_tool} partition "${devPath}"  ${partName} ${partImg} ${fileType}
    done

rm -rf ${tempdir4Unpack}/*

echo "${update_tool} bulkcmd \"${devPath}\" save_setting"
${update_tool} bulkcmd "${devPath}"  "save_setting"

f_save_update_log "Upgrade image successful!" $LINENO;

printf "\npkg[%s] programming successful^_^\n" ${burnPkgPath}

${update_tool} bulkcmd "reset"
