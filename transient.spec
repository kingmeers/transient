# -*- mode: python ; coding: utf-8 -*-

import os
import whisper

# Get the dynamic path for the Whisper assets directory
whisper_assets_dir = os.path.join(os.path.dirname(whisper.__file__), 'assets')

a = Analysis(
    ['transient.py'],
    pathex=[],
    binaries=[],
    datas=[(whisper_assets_dir, 'whisper/assets')],  # Include the Whisper assets dynamically
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='transient',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Ensure it's windowed and not a console app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='transient.app',  # Specify the .app extension for macOS
    icon='t.icns',  # Add your icon file here
    bundle_identifier='com.transient.app',  # Customize this if needed
    info_plist={
        'NSHighResolutionCapable': 'True',  # Support high-resolution screens
    }
)
