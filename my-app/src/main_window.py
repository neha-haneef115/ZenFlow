from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, 
                            QStackedWidget, QHBoxLayout, QFrame, QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QLinearGradient, QIcon
import os
import sys

class TaskCard(QPushButton):
    """A custom button widget for task selection."""
    # Custom signal emitted when the card is selected
    selected = pyqtSignal(bool)
    
    def __init__(self, title, description, icon_path=None, parent=None):
        super().__init__(parent)
        self.title = title
        self.description = description
        self.icon_path = icon_path
        self._setup_ui()
        
    def _setup_ui(self):
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(100)
        self.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                text-align: left;
                padding: 16px;
                font-size: 16px;
                font-weight: 500;
                color: #333;
            }
            QPushButton:hover {
                border-color: #4a90e2;
                background-color: #f8f9ff;
            }
            QPushButton:checked {
                border-color: #4a90e2;
                background-color: #f0f4ff;
                border-width: 2px;
            }
            QPushButton:pressed {
                background-color: #e8f0fe;
            }
        """)
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)
        
        # Icon
        if self.icon_path and os.path.exists(self.icon_path):
            icon_label = QLabel()
            icon_pixmap = QPixmap(self.icon_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)
            layout.addWidget(icon_label, 0, Qt.AlignLeft | Qt.AlignVCenter)
        
        # Text content
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)
        
        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-weight: 600; font-size: 16px; color: #2c3e50;")
        
        desc_label = QLabel(self.description)
        desc_label.setStyleSheet("color: #7f8c8d; font-size: 13px;")
        desc_label.setWordWrap(True)
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)
        text_layout.addStretch()
        
        layout.addWidget(text_widget, 1)
        
        # Selection indicator
        self.selection_indicator = QLabel()
        self.selection_indicator.setFixedSize(12, 12)
        self.selection_indicator.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: 2px solid #4a90e2;
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.selection_indicator, 0, Qt.AlignRight | Qt.AlignVCenter)
        
        # Animation for the selection indicator
        self.animation = QPropertyAnimation(self.selection_indicator, b"size")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.OutBack)
        
    def setChecked(self, checked):
        """Set the checked state of the card and emit the selected signal."""
        if self.isChecked() != checked:  # Only proceed if the state is actually changing
            super().setChecked(checked)
            # Update the visual state
            if checked:
                self.animation.setStartValue(QSize(0, 0))
                self.animation.setEndValue(QSize(12, 12))
                self.animation.start()
                self.selection_indicator.setStyleSheet("""
                    QLabel {
                        background-color: #4a90e2;
                        border: 2px solid #4a90e2;
                        border-radius: 6px;
                    }
                """)
            else:
                self.selection_indicator.setStyleSheet("""
                    QLabel {
                        background-color: transparent;
                        border: 2px solid #4a90e2;
                        border-radius: 6px;
                    }
                """)
            # Emit the signal after updating the visual state
            self.selected.emit(checked)
            print(f"Emitted selected signal with: {checked}")

class TaskSelectionPage(QWidget):
    """The task selection screen that shows available task categories."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.selected_task = None
        self.task_cards = []
        self._setup_ui()
        
    def _setup_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(30)
        
        # Header
        header = QLabel("What are you working on today?")
        header.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: 600;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)
        
        subheader = QLabel("Select a category that best matches your current focus")
        subheader.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 14px;
                margin-bottom: 20px;
            }
        """)
        
        # Scroll area for task cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f5f5f7;
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #d1d5db;
                min-height: 30px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Container for task cards
        tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(tasks_container)
        self.tasks_layout.setContentsMargins(5, 5, 15, 5)  # Right margin for scrollbar
        self.tasks_layout.setSpacing(12)
        
        # Add task cards
        self._add_task_cards()
        
        # Add stretch to push cards to the top
        self.tasks_layout.addStretch()
        
        scroll.setWidget(tasks_container)
        
        # Next button
        self.next_button = QPushButton("Continue")
        self.next_button.setFixedHeight(48)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 500;
                padding: 0 24px;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #a0a0a0;
            }
            QPushButton:hover {
                background-color: #3a7bc8;
            }
            QPushButton:pressed {
                background-color: #2c6cb0;
            }
        """)
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self._on_next_clicked)
        
        # Add widgets to layout
        layout.addWidget(header)
        layout.addWidget(subheader)
        layout.addWidget(scroll, 1)  # Make scroll area take remaining space
        
        # Button container - ensure it's properly added to the layout
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 10, 0, 0)  # Add some top margin
        button_layout.addStretch()
        button_layout.addWidget(self.next_button)
        
        # Add button container to main layout with stretch factor 0 to prevent it from expanding
        layout.addWidget(button_container, 0)
    
    def _add_task_cards(self):
        """Add task cards to the layout."""
        tasks = [
            {
                "title": "Coding & Development",
                "description": "Writing, testing, and debugging code",
                "icon": "icons/code.png"
            },
            {
                "title": "UI/UX Designing",
                "description": "Creating user interfaces and experiences",
                "icon": "icons/design.png"
            },
            {
                "title": "Video Editing",
                "description": "Editing and producing video content",
                "icon": "icons/video.png"
            },
            {
                "title": "Content Writing",
                "description": "Writing articles, blogs, or documentation",
                "icon": "icons/writing.png"
            },
            {
                "title": "Studying",
                "description": "Learning new concepts or studying for exams",
                "icon": "icons/study.png"
            },
            {
                "title": "Research",
                "description": "Conducting online research and analysis",
                "icon": "icons/research.png"
            },
            {
                "title": "Online Teaching",
                "description": "Teaching or conducting online classes",
                "icon": "icons/teaching.png"
            },
            {
                "title": "Business / Freelancing",
                "description": "Managing business or freelance work",
                "icon": "icons/business.png"
            },
            {
                "title": "Marketing",
                "description": "Handling marketing and social media",
                "icon": "icons/marketing.png"
            },
            {
                "title": "Meetings",
                "description": "Attending or conducting meetings",
                "icon": "icons/meeting.png"
            },
            {
                "title": "Custom Task",
                "description": "Define your own focus area",
                "icon": "icons/custom.png"
            }
        ]
        
        # Create a card for each task
        for task in tasks:
            card = TaskCard(
                task["title"],
                task["description"],
                task["icon"]
            )
            
            # Connect signals
            card.clicked.connect(lambda checked, c=card: self._on_card_clicked(c))
            card.selected.connect(self._on_card_selected)
            
            self.task_cards.append(card)
            self.tasks_layout.addWidget(card)
    
    def _on_card_selected(self, selected):
        """Handle card selection changes."""
        sender = self.sender()
        if not hasattr(sender, 'title'):
            print("Warning: Sender has no title attribute")
            return  # Safety check
            
        print(f"Card '{sender.title}' selected: {selected}")
            
        if selected:
            # Uncheck all other cards
            for card in self.task_cards:
                if card != sender and card.isChecked():
                    print(f"Unchecking other card: {card.title}")
                    card.setChecked(False)
            
            # Update selected task
            self.selected_task = sender.title
            print(f"Selected task: {self.selected_task}")
        else:
            if self.selected_task == sender.title:
                print(f"Deselected task: {self.selected_task}")
                self.selected_task = None
    
        # Update button state based on selection
        is_any_selected = any(card.isChecked() for card in self.task_cards)
        print(f"Any card selected: {is_any_selected}")
        print(f"Button enabled before: {self.next_button.isEnabled()}")
        self.next_button.setEnabled(is_any_selected)
        print(f"Button enabled after: {self.next_button.isEnabled()}")
        
        # Force UI update
        self.next_button.repaint()
        QApplication.processEvents()
    
    def _on_card_clicked(self, card):
        """Handle card click event."""
        print(f"Card '{card.title}' clicked. Current checked state: {card.isChecked()}")
        # Toggle the clicked card's checked state
        new_state = not card.isChecked()
        print(f"Setting checked state to: {new_state}")
        card.setChecked(new_state)
        
        # Ensure only one card is selected at a time
        if new_state:  # If we're checking this card
            for c in self.task_cards:
                if c != card and c.isChecked():
                    print(f"Unchecking other card: {c.title}")
                    c.setChecked(False)
        
        # Force update the button state
        is_any_selected = any(c.isChecked() for c in self.task_cards)
        print(f"Any card selected after click: {is_any_selected}")
        self.next_button.setEnabled(is_any_selected)
        
        # Update selected task
        self.selected_task = card.title if is_any_selected else None
        print(f"Selected task: {self.selected_task}")
        
        # Force UI update
        self.next_button.repaint()
        QApplication.processEvents()
    
    def _on_next_clicked(self):
        """Handle next button click."""
        print("Next button clicked!")
        if self.selected_task:
            print(f"Proceeding with task: {self.selected_task}")
            self.parent.show_app_selection(self.selected_task)
        else:
            print("No task selected, but button was clicked. This shouldn't happen!")

class MainWindow(QMainWindow):
    """The main application window."""
    def __init__(self, config=None):
        super().__init__()
        # Store the config
        self.config = config or {}
        
        # Set window title and size from config if available
        app_name = self.config.get('app_name', 'ZenFlow')
        self.setWindowTitle(app_name)
        
        # Set window size from config or use defaults
        width = self.config.get('window', {}).get('width', 1000)
        height = self.config.get('window', {}).get('height', 700)
        self.resize(width, height)
        self.setMinimumSize(800, 600)
        
        # Set theme from config or use default
        theme = self.config.get('theme', 'light')
        self._apply_theme(theme)
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create stacked widget for pages
        self.stacked_widget = QStackedWidget()
        
        # Create pages
        self.task_selection_page = TaskSelectionPage(self)
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.task_selection_page)
        
        # Set up main layout
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stacked_widget)
        
        # Apply window styling
        self._apply_styles()
    
    def _apply_styles(self):
        """Apply window styling."""
        # Additional styling can be added here if needed
        pass
        
    def _apply_theme(self, theme_name):
        """Apply theme based on configuration."""
        if theme_name == 'dark':
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #3a3a3a;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 5px 10px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                }
            """)
        else:  # Default light theme
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f8f9ff;
                    color: #333333;
                }
                QPushButton {
                    background-color: #f0f0f0;
                    color: #333333;
                    border: 1px solid #cccccc;
                    padding: 5px 10px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
    
    def show_app_selection(self, task):
        """Show the app selection page."""
        # TODO: Implement app selection page
        print(f"Selected task: {task}")

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
