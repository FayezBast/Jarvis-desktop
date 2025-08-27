# PyInstaller hook to exclude problematic FLAC binaries
from PyInstaller.utils.hooks import collect_data_files
import os

# Get all data files for speech_recognition
datas = collect_data_files('speech_recognition')

# Filter out FLAC binaries that cause architecture issues
filtered_datas = []
for src, dst in datas:
    if 'flac-' not in os.path.basename(src):
        filtered_datas.append((src, dst))

datas = filtered_datas
