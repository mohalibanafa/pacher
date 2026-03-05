# Cloud Patcher v2.0 | Technical Documentation

A professional web-based utility designed for binary patching and high-efficiency decompression. This system utilizes advanced algorithms to facilitate file updates and extractions across multiple environments, including Windows and Android (Termux).

---

## 📋 Project Overview

**Cloud Patcher** provides a centralized interface for managing binary differential updates and compressed archives. By leveraging pure Python implementations, the system ensures cross-platform compatibility without the need for complex system-level dependencies.

### Core Functionalities:
1.  **Binary Differential Patching**: Utilizing the **BSDIFF4** algorithm to apply incremental updates to existing files with high precision.
2.  **Archive Decompression**: Integrated **LZMA** engine for processing `.xz` archives, ensuring optimal compression ratios.
3.  **Output Management**: Automated packaging of processed files into `.zip` archives, accompanied by technical metadata and integrity signatures.

---

## ⚙️ Technical Specifications

-   **Autonomous Dependency Resolution**: The system automatically detects missing environment libraries (e.g., Flask, Requests) and performs a silent installation during the initial execution.
-   **Pure Python Architecture**: Developed entirely in Python to eliminate reliance on external C-extensions, ensuring stability across architectural variants.
-   **Integrity Verification Engine**: Automatic generation of **SHA256** and **MD5** checksums for all input and output files to guarantee data consistency.
-   **Automated Lifecycle Management**: An internal scheduled task cleanses temporary directories and output folders (removing files older than 60 minutes) to maintain storage efficiency.

---

## 🛠️ Usage Workflow (Step-by-Step)

The application follows a streamlined operational sequence:

1.  **Operational Mode Selection**: Choose between the **Patching** tab (applying updates) or the **Extraction** tab (decompressing files).
2.  **File Input**:
    *   *Patching Mode*: Upload the compressed patch file (`.xz`) and the corresponding original file to be updated.
    *   *Extraction Mode*: Upload the target `.xz` archive.
3.  **Process Execution**: Trigger the processing engine via the action button. The interface will provide real-time status logs during execution.
4.  **Verification & Retrieval**: Review the generated integrity hashes (MD5/SHA256) in the log area. Upon completion, the system will automatically package the results and initiate a download of the final `.zip` bundle.

---

## 🚀 Deployment Instructions

### 💻 Windows Environment

#### 1️⃣ Setup and Execution
1. Ensure [Python 3.x](https://www.python.org/downloads/) is installed and added to the system PATH.
2. Download the project and extract the contents.
3. Double-click `main.py` or run it via Terminal using:
   ```cmd
   python main.py
   ```
4. **Note**: The application will automatically verify the environment and install required libraries (Flask, Requests, etc.) during the first execution, then launch the interface in your browser.

---

### 📱 Android (Termux) Environment

#### 1️⃣ First-Time Setup and Launch
Copy the following command to initialize the environment (update system and install requirements) and start the application directly:
```bash
pkg update -y && pkg install git python -y && git clone https://github.com/mohalibanafa/pacher.git && cd pacher && python main.py
```

#### 2️⃣ Daily Usage
After the initial setup, you can launch the application later by simply running:
```bash
cd pacher
python main.py
```
- The application is self-sufficient and manages its own dependencies without external scripts.
- Access the interface via your mobile browser at: `http://localhost:5000`.

---

## 📁 System Architecture

```text
patcher/
├── pacher/                 # Main application directory
│   ├── main.py            # Primary server logic and algorithms
│   ├── templates/         # HTML structure (Jinja2)
│   ├── static/            # Static assets (CSS/JS)
│   └── outputs/           # Volatile output storage
└── README.md              # Technical documentation
```

---

## 🔍 Technical Logic and Algorithms

-   **BSDIFF4 Implementation**: The patching engine calculates the difference between binary files, allowing for significantly smaller update payloads.
-   **LZMA Decompression**: Handles the extraction of `.xz` headers and data blocks efficiently.
-   **Multi-threading**: Offloads heavy processing tasks to background threads to maintain a responsive web UI.

---

## 📝 Frequently Asked Questions (FAQ)

**Q: Is the data processing localized?**  
A: Yes. All file processing occurs strictly within the local environment. No data is transmitted to external servers or cloud storage.

**Q: Connectivity issues in Termux?**  
A: Ensure that you have updated the package manager and granted storage permissions via `termux-setup-storage`.

**Q: Performance on large datasets?**  
A: The system implements chunked data reading to process files larger than the available physical RAM, ensuring scalability.

---
*Developed for efficient cross-platform binary file management.*
