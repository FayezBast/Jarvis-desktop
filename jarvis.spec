# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['jarvis_gui.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('.env', '.'),
        ('tools/', 'tools/'),
        ('main.py', '.'),
        ('jarvis_icon.png', '.'),
        ('__init__.py', '.'),
    ],
    hiddenimports=[
        'speech_recognition',
        'pyttsx3',
        'elevenlabs',
        'pygame',
        'PyQt6',
        'langchain',
        'langchain_ollama',
        'dotenv',
        'ollama',
        'main',
        'tools.jarvis_speech',
        'tools.app_discovery',
        'tools.arp_scan',
        'tools.debug_tool',
        'tools.email_tool',
        'tools.facetime_tool',
        'tools.matrix',
        'tools.notes',
        'tools.OCR',
        'tools.open_app',
        'tools.screenshot',
        'tools.web_search',
        'tools.youtube',
    ],
    hookspath=['.'],  # Use our custom hook to exclude FLAC binaries
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'speech_recognition.flac-mac',  # Exclude problematic x86_64 FLAC binary
        'speech_recognition.flac-linux-x86',
        'speech_recognition.flac-linux-x86_64', 
        'speech_recognition.flac-win32.exe',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],  # Changed for onedir mode
    exclude_binaries=True,  # Changed for onedir mode
    name='Jarvis',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX compression to avoid architecture issues
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for a windowed app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',  # Explicitly set architecture for Apple Silicon
    codesign_identity=None,
    entitlements_file=None,
    icon='jarvis_icon.ico',  # Use our custom icon
)

# Add COLLECT for onedir mode
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Jarvis'
)

# For macOS, create an app bundle
app = BUNDLE(
    coll,  # Changed from exe to coll for onedir mode
    name='Jarvis.app',
    icon='jarvis_icon.ico',
    bundle_identifier='com.yourname.jarvis',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'NSMicrophoneUsageDescription': 'Jarvis AI Assistant needs microphone access for voice commands and speech recognition.',
        'NSSpeechRecognitionUsageDescription': 'Jarvis AI Assistant uses speech recognition to understand voice commands.',
        'NSCameraUsageDescription': 'Jarvis AI Assistant may need camera access for advanced features.',
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Jarvis Assistant',
                'CFBundleTypeIconFile': 'jarvis_icon.ico',
                'LSItemContentTypes': ['public.plain-text'],
                'LSHandlerRank': 'Owner'
            }
        ]
    },
)
