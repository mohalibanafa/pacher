import os
import sys
import subprocess
import threading
import webbrowser
import time
import hashlib
import lzma
import bz2
import struct
import tempfile
import shutil
import json
import zipfile
from datetime import datetime

# ---------------------------------------------------------
# Automatic Dependencies Installation Function
# ---------------------------------------------------------
def install_dependencies():
    """Checks for required libraries and installs them automatically if needed."""
    required = ['flask', 'requests', 'certifi', 'chardet', 'idna', 'urllib3']
    missing = []
    
    for lib in required:
        try:
            __import__(lib)
        except ImportError:
            missing.append(lib)
            
    if missing:
        print(f"[*] The following libraries are missing: {missing}")
        print("[*] Installing automatically... please wait.")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            print("[+] All libraries installed successfully!")
        except Exception as e:
            print(f"[-] Automatic installation failed: {e}")
            print("[-] Please try installing manually using: pip install " + " ".join(missing))
            sys.exit(1)

# Run installation before importing flask
install_dependencies()

from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__)

# Setup permanent directories
OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# ---------------------------------------------------------
# Programming Logic (Helper Functions)
# ---------------------------------------------------------

def cleanup_old_files():
    """Delete old files in outputs folder and temporary files."""
    now = time.time()
    # Clean outputs older than 1 hour
    if os.path.exists(OUTPUTS_DIR):
        for f in os.listdir(OUTPUTS_DIR):
            f_path = os.path.join(OUTPUTS_DIR, f)
            if os.path.isfile(f_path) and os.stat(f_path).st_mtime < now - 3600:
                try:
                    os.remove(f_path)
                except: pass

def calculate_hashes(filepath):
    """Calculate SHA256 and MD5 for file integrity."""
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
                md5.update(chunk)
        return {"SHA256": sha256.hexdigest().upper(), "MD5": md5.hexdigest().upper()}
    except Exception as e:
        return {"error": str(e)}

def bspatch_pure(old_data, patch_data):
    """Apply BSDIFF patch using pure Python logic."""
    if len(patch_data) < 32:
        raise ValueError("Patch file too short")
    
    header = patch_data[:32]
    if header[:8] != b'BSDIFF40':
        raise ValueError("Invalid patch header")
    
    ctrl_len = struct.unpack('<Q', header[8:16])[0]
    diff_len = struct.unpack('<Q', header[16:24])[0]
    new_size = struct.unpack('<Q', header[24:32])[0]
    
    ctrl_block = bz2.decompress(patch_data[32 : 32 + ctrl_len])
    diff_block = bz2.decompress(patch_data[32 + ctrl_len : 32 + ctrl_len + diff_len])
    extra_block = bz2.decompress(patch_data[32 + ctrl_len + diff_len :])
    
    new_data = bytearray(new_size)
    old_pos, new_pos, diff_pos, extra_pos = 0, 0, 0, 0
    
    for i in range(0, len(ctrl_block), 24):
        add_len = struct.unpack('<Q', ctrl_block[i : i+8])[0]
        copy_len = struct.unpack('<Q', ctrl_block[i+8 : i+16])[0]
        seek_len = struct.unpack('<q', ctrl_block[i+16 : i+24])[0]
        
        if new_pos + add_len > new_size: raise ValueError("Corrupt patch (add)")
        for j in range(add_len):
            val = diff_block[diff_pos + j]
            if 0 <= old_pos + j < len(old_data):
                val = (val + old_data[old_pos + j]) % 256
            new_data[new_pos + j] = val
        
        new_pos += add_len
        old_pos += add_len
        diff_pos += add_len
        
        if new_pos + copy_len > new_size: raise ValueError("Corrupt patch (copy)")
        new_data[new_pos : new_pos + copy_len] = extra_block[extra_pos : extra_pos + copy_len]
        new_pos += copy_len
        extra_pos += copy_len
        old_pos += seek_len
        
    return bytes(new_data)

# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    mode = request.form.get('mode')
    logs = []
    
    # Pre-cleanup of old files
    cleanup_old_files()
    
    temp_dir = tempfile.mkdtemp()
    try:
        if mode == 'patch':
            patch_file = request.files['patch_file']
            original_file = request.files['original_file']
            
            p_path = os.path.join(temp_dir, "patch.xz")
            o_path = os.path.join(temp_dir, "original")
            patch_file.save(p_path)
            original_file.save(o_path)
            
            logs.append("File upload successful. Analyzing...")
            h_orig = calculate_hashes(o_path)
            logs.append(f"Original MD5: {h_orig.get('MD5', 'Error')}")
            
            logs.append("Decompressing patch (LZMA)...")
            ext_patch_path = os.path.join(temp_dir, "extracted.patch")
            with lzma.open(p_path, 'rb') as f_in, open(ext_patch_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            
            logs.append("Applying BSDIFF algorithm...")
            with open(o_path, 'rb') as f_o, open(ext_patch_path, 'rb') as f_p:
                patched_data = bspatch_pure(f_o.read(), f_p.read())
            
            result_name = f"patched_{original_file.filename}"
            result_path = os.path.join(temp_dir, result_name)
            with open(result_path, 'wb') as f_out:
                f_out.write(patched_data)
                
            metadata = {
                "original": original_file.filename,
                "status": "success",
                "hash": h_orig,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            meta_path = os.path.join(temp_dir, "metadata.json")
            with open(meta_path, 'w', encoding='utf-8') as f_j:
                json.dump(metadata, f_j, ensure_ascii=False, indent=4)
            
            zip_name = f"result_{int(time.time())}.zip"
            zip_path = os.path.join(temp_dir, zip_name)
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.write(result_path, arcname=result_name)
                zf.write(meta_path, arcname="metadata.json")
            
            shutil.move(zip_path, os.path.join(OUTPUTS_DIR, zip_name))
            return jsonify({"success": True, "logs": logs, "download_url": f"/download/{zip_name}"})

        elif mode == 'extract':
            archive_file = request.files['archive_file']
            a_path = os.path.join(temp_dir, "archive.xz")
            archive_file.save(a_path)
            
            logs.append("Decompressing...")
            result_name = archive_file.filename.replace('.xz', '') or "extracted_file"
            result_path = os.path.join(temp_dir, result_name)
            with lzma.open(a_path, 'rb') as f_in, open(result_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            
            h_ext = calculate_hashes(result_path)
            logs.append(f"Result MD5: {h_ext.get('MD5', 'Error')}")
            
            zip_name = f"extract_{int(time.time())}.zip"
            zip_path = os.path.join(temp_dir, zip_name)
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.write(result_path, arcname=result_name)
            
            shutil.move(zip_path, os.path.join(OUTPUTS_DIR, zip_name))
            return jsonify({"success": True, "logs": logs, "download_url": f"/download/{zip_name}"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(OUTPUTS_DIR, filename)

# ---------------------------------------------------------
# التشغيل والتحكم
# ---------------------------------------------------------

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == '__main__':
    print(f"[*] Cloud Patcher Starting...")
    print(f"[*] Local Outputs: {OUTPUTS_DIR}")
    
    # Clean old outputs on startup
    cleanup_old_files()
    
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        threading.Thread(target=open_browser, daemon=True).start()
    
    app.run(host='0.0.0.0', port=5000, debug=False)
