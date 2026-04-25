[app]
title = Durak
package.name = durak
package.domain = org.dilshod.durak
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,mp3,ttf,otf,json,db
version = 1.0.0

requirements = python3,kivy==2.3.0,pillow,plyer,kivymd==1.2.0

orientation = portrait
fullscreen = 1
android.archs = arm64-v8a
android.allow_backup = True

# Permissions
android.permissions = VIBRATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# Presplash and Icon
android.presplash.filename = assets/images/logo.png
android.icon.filename = assets/images/logo.png

# (int) Target Android API, should be as high as possible.
android.targetapi = 33
# (int) Minimum API your APK will support.
android.minapi = 26

# (str) Android NDK version to use
# android.ndk = 25b

# (bool) If True, then skip trying to update the Android sdk
# This can be useful to avoid any automated update or any issues with
# the update.
android.skip_update = False

# (bool) If True, then automatically accept SDK license
# agreements. This is intended for automation only.
android.accept_sdk_license = True

# (str) Android entry point, default is to use main.py
android.entrypoint = main.py

# (list) List of service to declare
#services = NAME:ENTRYPOINT_TO_PY,NAME2:ENTRYPOINT2_TO_PY

# (str) The Android arch to build for — android.archs yuqorida belgilangan (13-qator)

[buildozer]
log_level = 2
warn_on_root = 1
