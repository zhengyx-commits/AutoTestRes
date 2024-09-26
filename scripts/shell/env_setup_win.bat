@echo off

REM Create a directory in C:\ and navigate to it
mkdir C:\DownloadedFiles
cd C:\DownloadedFiles

REM Call the function to download EXE files
call :DownloadExe python-3.8.10-amd64.exe
call :DownloadExe StreamXpressSetup.exe
call :DownloadExe DtaInstall.exe
call :DownloadExe DtInfoInstall.exe


REM The script will continue executing here after the function calls
echo All EXE files are ready for installation.

REM Check if Python is already installed
python --version
if %errorlevel% equ 0 (
    echo Python is already installed.
) else (
    REM Install Python
    echo Installing Python...
    start /wait python-3.8.10-amd64.exe /quiet InstallAllUsers=1 PrependPath=1

    REM Check if Python installation was successful
    python --version
    if %errorlevel% neq 1 (
        echo Python installation Succeed.
    ) else (
        echo Python installation failed. Exiting installation.
        pause
        exit
    )
)

REM Install Python dependencies (e.g., PyWinAuto)
echo Installing Python dependencies...
python -m pip install pywinauto

REM Write and run Python script for performing page click operations using WinAPI
echo Performing page click operations...
start /wait python env_setup_win.py

sc query sshd | find "RUNNING"
if not errorlevel 1 (
    echo SSH server is running.
) else (
    echo SSH server is not running.
    pause
    exit
)

if exist "C:\Program Files\DekTec" (
	echo StreamXpress is installed.
) else (
	echo StreamXpress is not installed.
	pause
	exit
)

echo Operation completed.

pause


REM Function to download EXE file using SCP
:DownloadExe
@REM set "url=%~1"
set "filename=%~1"

if "%filename%"=="" (
    echo No filename provided. Exiting.
    pause
    exit
)

echo Downloading %filename%...
if not exist %filename% (
@REM     curl -o %filename% %url%
    curl -o %filename% http://qa-sh.amlogic.com:8881/chfs/shared/Test_File/AUT/software/%filename%
) else (
    echo %filename% is already downloaded.
)

REM Check if EXE file was downloaded successfully
if not exist %filename% (
    echo Failed to download %filename%. Exiting installation.
    pause
    exit
)
goto :eof