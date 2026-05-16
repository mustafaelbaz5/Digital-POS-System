# -*- mode: python ; coding: utf-8 -*-
# pos_system.spec
# شغّل بـ: pyinstaller pos_system.spec

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# ── جمع كل submodules تلقائياً ──────────────────────────────────
hidden = []
hidden += collect_submodules('database')
hidden += collect_submodules('ui')
hidden += collect_submodules('ui.components')
hidden += collect_submodules('ui.screens')
hidden += collect_submodules('ui.styles')
hidden += collect_submodules('ui.utils')
hidden += collect_submodules('PyQt6')

# ── الملفات الإضافية (غير .py) ──────────────────────────────────
datas = []
# لو عندك أيقونة أو ملفات static أضفها هنا
# datas += [('assets/icon.ico', 'assets')]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # مكتبات مش محتاجها — تقلل الحجم
        'tkinter', 'matplotlib', 'numpy', 'pandas',
        'scipy', 'PIL', 'cv2', 'test', 'unittest',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='نظام_المدفوعات',           # اسم الـ EXE
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                         # يضغط الحجم (لازم UPX مثبت)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                    # بدون نافذة CMD
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',         # فك التعليق لو عندك أيقونة
)
