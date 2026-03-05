#!/data/data/com.termux/files/usr/bin/bash

# Cloud Patcher Termux Setup Script 📱
# ------------------------------------

echo -e "\e[1;34m[*] Updating Termux repositories...\e[0m"
pkg update -y && pkg upgrade -y

echo -e "\e[1;34m[*] Installing requirements (Python, Clang, OpenSSL)...\e[0m"
pkg install python git clang openssl -y

echo -e "\e[1;34m[*] Installing necessary libraries...\e[0m"
pip install --upgrade pip
pip install flask requests certifi chardet idna urllib3

# Check file location
if [ -f "pacher/main.py" ]; then
    TARGET="pacher/main.py"
elif [ -f "main.py" ]; then
    TARGET="main.py"
else
    echo -e "\e[1;31m[!] Error: main.py file not found\e[0m"
    exit 1
fi

echo -e "\e[1;32m[+] Everything is ready! Starting Cloud Patcher...\e[0m"
echo -e "\e[1;33m[*] Server will run on: http://localhost:5000\e[0m"
python $TARGET
