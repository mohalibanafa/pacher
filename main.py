import flet as ft
import os
import hashlib
import lzma
import bz2
import struct
# import bsdiff4  # تمت إزالته لضمان التوافق مع أندرويد
import tempfile
import threading
import io
import requests

def main(page: ft.Page):
    page.title = "🚀 Cloud Patcher - Flet Edition"
    page.theme_mode = ft.ThemeMode.DARK
    page.rtl = True
    page.window_width = 450
    page.window_height = 800
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.padding = 20

    # ---------------------------------------------------------
    # UI Elements & FilePickers
    # ---------------------------------------------------------
    title_text = ft.Text("Cloud Patcher 🚀", size=32, weight=ft.FontWeight.BOLD, color=ft.colors.CYAN_ACCENT)
    subtitle_text = ft.Text("تطبيق العميل: فك الضغط وتطبيق الباتشات", size=14, color=ft.colors.BLUE_GREY_200)

    mode_tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="تطبيق باتش", icon=ft.icons.COMPARE_ARROWS),
            ft.Tab(text="فك ضغط", icon=ft.icons.DISCOVER_TUNE),
        ],
    )

    # Variables to store selected file paths
    selected_files = {
        "patch": None,
        "original": None,
        "archive": None,
    }

    # Text elements to show selected file names
    lbl_patch = ft.Text("لم يتم اختيار ملف الباتش (.xz)", italic=True, size=12)
    lbl_original = ft.Text("لم يتم اختيار اللعبة/الملف الأصلي", italic=True, size=12)
    lbl_archive = ft.Text("لم يتم اختيار الملف المضغوط (.xz)", italic=True, size=12)

    def on_patch_selected(e: ft.FilePickerResultEvent):
        if e.files:
            selected_files["patch"] = e.files[0].path
            lbl_patch.value = f"✅ {e.files[0].name}"
            lbl_patch.color = ft.colors.GREEN_400
        page.update()

    def on_original_selected(e: ft.FilePickerResultEvent):
        if e.files:
            selected_files["original"] = e.files[0].path
            lbl_original.value = f"✅ {e.files[0].name}"
            lbl_original.color = ft.colors.GREEN_400
        page.update()

    def on_archive_selected(e: ft.FilePickerResultEvent):
        if e.files:
            selected_files["archive"] = e.files[0].path
            lbl_archive.value = f"✅ {e.files[0].name}"
            lbl_archive.color = ft.colors.GREEN_400
        page.update()

    fp_patch = ft.FilePicker(on_result=on_patch_selected)
    fp_original = ft.FilePicker(on_result=on_original_selected)
    fp_archive = ft.FilePicker(on_result=on_archive_selected)
    
    page.overlay.extend([fp_patch, fp_original, fp_archive])

    btn_pick_patch = ft.ElevatedButton(
        "اختر ملف الباتش (.xz)",
        icon=ft.icons.FILE_UPLOAD,
        on_click=lambda _: fp_patch.pick_files(allow_multiple=False)
    )
    
    btn_pick_original = ft.ElevatedButton(
        "اختر الملف الأصلي",
        icon=ft.icons.FOLDER_OPEN,
        on_click=lambda _: fp_original.pick_files(allow_multiple=False)
    )

    btn_pick_archive = ft.ElevatedButton(
        "اختر الملف المضغوط (.xz)",
        icon=ft.icons.UNARCHIVE,
        on_click=lambda _: fp_archive.pick_files(allow_multiple=False)
    )

    patch_mode_controls = ft.Column([
        ft.Row([btn_pick_patch, lbl_patch]),
        ft.Row([btn_pick_original, lbl_original])
    ], visible=True)

    extract_mode_controls = ft.Column([
        ft.Row([btn_pick_archive, lbl_archive])
    ], visible=False)

    controls_container = ft.Container(content=patch_mode_controls, margin=ft.margin.symmetric(vertical=10))

    log_area = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    progress_bar = ft.ProgressBar(width=400, color="cyan", visible=False)
    status_text = ft.Text("جاهز...", color=ft.colors.GREEN_400)

    # ---------------------------------------------------------
    # Helper Functions
    # ---------------------------------------------------------
    def log(message, color=ft.colors.WHITE):
        log_area.controls.append(ft.Text(message, color=color, size=12))
        page.update()

    def calculate_hashes(filepath):
        sha256 = hashlib.sha256()
        md5 = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
                md5.update(chunk)
        return {"SHA256": sha256.hexdigest().upper(), "MD5": md5.hexdigest().upper()}

    def extract_lzma(xz_path, output_path):
        with lzma.open(xz_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                f_out.write(f_in.read())

    # ---------------------------------------------------------
    # Core Processing Logic
    # ---------------------------------------------------------
    def bspatch_pure(old_data, patch_data):
        """Pure Python implementation of bspatch to avoid bsdiff4 C-extension issues on Android."""
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

    def run_process(e):
        if mode_tabs.selected_index == 0:  # Patch Mode
            if not selected_files["patch"] or not selected_files["original"]:
                status_text.value = "❌ يرجى اختيار ملف الباتش والملف الأصلي!"
                page.update()
                return
        else:  # Extract Mode
            if not selected_files["archive"]:
                status_text.value = "❌ يرجى اختيار الملف المضغوط!"
                page.update()
                return

        run_btn.disabled = True
        progress_bar.visible = True
        log_area.controls.clear()
        status_text.value = "جاري العمل... ⚙️"
        page.update()

        def work():
            temp_dir = tempfile.mkdtemp()
            try:
                if mode_tabs.selected_index == 0: # Patch Mode
                    patch_xz = selected_files["patch"]
                    original_file = selected_files["original"]
                    
                    log(f"✅ استخراج الهاش للملف الأصلي:")
                    hashes = calculate_hashes(original_file)
                    log(f"MD5: {hashes['MD5']}")
                    log(f"SHA256: {hashes['SHA256']}")
                    
                    uncompressed_patch = os.path.join(temp_dir, "extracted.patch")
                    
                    log("🗜️ جاري فك ضغط الباتش (LZMA)...")
                    extract_lzma(patch_xz, uncompressed_patch)
                    
                    # ننشئ الملف الناتج في نفس مجلد الملف الأصلي لسهولة الوصول (باسم جديد)
                    output_dir = os.path.dirname(original_file)
                    original_name = os.path.basename(original_file)
                    final_output = os.path.join(output_dir, f"patched_{original_name}")
                    
                    log("⚙️ جاري تطبيق الباتش...")
                    # استبدال bsdiff4.file_patch بالنسخة النقية
                    with open(original_file, 'rb') as f_orig:
                        old_data = f_orig.read()
                    with open(uncompressed_patch, 'rb') as f_patch:
                        patch_data = f_patch.read()
                    
                    patched_data = bspatch_pure(old_data, patch_data)
                    
                    with open(final_output, 'wb') as f_out:
                        f_out.write(patched_data)
                    
                    log(f"🎉 تم الانتهاء بنجاح! تم حفظ الملف في:", ft.colors.GREEN_ACCENT)
                    log(f"{final_output}", ft.colors.YELLOW)
                    
                else: # Compress Mode -> Extract Mode
                    archive_xz = selected_files["archive"]
                    output_dir = os.path.dirname(archive_xz)
                    archive_name = os.path.basename(archive_xz)
                    
                    # إزالة امتداد .xz إذا كان موجودا أو إضافة _extracted
                    if archive_name.endswith('.xz'):
                        final_output = os.path.join(output_dir, archive_name[:-3])
                    else:
                        final_output = os.path.join(output_dir, f"extracted_{archive_name}")
                        
                    log("🗜️ جاري فك ضغط الملف (LZMA)...")
                    extract_lzma(archive_xz, final_output)
                    
                    log(f"✅ استخراج الهاش للملف الناتج:")
                    hashes = calculate_hashes(final_output)
                    log(f"MD5: {hashes['MD5']}")
                    log(f"SHA256: {hashes['SHA256']}")
                    
                    log(f"🎉 تم الانتهاء بنجاح! تم الحفظ في:", ft.colors.GREEN_ACCENT)
                    log(f"{final_output}", ft.colors.YELLOW)
                    
                status_text.value = "تمت العملية بنجاح! ✅"
                
            except Exception as ex:
                log(f"❌ خطأ: {str(ex)}", ft.colors.RED_ACCENT)
                status_text.value = "فشلت العملية ❌"
            finally:
                run_btn.disabled = False
                progress_bar.visible = False
                page.update()

        threading.Thread(target=work).start()

    run_btn = ft.ElevatedButton(
        "⚡ بدء العملية",
        icon=ft.icons.PLAY_ARROW_ROUNDED,
        on_click=run_process,
        style=ft.ButtonStyle(
            color=ft.colors.BLACK,
            bgcolor=ft.colors.CYAN_ACCENT,
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
        width=400
    )

    # ---------------------------------------------------------
    # Assemble Page
    # ---------------------------------------------------------
    page.add(
        ft.Container(
            content=ft.Column([
                title_text,
                subtitle_text,
                ft.Divider(height=20, color=ft.colors.TRANSPARENT),
                mode_tabs,
                controls_container,
                ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                run_btn,
                ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                status_text,
                progress_bar,
                ft.Text("السجلات (Logs):", size=12, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=log_area,
                    bgcolor=ft.colors.BLACK12,
                    border_radius=10,
                    padding=10,
                    expand=True,
                    height=250
                )
            ]),
            padding=10,
            expand=True
        )
    )

    # Dynamic visibility for controls based on tab
    def on_tab_change(e):
        if mode_tabs.selected_index == 0:
            controls_container.content = patch_mode_controls
        else:
            controls_container.content = extract_mode_controls
        page.update()

    mode_tabs.on_change = on_tab_change

ft.app(target=main)
