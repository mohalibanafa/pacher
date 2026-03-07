# pacher

A professional web-based utility for high-efficiency binary differential patching (BSDIFF4) and LZMA extraction.

<div align="center">

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mohalibanafa/pacher/blob/main/patcher.ipynb)

</div>

## 🧩 How It Works (Overview)

The project consists of two complementary components that work together to create and apply patches efficiently. You do not need technical expertise to use either part. Here is how they interact:

- **`pacher.ipynb` (The Developer Tool / Patch Creator)**: This Google Colab notebook runs on the cloud and handles the heavy lifting of creating patch files. It takes the original file and the modified file, calculates the structural differences, and compresses the result using LZMA to generate a tiny patch file. This utilizes Google's fast cloud servers for the demanding creation process.

- **`main.py` (The Client Engine / Patch Applicator)**: This is the application designed for the end-user. It runs completely locally on the user's device. When someone wants to update their file, they run this script, which automatically prepares a local server and applies the patch locally using a pure Python algorithm without requiring complex external patching software.

## 🚀 Installation & Setup

### 💻 Windows
1. **Prerequisites**: Install [Python 3.x](https://www.python.org/downloads/) and ensure it is added to your PATH.
2. **Installation**: Download this repository and extract it to your desired folder.
3. **Execution**: Run `python main.py` in the terminal or double-click `main.py`.

---

### 🐧 Ubuntu
1. **Prerequisites**: Update your system and install Python and Git:
   ```bash
   sudo apt update && sudo apt install python3 python3-pip git -y
   ```
2. **Installation**: Clone the repository:
   ```bash
   git clone https://github.com/mohalibanafa/pacher.git && cd pacher
   ```
3. **Execution**: Run the application:
   ```bash
   python3 main.py
   ```

---

### 📱 Termux
1. **Prerequisites**: Update packages and install Python and Git:
   ```bash
   pkg update -y && pkg install python git -y
   ```
2. **Installation**: Clone the repository:
   ```bash
   git clone https://github.com/mohalibanafa/pacher.git && cd pacher
   ```
3. **Execution**: Run the application:
   ```bash
   python main.py
   ```

## 📝 Note
The application automatically installs required libraries (Flask, Requests, etc.) on the first run. Access the interface at `http://localhost:5000`.
