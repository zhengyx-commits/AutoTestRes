#!/bin/bash
if [ $# -lt 1 ]; then
    echo "Must pass the sudo password!"
    exit 1
fi
SUDO_PWD=$1
apt_install_list=("vim" "python3-pip" "git" "net-tools" "openssh-client" "openssh-server" "tox" "python3-tk" "python3-dev" "jq" "curl" "libxml2-utils" "sshpass")
get_install_list=("python-protobuf protobuf-compiler" "python-virtualenv" "virtualenv virtualenvwrapper python3-venv" "python-is-python3")
pip_install_list=("perfetto" "selenium" "PyUserInput" "pyautogui" "pykeyboard" "pyserial" "paramiko" "matplotlib")
echo "Start building XTS test environment>>>>>>>>"
echo "--------------------- Update the apt tool ---------------------"
echo $SUDO_PWD | sudo -S apt update
exit_code=$?
if [[ $exit_code -ne 0 ]];then
	if [[ -d /var/lib/dpkg/updates || -d /var/lib/dpkg/info || -d /var/lib/dpkg/alternatives || -e /var/lib/dpkg/status ]];then	
		echo $SUDO_PWD | sudo -S cp /etc/apt/sources.list /etc/apt/sources.list.bak
		echo $SUDO_PWD | sudo -S cp sources.list /etc/apt/sources.list
		echo $SUDO_PWD | sudo -S apt update
	else
		echo $SUDO_PWD | sudo -S mkdir -p /var/lib/dpkg/updates
		echo $SUDO_PWD | sudo -S mkdir -p /var/lib/dpkg/info 
		echo $SUDO_PWD | sudo -S mkdir -p /var/lib/dpkg/alternatives
		echo $SUDO_PWD | sudo -S touch /var/lib/dpkg/status
		echo $SUDO_PWD | sudo -S apt update
	fi
fi
echo $SUDO_PWD | sudo -S apt-get upgrade --fix-missing -y

echo "--------------------- Check java version ---------------------"
java_version=$(java -version 2>&1 | awk -F '"' '/version/ {print $2}')
if [[ $java_version == 11* ]]; then
    echo "Java JDK 11 has installed"
else
    echo $SUDO_PWD | sudo -S apt install -y openjdk-11-jdk
fi

echo "--------------------- Check python3 version ---------------------"
python_version=$(python3 --version | awk '{print $2}')
IFS='.' read -ra version_parts <<< "$python_version"
major=${version_parts[0]}
minor=${version_parts[1]}
if [[ $major -lt 3 || ($major -eq 3 && $minor -lt 8) ]]; then
    echo $SUDO_PWD | sudo apt install -y python3.8
    echo $SUDO_PWD | sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1
    echo $SUDO_PWD | sudo ln -s /usr/bin/python3 /usr/bin/python
    echo "Python update finished"
else
    echo "Python don't need to update"
fi

for apt_install_tools in ${apt_install_list[*]}
do

	echo "--------------------- Install $apt_install_tools  ---------------------"
	echo $SUDO_PWD | sudo -S apt install -y $apt_install_tools
done

for get_install_tools in ${get_install_list[*]}
do

	echo "--------------------- Install $get_install_tools  ---------------------"
	echo $SUDO_PWD | sudo -S apt-get install -y $get_install_tools
done
echo "--------------------- install nodejs ---------------------"
echo $SUDO_PWD | curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
echo $SUDO_PWD | sudo apt-get install -y nodejs
echo "--------------------- Update the pip tool ---------------------"
python3 -m pip install --upgrade pip
pip3 install update
for pip_install_tools in ${pip_install_list[*]}
do
	echo "--------------------- Install $pip_install_tools  ---------------------"
	pip3 --default-timeout=300 install --quiet $pip_install_tools
done
echo "--------------------- install bazel ---------------------"
bazel_folder="$HOME/bazel"
wget https://github.com/bazelbuild/bazel/releases/download/6.2.1/bazel-6.2.1-installer-linux-x86_64.sh -P "$bazel_folder"
chmod a+x "$bazel_folder"/bazel-6.2.1-installer-linux-x86_64.sh
bash "$bazel_folder"/bazel-6.2.1-installer-linux-x86_64.sh --user
bazel --version
echo "--------------------- Set up adb and aapt tools ---------------------"
server_address="10.18.11.98"
build_tools_file_path="/Resource/AndroidSDK/build-tools.zip"
platform_tools_file_path="/Resource/AndroidSDK/platform-tools.zip"
target_folder="$HOME/AndroidSDK"
mkdir -p "$target_folder"
echo "Downloading build-tools.zip..."
wget "http://$server_address$build_tools_file_path" -P "$target_folder"
echo "Downloading platform-tools.zip..."
wget "http://$server_address$platform_tools_file_path" -P "$target_folder"
unzip -q "$target_folder/build-tools.zip" -d "$target_folder"
unzip -q "$target_folder/platform-tools.zip" -d "$target_folder"
rm "$target_folder/build-tools.zip"
rm "$target_folder/platform-tools.zip"
echo $SUDO_PWD | sudo chmod -R +777 "$target_folder/platform-tools"
echo $SUDO_PWD | sudo chmod -R +777 "$target_folder/build-tools"
sudo ln -s "$target_folder"/platform-tools/adb /usr/bin/adb
sudo ln -s "$target_folder"/platform-tools/fastboot /usr/bin/fastboot
sudo ln -s "$target_folder"/build-tools/33.0.1/aapt /usr/bin/aapt
sudo ln -s "$target_folder"/build-tools/33.0.1/aapt2 /usr/bin/aapt2
sleep 5
echo $(adb --version)
echo $(aapt version)
echo $(aapt2 version)
echo "Building XTS test environment finished>>>>>>>>"
