import os
import sys
import shutil
import subprocess
import hashlib
import zlib

# ==========================================
# 1. نظام التثبيت الذكي
# ==========================================
def setup_environment():
    print("🔍 جاري فحص النظام...")
    needs_apt = not (shutil.which("bsdiff") and shutil.which("aria2c") and shutil.which("xz"))
    if needs_apt:
        print("⚙️ جاري تثبيت أدوات النظام (bsdiff, aria2, xz-utils)...")
        subprocess.run(["apt-get", "update", "-qq"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["apt-get", "install", "-y", "-qq", "bsdiff", "aria2", "xz-utils"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        import gradio
    except ImportError:
        print("⚙️ جاري تثبيت الواجهة الرسومية (Gradio)...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "gradio"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("✅ النظام جاهز بالكامل.")

setup_environment()
import gradio as gr

# ==========================================
# 2. دوال المعالجة الأساسية
# ==========================================
def download_file(url, output_name):
    # إذا كان الرابط فارغاً (يحدث عند استدعاء الـ API بوضع تحميل ملف واحد)، نتجاهل التحميل
    if not url or url.strip() == "":
        return
        
    command = ["aria2c", "-x", "16", "-s", "16", "--seed-time=0", "-d", "/content", "-o", output_name, url]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"فشل التحميل من الرابط: {url}\nالسبب: {result.stderr}")

def calculate_hashes(filepath):
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()
    sha384 = hashlib.sha384()
    sha512 = hashlib.sha512()
    crc32_val = 0

    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b""):
            md5.update(chunk)
            sha1.update(chunk)
            sha256.update(chunk)
            sha384.update(chunk)
            sha512.update(chunk)
            crc32_val = zlib.crc32(chunk, crc32_val)

    return {
        "CRC32": "%08X" % (crc32_val & 0xFFFFFFFF),
        "MD5": md5.hexdigest().upper(),
        "SHA1": sha1.hexdigest().upper(),
        "SHA256": sha256.hexdigest().upper(),
        "SHA384": sha384.hexdigest().upper(),
        "SHA512": sha512.hexdigest().upper()
    }

def create_patch(original, modified, patch_name):
    command = ["bsdiff", original, modified, patch_name]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"فشل إنشاء الباتش!\nالسبب: {result.stderr}")
    return patch_name

def compress_file_lzma(file_name):
    command = ["xz", "-z", "-9", "-e", "-T0", file_name]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"فشل الضغط بـ LZMA!\nالسبب: {result.stderr}")
    return f"{file_name}.xz"

# ==========================================
# 3. الدالة الرئيسية (هذه ما سيكلمها الأندرويد عبر الـ API)
# ==========================================
def process(operation_mode, original_url, modified_url):
    if not original_url or not original_url.strip():
        raise gr.Error("الرجاء إدخال الرابط الأول على الأقل!")

    orig_file = "downloaded_file.bin"
    mod_file = "modified_file.bin"
    patch_file = "output.patch"
    
    for f in [orig_file, mod_file, patch_file, f"{orig_file}.xz", f"{patch_file}.xz"]:
        if os.path.exists(f):
            os.remove(f)

    try:
        if operation_mode == "تحميل ملف وضغطه مباشرة":
            gr.Info("📥 بدء تحميل الملف...")
            download_file(original_url, orig_file)
            
            gr.Info("🔍 جاري استخراج الهاش للملف...")
            hashes = calculate_hashes(orig_file)
            msg = f"MD5: {hashes['MD5']}\nSHA256: {hashes['SHA256']}\nCRC32: {hashes['CRC32']}"
            
            gr.Info("🗜️ جاري ضغط الملف بأقصى إعدادات (LZMA)...")
            final_file = compress_file_lzma(orig_file)
            return final_file, msg

        else: # وضع الباتش
            if not modified_url or not modified_url.strip():
                raise gr.Error("في وضع إنشاء الباتش، يجب إدخال رابط الملف المعدل!")
                
            gr.Info("📥 بدء تحميل الملف الأصلي...")
            download_file(original_url, orig_file)
            
            gr.Info("🔍 جاري حساب الهاش للملف الأصلي...")
            hashes = calculate_hashes(orig_file)
            msg = f"MD5: {hashes['MD5']}\nSHA256: {hashes['SHA256']}\nCRC32: {hashes['CRC32']}"
            
            gr.Info("📥 بدء تحميل الملف المعدل...")
            download_file(modified_url, mod_file)
            
            gr.Info("⚙️ جاري إنشاء الباتش (قد يستغرق وقتاً)...")
            create_patch(orig_file, mod_file, patch_file)
            
            gr.Info("🗜️ جاري ضغط الباتش بأقصى إعدادات (LZMA)...")
            final_file = compress_file_lzma(patch_file)
            
            os.remove(orig_file)
            os.remove(mod_file)
            
            return final_file, msg

    except Exception as e:
        raise gr.Error(str(e))

# ==========================================
# 4. بناء الواجهة (وتعريف الـ API)
# ==========================================
with gr.Blocks(theme=gr.themes.Soft()) as interface:
    gr.Markdown("# 🚀 أداة المعالجة السحابية الشاملة (LZMA + Bsdiff + Aria2)")
    
    mode_selector = gr.Radio(
        choices=["إنشاء باتش بين ملفين وضغطه", "تحميل ملف وضغطه مباشرة"],
        value="إنشاء باتش بين ملفين وضغطه",
        label="🛠️ اختر نوع العملية"
    )
    
    with gr.Row():
        with gr.Column():
            orig_input = gr.Textbox(label="🔗 رابط الملف الأصلي", placeholder="https://... أو magnet:?xt=...")
            mod_input = gr.Textbox(label="🔗 رابط الملف المعدل", placeholder="https://... أو magnet:?xt=...")
            run_btn = gr.Button("⚡ بدء العملية", variant="primary")
            
        with gr.Column():
            output_file = gr.File(label="📥 تحميل الملف النهائي (.xz)")
            output_hashes = gr.Textbox(label="بيانات الملف (Hash)", lines=4)

    def update_ui(mode):
        if mode == "تحميل ملف وضغطه مباشرة":
            return gr.update(label="🔗 رابط الملف المراد تحميله وضغطه"), gr.update(visible=False, value="")
        else:
            return gr.update(label="🔗 رابط الملف الأصلي"), gr.update(visible=True)

    mode_selector.change(fn=update_ui, inputs=mode_selector, outputs=[orig_input, mod_input])

    # 🟢 السر هنا: إضافة api_name="process_task" ليتمكن الأندرويد من التخاطب معه
    run_btn.click(
        fn=process,
        inputs=[mode_selector, orig_input, mod_input],
        outputs=[output_file, output_hashes],
        api_name="process_task" 
    )

interface.launch(debug=True, share=True)