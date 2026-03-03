import os
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from plyer import filechooser

# مكتبات المعالجة (ستعمل لأننا سنضمنها في buildozer.spec)
import bsdiff4
import lzma
import tempfile
import shutil
from kivy.utils import platform

# تعيين لون خلفية التطبيق إلى لون داكن حديث
Window.clearcolor = (0.12, 0.12, 0.14, 1)

# فئة زر مخصصة مع زوايا دائرية ותأثيرات
class ModernButton(Button):
    def __init__(self, bg_color=(0.2, 0.6, 0.8, 1), **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0) # شفاف لإظهار الـ Canvas
        self.bg_color = bg_color
        self.markup = True
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color if not self.disabled else (0.3, 0.3, 0.3, 1))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[15])

class PatchApp(App):
    def build(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.INTERNET
            ])

        # الحاوية الرئيسية مع فراغات مريحة للعين
        self.layout = BoxLayout(orientation='vertical', padding=[30, 50, 30, 50], spacing=25)
        
        # العنوان مع خط عريض ولون ممیز
        self.title_label = Label(text="[color=00BFFF][b]🚀 Cloud Patcher[/b][/color]\n[size=14sp][color=AAAAAA]أداة التحديث السحابية الذكية[/color][/size]", 
                                 markup=True, halign="center", font_size=28, size_hint=(1, 0.15))
        self.layout.add_widget(self.title_label)
        
        # حاوية ملف الأصل
        box_original = BoxLayout(orientation='vertical', spacing=5, size_hint=(1, 0.2))
        self.btn_original = ModernButton(text="[b]📂 1. اختر الملف المتوفر لديك[/b]", bg_color=(0.15, 0.5, 0.85, 1))
        self.btn_original.bind(on_press=self.choose_original)
        self.lbl_original = Label(text="لم يتم اختيار ملف", color=(0.6, 0.6, 0.6, 1), size_hint=(1, 0.4), font_size=14)
        box_original.add_widget(self.btn_original)
        box_original.add_widget(self.lbl_original)
        self.layout.add_widget(box_original)

        # حاوية ملف الباتش
        box_patch = BoxLayout(orientation='vertical', spacing=5, size_hint=(1, 0.2))
        self.btn_patch = ModernButton(text="[b]📦 2. اختر ملف التحديث (.xz)[/b]", bg_color=(0.85, 0.4, 0.15, 1))
        self.btn_patch.bind(on_press=self.choose_patch)
        self.lbl_patch = Label(text="لم يتم اختيار ملف", color=(0.6, 0.6, 0.6, 1), size_hint=(1, 0.4), font_size=14)
        box_patch.add_widget(self.btn_patch)
        box_patch.add_widget(self.lbl_patch)
        self.layout.add_widget(box_patch)

        # فاصل مرئي بسيط
        self.layout.add_widget(Label(size_hint=(1, 0.05)))

        # شريط التقدم بتصميم أفضل (في Kivy يكون الافتراضي بسيطاً، نكتفي بالتحكم في حجمه)
        self.progress = ProgressBar(max=100, value=0, size_hint=(1, None), height=20)
        self.layout.add_widget(self.progress)
        
        self.lbl_status = Label(text="جاهز", color=(0.5, 0.8, 0.5, 1), size_hint=(1, 0.05), font_size=16)
        self.layout.add_widget(self.lbl_status)

        # زر البدء (كبير وواضح في الأسفل)
        self.btn_start = ModernButton(text="[size=20sp][b]⚡ بدء الدمج والتحديث[/b][/size]", bg_color=(0.15, 0.75, 0.35, 1), size_hint=(1, 0.2))
        self.btn_start.disabled = True
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
            self.btn_start.text = "[size=20sp][b]⚡ بدء الدمج والتحديث[/b][/size]"
            self.btn_start.update_canvas() # لتحديث لون الزر بعد التفعيل

    def start_patching_thread(self, instance):
        self.btn_start.disabled = True
        self.btn_start.update_canvas()
        self.progress.value = 10
        self.lbl_status.text = "جاري تحضير الملفات..."
        threading.Thread(target=self.run_patch_process).start()

    def run_patch_process(self):
        try:
            # مسار الإخراج 
            output_dir = "/storage/emulated/0/Download"
            if not os.path.exists(output_dir) or not os.access(output_dir, os.W_OK):
                output_dir = App.get_running_app().user_data_dir
                
            output_file = os.path.join(output_dir, "patched_file_final.bin")
            
            Clock.schedule_once(lambda dt: self.update_status("جاري فك ضغط الباتش... (LZMA)"))
            
            # استخراج الباتش في ملف مؤقت 
            fd, temp_patch_path = tempfile.mkstemp()
            try:
                # 1. قراءة الملف المضغوط وفكه في مسار مؤقت
                with lzma.open(self.patch_path, "rb") as f_in, os.fdopen(fd, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
                
                Clock.schedule_once(lambda dt: self.update_progress(50))
                Clock.schedule_once(lambda dt: self.update_status("جاري تطبيق bsdiff..."))

                # 2. تطبيق الباتش
                bsdiff4.file_patch(self.original_path, output_file, temp_patch_path)
                
                Clock.schedule_once(lambda dt: self.update_progress(100))
                Clock.schedule_once(lambda dt: self.show_success(output_file))
            finally:
                # تنظيف الملف المؤقت
                if os.path.exists(temp_patch_path):
                    os.remove(temp_patch_path)

        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_error(str(e)))

    def update_status(self, text):
        self.lbl_status.text = text

    def update_progress(self, val):
        self.progress.value = val

    def show_success(self, path):
        self.btn_start.disabled = False
        self.btn_start.text = "[size=20sp][b]✅ اكتمل بنجاح![/b][/size]"
        self.btn_start.update_canvas()
        self.lbl_status.text = "تم الانتهاء."
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text="تم دمج التحديث بنجاح.\nتم حفظ الملف في:", halign="center"))
        path_label = Label(text=path, color=(0.4, 0.8, 1, 1), font_size=12, text_size=(300, None), halign="center", valign="middle")
        content.add_widget(path_label)
        btn_close = ModernButton(text="إغلاق", bg_color=(0.3, 0.3, 0.3, 1), size_hint=(1, 0.4))
        content.add_widget(btn_close)
        
        popup = Popup(title='🎉 نجاح', content=content, size_hint=(0.85, 0.45), auto_dismiss=False)
        btn_close.bind(on_release=popup.dismiss)
        popup.open()

    def show_error(self, error):
        self.btn_start.disabled = False
        self.btn_start.update_canvas()
        self.lbl_status.text = "حدث خطأ!"
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text="حدث خطأ أثناء العملية:", text_size=(300, None), halign="center"))
        err_label = Label(text=str(error), color=(1, 0.4, 0.4, 1), font_size=12, text_size=(300, None), halign="center")
        content.add_widget(err_label)
        btn_close = ModernButton(text="إغلاق", bg_color=(0.8, 0.2, 0.2, 1), size_hint=(1, 0.4))
        content.add_widget(btn_close)
        
        popup = Popup(title='❌ خطأ', content=content, size_hint=(0.85, 0.45), auto_dismiss=False)
        btn_close.bind(on_release=popup.dismiss)
        popup.open()

if __name__ == '__main__':
    PatchApp().run()
