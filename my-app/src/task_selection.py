from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGridLayout, 
                            QPushButton, QLineEdit, QScrollArea)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon, QFont

class TaskCard(QPushButton):
    """Custom button widget for task selection"""
    def __init__(self, task_name, icon_path=None, parent=None):
        super().__init__(parent)
        self.task_name = task_name
        self.setCheckable(True)
        self.setFixedSize(120, 120)
        self.setStyleSheet("""
            QPushButton {
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 15px;
                background: white;
                text-align: center;
            }
            QPushButton:hover {
                border: 2px solid #4a90e2;
                background: #f0f7ff;
            }
            QPushButton:checked {
                border: 2px solid #4a90e2;
                background: #e6f0ff;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Add icon (placeholder - replace with actual icons)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setStyleSheet("background: transparent;")
        if icon_path:
            self.icon_label.setPixmap(QIcon(icon_path).pixmap(40, 40))
        
        # Add task name
        self.name_label = QLabel(task_name)
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.icon_label, 0, Qt.AlignHCenter)
        layout.addWidget(self.name_label, 0, Qt.AlignHCenter)
        layout.addStretch()
        
        self.setLayout(layout)


class TaskSelectionScreen(QWidget):
    """Screen for selecting the main task"""
    task_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ZenFlow - Select Task")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel#title {
                font-size: 24px;
                font-weight: 500;
                color: #333;
                margin-bottom: 30px;
            }
            QLineEdit {
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                min-width: 300px;
            }
            QPushButton#startButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: 500;
                margin-top: 20px;
            }
            QPushButton#startButton:hover {
                background-color: #3a7bc8;
            }
            QPushButton#startButton:disabled {
                background-color: #b0c4de;
            }
        """)
        
        self.selected_task = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 30, 40, 40)
        layout.setSpacing(0)
        
        # Title
        title = QLabel("What are you working on today?")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Task grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 4px;
            }
        """)
        
        grid_widget = QWidget()
        self.grid_layout = QGridLayout(grid_widget)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Define tasks with their icons (placeholder paths)
        self.tasks = [
            ("Coding & Development", "code.png"),
            ("UI/UX Designing", "design.png"),
            ("Video Editing", "video.png"),
            ("Content Writing", "writing.png"),
            ("Studying", "study.png"),
            ("Research", "research.png"),
            ("Online Teaching", "teaching.png"),
            ("Business / Freelancing", "business.png"),
            ("Marketing", "marketing.png"),
            ("Meetings", "meeting.png"),
        ]
        
        # Add task cards to grid
        self.task_buttons = []
        for i, (task_name, icon_path) in enumerate(self.tasks):
            row = i // 3
            col = i % 3
            card = TaskCard(task_name, icon_path)
            card.clicked.connect(lambda checked, t=task_name: self.on_task_selected(t))
            self.grid_layout.addWidget(card, row, col, 1, 1)
            self.task_buttons.append(card)
        
        # Add custom task input
        self.custom_task_input = QLineEdit()
        self.custom_task_input.setPlaceholderText("Or type your custom task...")
        self.custom_task_input.textChanged.connect(self.on_custom_task_changed)
        self.grid_layout.addWidget(self.custom_task_input, (len(self.tasks) // 3) + 1, 0, 1, 3)
        
        scroll.setWidget(grid_widget)
        layout.addWidget(scroll)
        
        # Start button
        self.start_button = QPushButton("Start My Session")
        self.start_button.setObjectName("startButton")
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.on_start_clicked)
        
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.addStretch()
        button_layout.addWidget(self.start_button)
        button_layout.addStretch()
        
        layout.addWidget(button_container)
        self.setLayout(layout)
    
    def on_task_selected(self, task_name):
        """Handle task selection"""
        self.selected_task = task_name
        self.start_button.setEnabled(True)
        
        # Update button states
        for btn in self.task_buttons:
            btn.setChecked(btn.task_name == task_name)
        
        # Clear custom task input if a predefined task is selected
        self.custom_task_input.clear()
    
    def on_custom_task_changed(self, text):
        """Handle custom task input"""
        if text.strip():
            self.selected_task = text.strip()
            self.start_button.setEnabled(True)
            
            # Uncheck all task buttons
            for btn in self.task_buttons:
                btn.setChecked(False)
        else:
            self.start_button.setEnabled(self.selected_task is not None)
    
    def on_start_clicked(self):
        """Emit signal when start button is clicked"""
        if self.selected_task:
            self.task_selected.emit(self.selected_task)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show the task selection screen
    window = TaskSelectionScreen()
    window.show()
    
    sys.exit(app.exec_())
