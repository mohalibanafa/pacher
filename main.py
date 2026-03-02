import os
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.clock import Clock
from plyer import filechooser

# مكتبات المعالجة (ستعمل لأننا سنضمنها في buildozer.spec)
import bsdiff4
import lzma

class PatchApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # العنوان
        self.title_label = Label(text="[b]🚀 Cloud Patcher (Local)[/b]", markup=True, font_size=24, size_hint=(1, 0.1))
        self.layout.add_widget(self.title_label)
        
        # زر اختيار الملف الأصلي
        self.btn_original = Button(text="📂 1. اختر الملف الأصلي", size_hint=(1, 0.15), background_color=(0.2, 0.6, 0.8, 1))
        self.btn_original.bind(on_press=self.choose_original)
        self.layout.add_widget(self.btn_original)
        
        self.lbl_original = Label(text="لم يتم اختيار ملف", color=(0.7, 0.7, 0.7, 1), size_hint=(1, 0.05))
        self.layout.add_widget(self.lbl_original)

        # زر اختيار ملف الباتش
        self.btn_patch = Button(text="📂 2. اختر ملف الباتش (.xz)", size_hint=(1, 0.15), background_color=(0.8, 0.4, 0.2, 1))
        self.btn_patch.bind(on_press=self.choose_patch)
        self.layout.add_widget(self.btn_patch)
        
        self.lbl_patch = Label(text="لم يتم اختيار ملف", color=(0.7, 0.7, 0.7, 1), size_hint=(1, 0.05))
        self.layout.add_widget(self.lbl_patch)

        # شريط التقدم
        self.progress = ProgressBar(max=100, value=0, size_hint=(1, 0.05))
        self.layout.add_widget(self.progress)
        
        # زر البدء
        self.btn_start = Button(text="⚡ بدء الدمج (Apply Patch)", size_hint=(1, 0.2), background_color=(0.2, 0.8, 0.2, 1), disabled=True)
        self.btn_start.bind(on_press=self.start_patching_thread)
        self.layout.add_widget(self.btn_start)
        
        # متغيرات المسارات
        self.original_path = None
        self.patch_path = None

        return self.layout

    def choose_original(self, instance):
        filechooser.open_file(on_selection=self.handle_original_selection)

    def handle_original_selection(self, selection):
        if selection:
            self.original_path = selection[0]
            self.lbl_original.text = os.path.basename(self.original_path)
            self.check_ready()

    def choose_patch(self, instance):
        filechooser.open_file(on_selection=self.handle_patch_selection, filters=["*.xz"])

    def handle_patch_selection(self, selection):
        if selection:
            self.patch_path = selection[0]
            self.lbl_patch.text = os.path.basename(self.patch_path)
            self.check_ready()

    def check_ready(self):
        if self.original_path and self.patch_path:
            self.btn_start.disabled = False
            self.btn_start.text = "⚡ بدء الدمج (Apply Patch)"

    def start_patching_thread(self, instance):
        self.btn_start.disabled = True
        self.progress.value = 10
        threading.Thread(target=self.run_patch_process).start()

    def run_patch_process(self):
        try:
            # مسار الإخراج (في مجلد التنزيلات)
            output_dir = "/storage/emulated/0/Download"
            if not os.path.exists(output_dir):
                output_dir = os.path.dirname(self.original_path) # Fallback
            
            output_file = os.path.join(output_dir, "patched_file_final.bin")
            
            Clock.schedule_once(lambda dt: self.update_status("جاري فك ضغط الباتش... (LZMA)"))
            
            # 1. قراءة الملف المضغوط وفكه في الذاكرة
            with lzma.open(self.patch_path, "rb") as f:
                patch_data = f.read()
            
            Clock.schedule_once(lambda dt: self.update_progress(50))
            Clock.schedule_once(lambda dt: self.update_status("جاري تطبيق bsdiff..."))

            # 2. تطبيق الباتش
            bsdiff4.file_patch(self.original_path, output_file, patch_data)
            
            Clock.schedule_once(lambda dt: self.update_progress(100))
            Clock.schedule_once(lambda dt: self.show_success(output_file))

        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_error(str(e)))

    def update_status(self, text):
        self.lbl_patch.text = text

    def update_progress(self, val):
        self.progress.value = val

    def show_success(self, path):
        self.btn_start.disabled = False
        self.btn_start.text = "✅ تم بنجاح!"
        popup = Popup(title='نجاح', content=Label(text=f'تم حفظ الملف في:\n{path}'), size_hint=(0.8, 0.4))
        popup.open()

    def show_error(self, error):
        self.btn_start.disabled = False
        popup = Popup(title='خطأ', content=Label(text=f'حدث خطأ:\n{error}'), size_hint=(0.8, 0.4))
        popup.open()

if __name__ == '__main__':
    PatchApp().run()
