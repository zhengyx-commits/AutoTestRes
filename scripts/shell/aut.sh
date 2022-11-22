#!/bin/bash

sudo_pwd=123456 #The password for sudo permissions
git_code_cmd='git://git.myamlogic.com/amlogic/tools/AutoTestRes.git' #Requires IT authorization to access myamlogic.com
git_code_branch=release

apt_install_list=("vim" "python3-pip" "git" "net-tools" "openssh-client" "openssh-server" "tox" "python3-tk" "python3-dev")

pip_install_list=("pytest" "PrettyTable" "lxml" "pyhtml" "setuptools")

echo "--------------------- Update the apt tool ---------------------"
echo $sudo_pwd | sudo -S apt update
if [[ $? -ne 0 ]];then

	if [[ -d /var/lib/dpkg/updates || -d /var/lib/dpkg/info || -d /var/lib/dpkg/alternatives || -e /var/lib/dpkg/status ]];then
		
		echo $sudo_pwd | sudo -S cp /etc/apt/sources.list /etc/apt/sources.list.bak
		echo $sudo_pwd | sudo -S cp sources.list /etc/apt/sources.list
		echo $sudo_pwd | sudo -S apt update
	
	else
		
		echo $sudo_pwd | sudo -S mkdir -p /var/lib/dpkg/updates
		echo $sudo_pwd | sudo -S mkdir -p /var/lib/dpkg/info 
		echo $sudo_pwd | sudo -S mkdir -p /var/lib/dpkg/alternatives
		echo $sudo_pwd | sudo -S touch /var/lib/dpkg/status
		
		echo $sudo_pwd | sudo -S apt update
		
	fi	

fi
echo $sudo_pwd | sudo -S apt-get upgrade --fix-missing -y

for apt_install_tools in ${apt_install_list[*]}
do

	echo "--------------------- Install $apt_install_tools  ---------------------"
	echo $sudo_pwd | sudo -S apt-get install $apt_install_tools -y

done


echo "--------------------- Update the pip tool ---------------------"
python3 -m pip install --upgrade pip
pip3 install update

for pip_install_tools in ${pip_install_list[*]}
do

	echo "--------------------- Install $pip_install_tools  ---------------------"
	pip3 --default-timeout=200 install $pip_install_tools

done

