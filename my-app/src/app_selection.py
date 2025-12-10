from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QCheckBox, QScrollArea,
                            QPushButton, QFrame, QHBoxLayout, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

class AppCheckBox(QCheckBox):
    """Custom checkbox for app selection with icon and description"""
    def __init__(self, app_name, description="", icon_path=None, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        
        # Create main layout
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(15)
        
        # Add checkbox
        self.setStyleSheet("""
            QCheckBox {
                spacing: 15px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
        """)
        
        # Add icon (placeholder)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setStyleSheet("""
            QLabel {
                background: #e9ecef;
                border-radius: 5px;
                padding: 3px;
            }
        """)
        
        # App name and description
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        self.name_label = QLabel(app_name)
        self.name_label.setStyleSheet("font-weight: 500;")
        
        self.desc_label = QLabel(description)
        self.desc_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        self.desc_label.setWordWrap(True)
        
        text_layout.addWidget(self.name_label)
        text_layout.addWidget(self.desc_label)
        text_layout.addStretch()
        
        # Add widgets to layout
        layout.addWidget(self.icon_label)
        layout.addLayout(text_layout)
        layout.addStretch()
        
        # Set the layout to a container widget
        container = QWidget()
        container.setLayout(layout)
        
        # Set the container as the checkbox's layout
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(container)
        
        # Style the checkbox
        self.setStyleSheet("""
            QCheckBox {
                background: white;
                border-radius: 8px;
                padding: 0px;
                margin: 2px 0;
            }
            QCheckBox:hover {
                background: #f8f9fa;
            }
        """)


class AppSelectionScreen(QWidget):
    """Screen for selecting allowed and blocked applications"""
    session_started = pyqtSignal(dict)  # Emits dict of {app_name: allowed}
    
    def __init__(self, task_name, parent=None):
        super().__init__(parent)
        self.task_name = task_name
        self.apps = {}
        
        self.setWindowTitle(f"ZenFlow - {task_name}")
        self.setMinimumSize(900, 700)
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel#title {
                font-size: 22px;
                font-weight: 500;
                color: #333;
                margin-bottom: 5px;
            }
            QLabel#subtitle {
                color: #6c757d;
                margin-bottom: 25px;
            }
            QGroupBox {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 20px;
                padding-top: 15px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: #495057;
                font-weight: 500;
            }
            QPushButton#startButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 12px 40px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: 500;
                min-width: 200px;
            }
            QPushButton#startButton:hover {
                background-color: #3a7bc8;
            }
            QPushButton#backButton {
                background: transparent;
                color: #4a90e2;
                border: 1px solid #4a90e2;
                padding: 12px 25px;
                border-radius: 6px;
                font-size: 16px;
            }
            QPushButton#backButton:hover {
                background: #e6f0ff;
            }
        """)
        
        self.init_ui()
        self.load_app_suggestions()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(0)
        
        # Header
        title = QLabel(f"Smart App Control for: {self.task_name}")
        title.setObjectName("title")
        
        subtitle = QLabel("We've pre-selected apps that will help you stay focused. You can customize the list below.")
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        # Scroll area for app lists
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
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 15, 0)
        scroll_layout.setSpacing(15)
        
        # Section 1: Auto-Detected Work Apps
        work_group = QWidget()
        work_layout = QVBoxLayout(work_group)
        work_layout.setContentsMargins(0, 0, 0, 0)
        work_layout.setSpacing(10)
        
        work_label = QLabel("Recommended for your task:")
        work_label.setStyleSheet("font-weight: 500; color: #2c3e50; font-size: 16px;")
        
        self.work_apps_container = QVBoxLayout()
        self.work_apps_container.setSpacing(5)
        
        work_layout.addWidget(work_label)
        work_layout.addLayout(self.work_apps_container)
        work_layout.addStretch()
        
        # Section 2: Manually Allowed Apps
        manual_group = QWidget()
        manual_layout = QVBoxLayout(manual_group)
        manual_layout.setContentsMargins(0, 0, 0, 0)
        manual_layout.setSpacing(10)
        
        manual_label = QLabel("Additional helpful apps:")
        manual_label.setStyleSheet("font-weight: 500; color: #2c3e50; font-size: 16px;")
        
        self.manual_apps_container = QVBoxLayout()
        self.manual_apps_container.setSpacing(5)
        
        manual_layout.addWidget(manual_label)
        manual_layout.addLayout(self.manual_apps_container)
        manual_layout.addStretch()
        
        # Section 3: Distracting Apps
        distracting_group = QWidget()
        distracting_layout = QVBoxLayout(distracting_group)
        distracting_layout.setContentsMargins(0, 0, 0, 0)
        distracting_layout.setSpacing(10)
        
        distracting_label = QLabel("Potentially distracting apps:")
        distracting_label.setStyleSheet("font-weight: 500; color: #2c3e50; font-size: 16px;")
        
        distracting_note = QLabel("These will be blocked during your session. Uncheck any you need for work.")
        distracting_note.setStyleSheet("color: #6c757d; font-size: 13px; margin-bottom: 5px;")
        
        self.distracting_apps_container = QVBoxLayout()
        self.distracting_apps_container.setSpacing(5)
        
        distracting_layout.addWidget(distracting_label)
        distracting_layout.addWidget(distracting_note)
        distracting_layout.addLayout(self.distracting_apps_container)
        distracting_layout.addStretch()
        
        # Add all sections to scroll layout
        scroll_layout.addWidget(work_group)
        scroll_layout.addWidget(self.create_divider())
        scroll_layout.addWidget(manual_group)
        scroll_layout.addWidget(self.create_divider())
        scroll_layout.addWidget(distracting_group)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Buttons at bottom
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 20, 0, 0)
        button_layout.setSpacing(20)
        
        self.back_button = QPushButton("← Back")
        self.back_button.setObjectName("backButton")
        self.back_button.clicked.connect(self.go_back)
        
        self.start_button = QPushButton("Start Focus Session")
        self.start_button.setObjectName("startButton")
        self.start_button.clicked.connect(self.on_start_session)
        
        button_layout.addWidget(self.back_button)
        button_layout.addStretch()
        button_layout.addWidget(self.start_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_divider(self):
        """Create a horizontal divider line"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #dee2e6;")
        line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        return line
    
    def load_app_suggestions(self):
        """Load app suggestions based on the selected task"""
        # This would be replaced with AI-based suggestions in the real implementation
        task_apps = {
            # Work apps (pre-selected)
            'work': [],
            # Additional helpful apps (not pre-selected)
            'manual': [],
            # Distracting apps (blocked by default)
            'distracting': [
                ("Social Media", "Facebook, Instagram, Twitter, etc."),
                ("Entertainment", "YouTube, Netflix, Hulu, etc."),
                ("Gaming", "Steam, Epic Games, etc."),
                ("Shopping", "Amazon, eBay, etc."),
                ("News", "News websites, Reddit, etc.")
            ]
        }
        
        # Task-specific app suggestions
        task_lower = self.task_name.lower()
        if 'code' in task_lower or 'dev' in task_lower:
            task_apps['work'].extend([
                ("VS Code", "Code editor"),
                ("GitHub Desktop", "Version control"),
                ("Postman", "API testing"),
                ("Docker", "Containerization"),
                ("Terminal", "Command line")
            ])
            task_apps['manual'].extend([
                ("Chrome", "Web browser"),
                ("Stack Overflow", "Developer Q&A"),
                ("Notion", "Notes & documentation"),
                ("Slack", "Team communication"),
                ("Trello", "Task management")
            ])
        elif 'design' in task_lower or 'ui' in task_lower or 'ux' in task_lower:
            task_apps['work'].extend([
                ("Figma", "UI/UX design"),
                ("Adobe XD", "UI/UX design"),
                ("Photoshop", "Image editing"),
                ("Illustrator", "Vector graphics"),
                ("Sketch", "UI/UX design")
            ])
            task_apps['manual'].extend([
                ("Chrome", "Web browser"),
                ("Dribbble", "Design inspiration"),
                ("Behance", "Design portfolio"),
                ("Slack", "Team communication"),
                ("Notion", "Project documentation")
            ])
        # Add more task-specific suggestions as needed
        
        # Add the apps to the UI
        for app_name, description in task_apps['work']:
            self.add_app(app_name, description, 'work', checked=True)
        
        for app_name, description in task_apps['manual']:
            self.add_app(app_name, description, 'manual', checked=False)
        
        for app_name, description in task_apps['distracting']:
            self.add_app(app_name, description, 'distracting', checked=False)
    
    def add_app(self, name, description, category, checked=True):
        """Add an app to the appropriate section"""
        app_checkbox = AppCheckBox(name, description)
        app_checkbox.setChecked(checked)
        
        if category == 'work':
            self.work_apps_container.addWidget(app_checkbox)
        elif category == 'manual':
            self.manual_apps_container.addWidget(app_checkbox)
        elif category == 'distracting':
            self.distracting_apps_container.addWidget(app_checkbox)
        
        # Store reference to the checkbox
        if category not in self.apps:
            self.apps[category] = {}
        self.apps[category][name] = app_checkbox
    
    def on_start_session(self):
        """Emit signal with the selected apps when starting the session"""
        app_states = {}
        
        # Add work apps (allowed)
        if 'work' in self.apps:
            for name, checkbox in self.apps['work'].items():
                app_states[name] = checkbox.isChecked()
        
        # Add manual apps (user-selected)
        if 'manual' in self.apps:
            for name, checkbox in self.apps['manual'].items():
                app_states[name] = checkbox.isChecked()
        
        # Add distracting apps (blocked by default unless unchecked)
        if 'distracting' in self.apps:
            for name, checkbox in self.apps['distracting'].items():
                app_states[name] = not checkbox.isChecked()  # Invert because unchecked means blocked
        
        self.session_started.emit(app_states)
    
    def go_back(self):
        """Go back to the task selection screen"""
        self.parent().show_task_selection()
        self.hide()


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow
    
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("ZenFlow - Test")
            self.setMinimumSize(900, 700)
            
            # Create and set the app selection screen
            self.app_selection = AppSelectionScreen("Coding & Development", self)
            self.setCentralWidget(self.app_selection)
            
            # Connect signals
            self.app_selection.session_started.connect(self.on_session_started)
        
        def on_session_started(self, app_states):
            print("Session started with apps:", app_states)
            # In a real app, you would start the monitoring service here
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())
