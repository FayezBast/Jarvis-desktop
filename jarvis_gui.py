import sys
import os
import threading
import time
import logging
from typing import Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QLineEdit, QPushButton, QLabel, QFrame, QScrollArea,
    QSystemTrayIcon, QMenu, QMessageBox, QProgressBar, QSplitter
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve,
    QRect, QSize, QPoint, QPointF, QUrl, QObject
)
from PyQt6.QtGui import (
    QFont, QIcon, QPixmap, QPainter, QBrush, QColor, QPen, QLinearGradient,
    QRadialGradient, QFontDatabase, QPalette, QAction
)

# Import your existing Jarvis components
from main import executor, recognizer, mic, TRIGGER_WORD
from tools.jarvis_speech import speak_text, get_speech_status
import speech_recognition as sr
import pyaudio


class VoiceVisualizerWidget(QWidget):
    """Animated voice visualization widget"""
    
    def __init__(self):
        super().__init__()
        self.setFixedSize(200, 200)
        self.listening = False
        self.speaking = False
        self.amplitude = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(50)  # 20 FPS
        
    def start_listening(self):
        self.listening = True
        self.speaking = False
        
    def start_speaking(self):
        self.listening = False
        self.speaking = True
        
    def stop_all(self):
        self.listening = False
        self.speaking = False
        self.amplitude = 0
        
    def update_animation(self):
        if self.listening:
            self.amplitude = (self.amplitude + 0.1) % (2 * 3.14159)
        elif self.speaking:
            self.amplitude = (self.amplitude + 0.2) % (2 * 3.14159)
        else:
            self.amplitude *= 0.95  # Fade out
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create gradient
        center = QPointF(100, 100)
        gradient = QRadialGradient(center, 80)
        
        if self.listening:
            # Blue gradient for listening
            gradient.setColorAt(0, QColor(64, 224, 255, 200))
            gradient.setColorAt(1, QColor(0, 100, 255, 50))
        elif self.speaking:
            # Green gradient for speaking
            gradient.setColorAt(0, QColor(64, 255, 144, 200))
            gradient.setColorAt(1, QColor(0, 200, 100, 50))
        else:
            # Gray gradient for idle
            gradient.setColorAt(0, QColor(100, 100, 100, 100))
            gradient.setColorAt(1, QColor(50, 50, 50, 30))
            
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Draw pulsing circle
        import math
        pulse = 20 + int(10 * math.sin(self.amplitude))
        painter.drawEllipse(center, 60 + pulse, 60 + pulse)
        
        # Draw inner circle
        inner_gradient = QRadialGradient(center, 30)
        if self.listening:
            inner_gradient.setColorAt(0, QColor(255, 255, 255, 255))
            inner_gradient.setColorAt(1, QColor(64, 224, 255, 200))
        elif self.speaking:
            inner_gradient.setColorAt(0, QColor(255, 255, 255, 255))
            inner_gradient.setColorAt(1, QColor(64, 255, 144, 200))
        else:
            inner_gradient.setColorAt(0, QColor(200, 200, 200, 150))
            inner_gradient.setColorAt(1, QColor(100, 100, 100, 100))
            
        painter.setBrush(QBrush(inner_gradient))
        painter.drawEllipse(center, 30, 30)


class ChatBubble(QFrame):
    """Modern chat bubble widget"""
    
    def __init__(self, text: str, is_user: bool = False):
        super().__init__()
        self.is_user = is_user
        self.setup_ui(text)
        
    def setup_ui(self, text: str):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Create label with text
        label = QLabel(text)
        label.setWordWrap(True)
        label.setFont(QFont("Helvetica", 12))
        
        if self.is_user:
            label.setStyleSheet("color: white;")
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #007AFF, stop:1 #0051D5);
                    border-radius: 15px;
                    margin-left: 50px;
                    margin-right: 5px;
                    margin-top: 5px;
                    margin-bottom: 5px;
                }
            """)
        else:
            label.setStyleSheet("color: #FFFFFF;")
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #2C2C2E, stop:1 #1C1C1E);
                    border-radius: 15px;
                    border: 1px solid #3A3A3C;
                    margin-left: 5px;
                    margin-right: 50px;
                    margin-top: 5px;
                    margin-bottom: 5px;
                }
            """)
            
        layout.addWidget(label)
        self.setLayout(layout)


class TextProcessingThread(QThread):
    """Thread for processing text messages"""
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, message):
        super().__init__()
        self.message = message
    
    def run(self):
        """Process text message with Jarvis"""
        try:
            print(f"DEBUG: Processing message in thread: {self.message}")
            response = executor.invoke({"input": self.message})
            content = response["output"]
            print(f"DEBUG: Got response content in thread: {content}")
            self.response_ready.emit(content)
            
        except Exception as e:
            print(f"DEBUG: Error in thread: {str(e)}")
            error_msg = f"Error: {str(e)}"
            self.error_occurred.emit(error_msg)


class JarvisWorker(QThread):
    """Worker thread for Jarvis voice processing"""
    
    user_message_ready = pyqtSignal(str)
    assistant_response_ready = pyqtSignal(str)
    listening_started = pyqtSignal()
    listening_stopped = pyqtSignal()
    speaking_started = pyqtSignal()
    speaking_stopped = pyqtSignal()
    error_occurred = pyqtSignal(str)
    status_update = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.conversation_mode = False
        
    def run(self):
        self.running = True
        last_interaction_time = None
        CONVERSATION_TIMEOUT = 30
        
        print("DEBUG: Voice worker started")
        
        # Check microphone access
        try:
            import pyaudio
            audio = pyaudio.PyAudio()
            # Try to access default microphone
            stream = audio.open(format=pyaudio.paInt16,
                              channels=1,
                              rate=44100,
                              input=True,
                              frames_per_buffer=1024)
            stream.close()
            audio.terminate()
            print("✅ Microphone access confirmed")
        except Exception as e:
            print(f"❌ Microphone access error: {e}")
            self.error_occurred.emit(f"Microphone access denied. Please grant microphone permissions to Jarvis in System Preferences > Security & Privacy > Microphone")
            return
        
        try:
            with mic as source:
                print("DEBUG: Microphone initialized")
                recognizer.adjust_for_ambient_noise(source)
                print("DEBUG: Ambient noise adjusted")
                
                while self.running:
                    try:
                        if not self.conversation_mode:
                            print("DEBUG: Listening for wake word...")
                            self.listening_started.emit()
                            print("DEBUG: Microphone listening started...")
                            audio = recognizer.listen(source, timeout=10)
                            print("DEBUG: Audio captured, processing...")
                            self.listening_stopped.emit()
                            
                            print("DEBUG: Sending to Google Speech Recognition...")
                            transcript = recognizer.recognize_google(audio)
                            print(f"DEBUG: Heard: '{transcript}'")
                            
                            if TRIGGER_WORD.lower() in transcript.lower():
                                print(f"DEBUG: Wake word detected in: '{transcript}'")
                                self.conversation_mode = True
                                last_interaction_time = time.time()
                                self.speaking_started.emit()
                                print("DEBUG: Speaking response...")
                                speak_text("Yes sir?")
                                self.speaking_stopped.emit()
                                print("DEBUG: Response spoken, waiting for command...")
                            else:
                                print(f"DEBUG: Wake word not found in: '{transcript}'")
                        else:
                            print("DEBUG: Listening for command...")
                            self.listening_started.emit()
                            audio = recognizer.listen(source, timeout=10)
                            self.listening_stopped.emit()
                            
                            command = recognizer.recognize_google(audio)
                            print(f"DEBUG: Command received: {command}")
                            self.user_message_ready.emit(command)
                            
                            # Process with agent
                            response = executor.invoke({"input": command})
                            content = response["output"]
                            print(f"DEBUG: Agent response: {content}")
                            
                            self.assistant_response_ready.emit(content)
                            self.speaking_started.emit()
                            speak_text(content)
                            self.speaking_stopped.emit()
                            
                            last_interaction_time = time.time()
                            
                            if time.time() - last_interaction_time > CONVERSATION_TIMEOUT:
                                print("DEBUG: Conversation timeout")
                                self.conversation_mode = False
                                
                    except sr.WaitTimeoutError:
                        print("DEBUG: Listening timeout (no speech detected)")
                        if (self.conversation_mode and 
                            time.time() - last_interaction_time > CONVERSATION_TIMEOUT):
                            print("DEBUG: Conversation mode timeout")
                            self.conversation_mode = False
                    except sr.UnknownValueError:
                        print("DEBUG: Could not understand audio")
                    except Exception as e:
                        print(f"DEBUG: Voice processing error: {e}")
                        self.error_occurred.emit(str(e))
                        time.sleep(1)
                        
        except Exception as e:
            print(f"DEBUG: Critical voice error: {e}")
            self.error_occurred.emit(f"Critical error: {str(e)}")
            
    def stop(self):
        self.running = False


class JarvisGUI(QMainWindow):
    """Main Jarvis Desktop GUI"""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.setup_ui()
        self.setup_system_tray()
        self.show()
        
    def setup_ui(self):
        self.setWindowTitle("J.A.R.V.I.S - Desktop Assistant")
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(800, 600)
        
        # Set window icon if available
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'jarvis_icon.png')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except:
            pass
        
        # Setup system tray
        self.setup_system_tray()
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1E1E1E, stop:1 #0F0F0F);
            }
            QWidget {
                background: transparent;
                color: #FFFFFF;
                font-family: 'Helvetica', Arial, sans-serif;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #2C2C2E;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #48484A;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #5E5E60;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Voice control
        self.setup_left_panel(splitter)
        
        # Right panel - Chat interface  
        self.setup_right_panel(splitter)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
        
    def setup_left_panel(self, parent):
        """Setup left panel with voice controls and status"""
        left_widget = QWidget()
        left_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2C2C2E, stop:1 #1C1C1E);
                border-radius: 15px;
                border: 1px solid #3A3A3C;
            }
        """)
        
        layout = QVBoxLayout(left_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("J.A.R.V.I.S")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Helvetica", 24, QFont.Weight.Bold))
        title.setStyleSheet("""
            color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #007AFF, stop:1 #00C7FF);
            background: transparent;
            padding: 10px;
        """)
        layout.addWidget(title)
        
        # Voice visualizer
        self.voice_visualizer = VoiceVisualizerWidget()
        layout.addWidget(self.voice_visualizer, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Status label
        self.status_label = QLabel("Ready - Say 'Jarvis' to start")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Helvetica", 14))
        self.status_label.setStyleSheet("""
            color: #8E8E93;
            background: transparent;
            padding: 10px;
        """)
        layout.addWidget(self.status_label)
        
        # Control buttons
        button_layout = QVBoxLayout()
        
        self.start_button = QPushButton("Start Voice Assistant")
        self.start_button.setFont(QFont("Helvetica", 12, QFont.Weight.Medium))
        self.start_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34C759, stop:1 #28A745);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #40D766, stop:1 #2EB84E);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2AA04A, stop:1 #1F7A33);
            }
        """)
        self.start_button.clicked.connect(self.start_voice_assistant)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Voice Assistant")
        self.stop_button.setFont(QFont("Helvetica", 12, QFont.Weight.Medium))
        self.stop_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF3B30, stop:1 #D32F2F);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF5722, stop:1 #E53E3E);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #C53030, stop:1 #9B2C2C);
            }
        """)
        self.stop_button.clicked.connect(self.stop_voice_assistant)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        # Add Skip Speech button
        self.skip_button = QPushButton("⏭️ Skip Speech")
        self.skip_button.setFont(QFont("Helvetica", 12, QFont.Weight.Medium))
        self.skip_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF9500, stop:1 #E68900);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFB84D, stop:1 #FF9500);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #E68900, stop:1 #CC7A00);
            }
            QPushButton:disabled {
                background: #555555;
                color: #888888;
            }
        """)
        self.skip_button.clicked.connect(self.skip_speech)
        self.skip_button.setEnabled(False)
        button_layout.addWidget(self.skip_button)
        
        # Add microphone test button
        self.test_mic_button = QPushButton("🎤 Test Microphone")
        self.test_mic_button.setFont(QFont("Helvetica", 12, QFont.Weight.Medium))
        self.test_mic_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6366F1, stop:1 #4F46E5);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7C7DF2, stop:1 #6366F1);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4F46E5, stop:1 #3B35E3);
            }
        """)
        self.test_mic_button.clicked.connect(self.test_microphone)
        button_layout.addWidget(self.test_mic_button)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        parent.addWidget(left_widget)
        
    def setup_right_panel(self, parent):
        """Setup right panel with chat interface"""
        right_widget = QWidget()
        right_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2C2C2E, stop:1 #1C1C1E);
                border-radius: 15px;
                border: 1px solid #3A3A3C;
            }
        """)
        
        layout = QVBoxLayout(right_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Chat title
        chat_title = QLabel("Conversation")
        chat_title.setFont(QFont("Helvetica", 18, QFont.Weight.Bold))
        chat_title.setStyleSheet("color: #FFFFFF; background: transparent;")
        layout.addWidget(chat_title)
        
        # Chat area
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        self.chat_layout.setSpacing(10)
        self.chat_layout.addStretch()
        
        self.chat_scroll.setWidget(self.chat_widget)
        layout.addWidget(self.chat_scroll)
        
        # Text input area
        input_layout = QHBoxLayout()
        
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type a message to Jarvis...")
        self.text_input.setFont(QFont("Helvetica", 12))
        self.text_input.setStyleSheet("""
            QLineEdit {
                background: #3A3A3C;
                border: 2px solid #48484A;
                border-radius: 10px;
                padding: 10px 15px;
                color: #FFFFFF;
            }
            QLineEdit:focus {
                border: 2px solid #007AFF;
            }
        """)
        self.text_input.returnPressed.connect(self.send_text_message)
        input_layout.addWidget(self.text_input)
        
        self.send_button = QPushButton("Send")
        self.send_button.setFont(QFont("Helvetica", 12, QFont.Weight.Medium))
        self.send_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #007AFF, stop:1 #0051D5);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0A84FF, stop:1 #005EDC);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0051D5, stop:1 #003DA8);
            }
        """)
        self.send_button.clicked.connect(self.send_text_message)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        parent.addWidget(right_widget)
        
    def setup_system_tray(self):
        """Setup system tray icon"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            
            # Create tray menu
            tray_menu = QMenu()
            
            show_action = QAction("Show Jarvis", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)
            
            hide_action = QAction("Hide Jarvis", self)
            hide_action.triggered.connect(self.hide)
            tray_menu.addAction(hide_action)
            
            tray_menu.addSeparator()
            
            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(self.quit_application)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.tray_icon_activated)
            
            # Set icon (you can replace this with a custom icon)
            self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
            self.tray_icon.show()
            
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
                
    def add_chat_message(self, text: str, is_user: bool = False):
        """Add a message to the chat interface"""
        print(f"DEBUG: Adding chat message: '{text}' (is_user={is_user})")
        bubble = ChatBubble(text, is_user)
        
        # Remove stretch before adding new message
        self.chat_layout.removeItem(self.chat_layout.itemAt(self.chat_layout.count() - 1))
        
        self.chat_layout.addWidget(bubble)
        self.chat_layout.addStretch()
        
        # Scroll to bottom
        QTimer.singleShot(100, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        ))
        
    def send_text_message(self):
        """Send text message to Jarvis"""
        text = self.text_input.text().strip()
        if not text:
            return
            
        print(f"DEBUG: Sending text message: {text}")
        self.text_input.clear()
        self.add_chat_message(text, is_user=True)
        
        # Create a worker thread for processing
        self.text_worker = TextProcessingThread(text)
        self.text_worker.response_ready.connect(self.on_text_response_ready)
        self.text_worker.error_occurred.connect(self.on_text_error)
        self.text_worker.start()
        
    def on_text_response_ready(self, content):
        """Handle text response ready signal"""
        print(f"DEBUG: Response signal received: {content}")
        self.add_chat_message(content, is_user=False)
        # Enable skip button before speaking
        self.skip_button.setEnabled(True)
        # Speak response in separate thread to avoid blocking
        threading.Thread(target=self.speak_with_skip_handling, args=(content,), daemon=True).start()
        
    def speak_with_skip_handling(self, text):
        """Speak text and handle skip button state"""
        try:
            speak_text(text)
        finally:
            # Disable skip button when done speaking (thread-safe)
            QTimer.singleShot(0, lambda: self.skip_button.setEnabled(False))
        
    def on_text_error(self, error_msg):
        """Handle text processing error"""
        print(f"DEBUG: Error signal received: {error_msg}")
        self.add_chat_message(error_msg, is_user=False)
        
    def add_response_to_chat(self, content):
        """Add response to chat - thread safe method"""
        # Use QTimer to ensure this runs in the main thread
        def add_now():
            print(f"DEBUG: Adding response to chat: {content}")
            self.add_chat_message(content, is_user=False)
        
        QTimer.singleShot(0, add_now)
        
    def add_response_message(self, content):
        """Add response message to chat - thread safe"""
        QTimer.singleShot(0, lambda: self.add_chat_message(content, is_user=False))
        
    def add_error_message(self, error):
        """Add error message to chat - thread safe"""
        QTimer.singleShot(0, lambda: self.add_chat_message(error, is_user=False))
        
    def test_microphone(self):
        """Test microphone access and permissions"""
        try:
            print("🎤 Testing microphone access...")
            audio = pyaudio.PyAudio()
            
            # List available audio devices
            print("Available audio devices:")
            for i in range(audio.get_device_count()):
                device_info = audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    print(f"  {i}: {device_info['name']}")
            
            # Try to record a short sample
            stream = audio.open(format=pyaudio.paInt16,
                              channels=1,
                              rate=44100,
                              input=True,
                              frames_per_buffer=1024)
            
            print("🎤 Recording 2 seconds...")
            frames = []
            for _ in range(0, int(44100 / 1024 * 2)):
                data = stream.read(1024)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            self.add_chat_message("✅ Microphone test successful! Audio recording works.", is_user=False)
            print("✅ Microphone test successful!")
            
        except Exception as e:
            error_msg = f"❌ Microphone test failed: {e}"
            print(error_msg)
            self.add_chat_message(f"❌ Microphone test failed. Please check:\n1. Microphone permissions in System Preferences\n2. Microphone is connected and working\n3. No other apps are using the microphone\n\nError: {e}", is_user=False)
    
    def start_voice_assistant(self):
        """Start the voice assistant"""
        if self.worker is None or not self.worker.isRunning():
            self.worker = JarvisWorker()
            self.worker.user_message_ready.connect(lambda msg: self.add_chat_message(msg, is_user=True))
            self.worker.assistant_response_ready.connect(lambda msg: self.add_chat_message(msg, is_user=False))
            self.worker.status_update.connect(lambda msg: self.add_chat_message(msg, is_user=False))
            self.worker.listening_started.connect(self.on_listening_started)
            self.worker.listening_stopped.connect(self.on_listening_stopped)
            self.worker.speaking_started.connect(self.on_speaking_started)
            self.worker.speaking_stopped.connect(self.on_speaking_stopped)
            self.worker.error_occurred.connect(self.on_error)
            
            self.worker.start()
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText("Listening for wake word...")
            
    def stop_voice_assistant(self):
        """Stop the voice assistant"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
            
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.skip_button.setEnabled(False)
        self.status_label.setText("Voice assistant stopped")
        self.voice_visualizer.stop_all()
        
    def skip_speech(self):
        """Skip current speech/TTS output"""
        try:
            from tools.jarvis_speech import stop_speech
            stop_speech()
            self.skip_button.setEnabled(False)
            self.status_label.setText("Speech skipped")
            print("DEBUG: Speech skipped by user")
        except Exception as e:
            print(f"DEBUG: Error skipping speech: {e}")
        
    def on_listening_started(self):
        """Handle listening started"""
        self.status_label.setText("🎤 Listening...")
        self.voice_visualizer.start_listening()
        
    def on_listening_stopped(self):
        """Handle listening stopped"""
        self.status_label.setText("Processing...")
        self.voice_visualizer.stop_all()
        
    def on_speaking_started(self):
        """Handle speaking started"""
        self.status_label.setText("🔊 Speaking...")
        self.voice_visualizer.start_speaking()
        self.skip_button.setEnabled(True)  # Enable skip button when speaking
        
    def on_speaking_stopped(self):
        """Handle speaking stopped"""
        self.status_label.setText("Listening for wake word...")
        self.voice_visualizer.stop_all()
        self.skip_button.setEnabled(False)  # Disable skip button when not speaking
        
    def on_error(self, error_msg: str):
        """Handle errors"""
        self.status_label.setText(f"Error: {error_msg}")
        self.add_chat_message(f"Error: {error_msg}", is_user=False)
        
    def closeEvent(self, event):
        """Handle window close event"""
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            self.quit_application()
            
    def quit_application(self):
        """Quit the application completely"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
            
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
            
        QApplication.quit()


def main():
    """Main function to run the Jarvis GUI"""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep app running when window is closed
    
    # Set application properties
    app.setApplicationName("J.A.R.V.I.S")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Jarvis AI")
    
    # Create and show main window
    window = JarvisGUI()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
