# J.A.R.V.I.S - Desktop AI Assistant

A modern desktop AI assistant built with PyQt6, featuring voice recognition, ElevenLabs text-to-speech, and a sleek chat interface.

## Features

- 🎙️ **Voice Recognition**: Wake word detection with "Jarvis"
- 🔊 **ElevenLabs TTS**: High-quality voice synthesis
- 💬 **Chat Interface**: Modern PyQt6 GUI with conversation history
- ⏭️ **Skip Speech**: Button to skip long responses
- 🎤 **Microphone Testing**: Built-in microphone diagnostics
- 🍎 **macOS App Bundle**: Native desktop application

## Installation

1. Clone the repository:
```bash
git clone https://github.com/FayezBast/desktop-jarvis.git
cd desktop-jarvis
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your API keys:
```
ELEVEN_API_KEY=your_elevenlabs_api_key_here
# Add other API keys as needed
```

## Usage

### Running from Source
```bash
python jarvis_gui.py
```

### Building Desktop App
```bash
pyinstaller jarvis.spec
```

The built app will be available in `dist/Jarvis.app` (macOS) or `dist/Jarvis/` (Windows/Linux).

## Project Structure

- `jarvis_gui.py` - Main GUI application
- `main.py` - Core AI agent logic
- `tools/` - Tool modules for various functionalities
- `jarvis.spec` - PyInstaller configuration
- `requirements.txt` - Python dependencies

## Voice Setup

1. Get an ElevenLabs API key from [ElevenLabs](https://elevenlabs.io)
2. Add your voice ID to the configuration (currently set to 'JBFqnCBsd6RMkjVDRZzb')
3. Ensure microphone permissions are granted on macOS

## Requirements

- Python 3.8+
- PyQt6
- speech_recognition
- elevenlabs
- pygame
- pyaudio (for microphone access)

## License

This project is for personal use. Please ensure you comply with API providers' terms of service.
