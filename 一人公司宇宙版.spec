# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('data', 'data'), ('config', 'config'), ('iqra', 'iqra'), ('knowledge_base', 'knowledge_base'), ('rules_project', 'rules_project'), ('solar_explorer', 'solar_explorer'), ('tools', 'tools')],
    hiddenimports=['PyQt5', 'PyQt5.QtWebEngineWidgets', 'PyQt5.QtWebChannel', 'PyQt5.QtMultimedia', 'PyQt5.QtMultimediaWidgets', 'qrcode', 'PIL', 'cryptography', 'supabase', 'bcrypt', 'requests', 'matplotlib', 'matplotlib.backends.backend_qt5agg', 'jinja2', 'plyer'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='一人公司宇宙版',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='一人公司宇宙版',
)
app = BUNDLE(
    coll,
    name='一人公司宇宙版.app',
    icon='assets/icon.icns',
    bundle_identifier=None,
)
