[app]

# (str) Title of your application
title = Cloud Patcher

# (str) Package name
package.name = cloudpatcher
version = 1.0
# (str) Package domain (needed for android/ios packaging)
package.domain = org.test

# (str) Source code where the main.py live
source.dir = .

# (str) Source filename (default: main.py)
source.include_exts = py,png,jpg,kv,atlas

# (list) Application requirements
# هنا السحر: نضيف bsdiff4 (للتعامل مع الباتش) و plyer (للملفات)
requirements = python3,kivy==2.3.0,plyer,bsdiff4,https://github.com/kivy/python-for-android/archive/master.zip

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (list) Permissions
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) List of Java classes to add to the compilation
# (هنا نضيف مكتبة FileChooser الأصلية للأندرويد)
android.add_jars = foo.jar

# (bool) Skip byte compile for .py files
android.skip_byte_compile = 0

# (str) Bootstrap to use for android builds
p4a.bootstrap = sdl2

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
