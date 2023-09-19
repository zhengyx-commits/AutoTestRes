#!/bin/bash
if [ $# -lt 1 ]; then
    echo "Must pass the sudo password!"
    exit 1
fi
sudo_pwd=$1 #The password for sudo permissions
git_code_cmd='git://git.myamlogic.com/amlogic/tools/AutoTestRes.git' #Requires IT authorization to access myamlogic.com
git_code_branch=release

max_reinstall_attempts=3
reinstall_attempts=0

apt_install_list=("vim" "python3-pip" "git" "net-tools" "openssh-client" "openssh-server" "tox" "python3-tk" "python3-dev" "ffmpeg" "jq" "fastboot" "curl" "vlc" "apache2" "openssl" "libssl-dev")

pip_install_list=("pytest" "PrettyTable" "lxml" "pyhtml" "setuptools")

# Function to check if a package is installed
function is_package_installed() {
    dpkg -s "$1" &> /dev/null
}

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
    # echo $sudo_pwd | sudo -S apt-get install $apt_install_tools -y

    # Check if the package is already installed
    if is_package_installed "$apt_install_tools"; then
        echo "Package $apt_install_tools is already installed."
    else
        while [[ $reinstall_attempts -lt $max_reinstall_attempts ]]; do
            ((reinstall_attempts++))

            echo "Package $apt_install_tools is not installed. Installing (Attempt $reinstall_attempts)..."
            echo "$sudo_password" | sudo -S apt-get install "$apt_install_tools" -y

            # Check if installation was successful
            if is_package_installed "$apt_install_tools"; then
                echo "Package $apt_install_tools was installed successfully."
                break
            else
                echo "Package $apt_install_tools installation failed."
                if [[ $reinstall_attempts -lt $max_reinstall_attempts ]]; then
                    echo "Retrying installation..."
                else
                    echo "Reached maximum reinstall attempts. Aborting script execution."
                    exit 1
                fi
            fi
        done
    fi
done

echo "--------------------- Install OpenJDK ---------------------"
if is_package_installed openjdk-11-jdk; then
    echo "Package openjdk-11-jdk is already installed."
else
    sudo apt update
    sudo apt install -y openjdk-11-jdk

    echo "--------------------- Verify installation and configure environment variables ---------------------"
    JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
    if command -v java &>/dev/null; then
        echo "Java installation successful!"
        echo "Configuring environment variables..."
        echo "JAVA_HOME=$JAVA_HOME" | sudo tee -a /etc/environment
        echo "export JAVA_HOME" | sudo tee -a /etc/profile.d/java.sh
        echo "export PATH=\$PATH:\$JAVA_HOME/bin" | sudo tee -a /etc/profile.d/java.sh
        source /etc/environment
        source /etc/profile.d/java.sh
        echo "Environment variables configured successfully!"
    else
        echo "Java installation failed. Please check the installation steps."
    fi
fi

echo "--------------------- Update the pip tool ---------------------"
python3 -m pip install --upgrade pip
pip3 install update

for pip_install_tools in ${pip_install_list[*]}
do

    echo "--------------------- Install $pip_install_tools  ---------------------"
    pip3 --default-timeout=200 install $pip_install_tools

done

echo "--------------------- Install allure  ---------------------"
sudo apt-key adv --fetch-keys https://dl.yarnpkg.com/debian/pubkey.gpg
echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
sudo apt update
sudo apt install yarn -y
sudo yarn global add allure-commandline

allure --version
if [ $? -eq 0 ]; then
  echo "Allure installation successful!"
else
  echo "Allure installation failed!"
fi

echo "--------------------- Download and compile live555  ---------------------"
mkdir live555
cd live555
# Donwload from live555.com
# wget http://www.live555.com/liveMedia/public/live555-latest.tar.gz
# tar -xf live555-latest.tar.gz

# Download from file node
wget http://qa-sh.amlogic.com:8881/chfs/shared/Test_File/AUT/software/live555.tar.gz
tar -zxvf live555.tar.gz

cd live
./genMakefiles linux
make
sudo make install

cd mediaServer
./live555MediaServer &
live555_pid=$!
echo "Live555 pid is $live555_pid"
if [ $? -eq 0 ]; then
  echo "Live555 installation successful!"
else
  echo "Live555 installation failed!"
fi
kill $live555_pid

# execute command：bash aut.sh $sudo_pwd
