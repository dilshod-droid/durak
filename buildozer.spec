[app]
title = Durak
package.name = durak
package.domain = org.durakgame
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,mp3,ttf,otf,json,db
version = 1.0.0

requirements = python3,kivy==2.3.0,pillow,plyer

orientation = portrait
fullscreen = 0

android.minapi = 26
android.targetapi = 33
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.permissions = VIBRATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

android.presplash.filename = assets/images/logo.png
android.icon.filename = assets/images/logo.png

[buildozer]
log_level = 2
warn_on_root = 1
