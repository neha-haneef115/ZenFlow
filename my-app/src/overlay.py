from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QApplication,
                           QHBoxLayout, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor, QKeyEvent
import logging

class FullScreenOverlay(QWidget):
    overlay_closed = pyqtSignal()
    
    def __init__(self, task_name, app_name, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint |
            Qt.WindowDoesNotAcceptFocus |
            Qt.Tool
        )
        
        # Make window transparent for click-through
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # Set window to be full screen and on top of everything
        self.setWindowState(Qt.WindowFullScreen)
        
        # Semi-transparent black background
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.9);
                color: white;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 15px 32px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                margin: 4px 2px;
                border-radius: 4px;
                min-width: 200px;
            }
            QPushButton#emergency {
                background-color: #f44336;
            }
            QLabel#title {
                font-size: 36px;
                font-weight: bold;
                margin-bottom: 30px;
            }
            QLabel#task {
                font-size: 24px;
                margin: 20px 0;
                color: #4CAF50;
            }
            QLabel#message {
                font-size: 18px;
                margin-bottom: 40px;
            }
        """)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        # Title
        title = QLabel("🚫 Focus Mode Active")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        
        # Task reminder
        task_label = QLabel(f"Task: {task_name}")
        task_label.setObjectName("task")
        task_label.setAlignment(Qt.AlignCenter)
        
        # Message
        message = QLabel(f"{app_name} is blocked during this focus session.")
        message.setObjectName("message")
        message.setAlignment(Qt.AlignCenter)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        back_btn = QPushButton("👈 Back to Work")
        back_btn.clicked.connect(self.close)
        
        emergency_btn = QPushButton("🔐 Emergency Override")
        emergency_btn.setObjectName("emergency")
        emergency_btn.clicked.connect(self.request_emergency_override)
        
        button_layout.addStretch()
        button_layout.addWidget(back_btn)
        button_layout.addWidget(emergency_btn)
        button_layout.addStretch()
        
        # Add widgets to layout
        layout.addWidget(title)
        layout.addWidget(task_label)
        layout.addWidget(message)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Prevent closing with Alt+F4 or other methods
        self.setWindowModality(Qt.ApplicationModal)
        
        # Track if we're in emergency override mode
        self.emergency_override = False
        
        # Log the overlay creation
        logging.info(f"Overlay created for blocked app: {app_name}")
    
    def request_emergency_override(self):
        """Handle emergency override request."""
        from PyQt5.QtWidgets import QInputDialog, QLineEdit
        
        password, ok = QInputDialog.getText(
            self,
            'Emergency Override',
            'Enter emergency override password:',
            QLineEdit.Password
        )
        
        # In a real app, you would verify the password here
        # For now, we'll just check if something was entered
        if ok and password:
            self.emergency_override = True
            self.close()
    
    def closeEvent(self, event):
        """Handle window close event."""
        if not self.emergency_override:
            # Log the return to work
            logging.info("User returned to work from overlay")
        else:
            # Log the emergency override
            logging.warning("Emergency override activated")
            
        self.overlay_closed.emit()
        event.accept()
    
    def keyPressEvent(self, event):
        """Override key press events to prevent closing with keyboard."""
        # Allow Alt+F4 to close in case of issues
        if event.key() == Qt.Key_F4 and (event.modifiers() & Qt.AltModifier):
            self.emergency_override = True
            self.close()
        else:
            event.ignore()  # Ignore other key presses
    
    def showEvent(self, event):
        """Ensure the window stays on top when shown."""
        self.activateWindow()
        self.raise_()
        super().showEvent(event)
