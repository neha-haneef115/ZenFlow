import sys
import os
import json
import logging
import time
import atexit
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, 
    QPushButton, QInputDialog, QMessageBox, QSystemTrayIcon, 
    QMenu, QAction, QGroupBox, QCheckBox, QListWidget, QListWidgetItem, QHBoxLayout,
    QStackedWidget, QLineEdit, QComboBox, QFormLayout, QScrollArea
)
from PyQt5.QtCore import QTimer, Qt, QSettings, QStandardPaths
from PyQt5.QtGui import QIcon, QFont, QPixmap

# Import the overlay
from src.overlay import FullScreenOverlay

# Platform-specific imports
try:
    import win32gui  # Windows
    import win32process
    import psutil
    PLATFORM = 'windows'
except ImportError:
    try:
        from AppKit import NSWorkspace  # macOS
        from Foundation import NSBundle
        PLATFORM = 'darwin'
    except ImportError:
        try:
            import subprocess  # Linux
            PLATFORM = 'linux'
        except ImportError:
            PLATFORM = 'unknown'

class TaskSelectionPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        # Title
        title = QLabel("Welcome to ZenFlow")
        title.setFont(QFont('Arial', 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        
        # Task selection
        task_label = QLabel("What are you working on?")
        task_label.setFont(QFont('Arial', 16))
        
        self.task_combo = QComboBox()
        self.task_combo.addItems(["Coding", "Designing", "Studying", "Writing", "Other"])
        self.task_combo.setFont(QFont('Arial', 12))
        self.task_combo.setFixedWidth(300)
        
        # Custom task input
        self.custom_task = QLineEdit()
        self.custom_task.setPlaceholderText("Enter custom task...")
        self.custom_task.setFont(QFont('Arial', 12))
        self.custom_task.setFixedWidth(300)
        self.custom_task.hide()
        
        self.task_combo.currentTextChanged.connect(self.on_task_changed)
        
        # Next button
        next_btn = QPushButton("Next")
        next_btn.clicked.connect(self.on_next_clicked)
        next_btn.setFixedWidth(200)
        
        # Add widgets to layout
        layout.addWidget(title)
        layout.addSpacing(40)
        layout.addWidget(task_label)
        layout.addWidget(self.task_combo, alignment=Qt.AlignCenter)
        layout.addWidget(self.custom_task, alignment=Qt.AlignCenter)
        layout.addSpacing(40)
        layout.addWidget(next_btn, alignment=Qt.AlignCenter)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def on_task_changed(self, text):
        self.custom_task.setVisible(text == "Other")
    
    def on_next_clicked(self):
        task = self.task_combo.currentText()
        if task == "Other":
            task = self.custom_task.text().strip()
            if not task:
                QMessageBox.warning(self, "Error", "Please enter a task")
                return
        
        self.parent.task_selected(task)


class AppSelectionPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Select Allowed Apps")
        title.setFont(QFont('Arial', 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        
        # Description
        desc = QLabel("Check the apps you want to allow during your focus session.")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        
        # App list
        self.app_list = QListWidget()
        self.populate_app_list()
        
        # Buttons
        btn_layout = QHBoxLayout()
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.parent.show_task_selection)
        
        self.start_btn = QPushButton("Start Focus Session")
        self.start_btn.clicked.connect(self.on_start_clicked)
        
        btn_layout.addWidget(back_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.start_btn)
        
        # Add widgets to layout
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(self.app_list)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def populate_app_list(self):
        # This is a simplified version. In a real app, you would scan for installed apps
        common_apps = [
            "Visual Studio Code", "PyCharm", "IntelliJ", "Sublime Text",
            "Google Chrome", "Firefox", "Microsoft Edge", "Safari",
            "Microsoft Word", "Microsoft Excel", "Microsoft PowerPoint",
            "Slack", "Discord", "Zoom", "Microsoft Teams"
        ]
        
        for app in common_apps:
            item = QListWidgetItem(app)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)  # Default to checked
            self.app_list.addItem(item)
    
    def get_selected_apps(self):
        selected = []
        for i in range(self.app_list.count()):
            item = self.app_list.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.text())
        return selected
    
    def on_start_clicked(self):
        selected_apps = self.get_selected_apps()
        if not selected_apps:
            QMessageBox.warning(self, "Error", "Please select at least one app")
            return
        
        self.parent.start_session(selected_apps)


class ProductivityTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZenFlow - Productivity & Health Tracker")
        self.setMinimumSize(800, 600)
        
        # Initialize settings
        self.settings = QSettings("ZenFlow", "FocusFlow")
        
        # Initialize app data
        self.session_data = {
            'start_time': None,
            'end_time': None,
            'purpose': '',
            'allowed_apps': [],
            'blocked_events': [],
            'health_events': [],
            'distractions': 0,
            'focus_time': 0  # in seconds
        }
        
        # Health tracking configuration (in seconds)
        self.health_config = {
            'break': {
                'interval': 25 * 60,  # 25 minutes
                'last_triggered': None,
                'enabled': True,
                'message': "Time for a short break! Stand up and stretch for a minute.",
                'title': "Break Reminder"
            },
            'eye_strain': {
                'interval': 20 * 60,  # 20 minutes
                'last_triggered': None,
                'enabled': True,
                'message': "20-20-20 Rule: Look at something 20 feet away for 20 seconds.",
                'title': "Eye Strain Prevention"
            },
            'hydration': {
                'interval': 60 * 60,  # 60 minutes
                'last_triggered': None,
                'enabled': True,
                'message': "Stay hydrated! Please drink some water.",
                'title': "Hydration Reminder"
            },
            'posture': {
                'interval': 30 * 60,  # 30 minutes
                'last_triggered': None,
                'enabled': True,
                'message': "Posture check! Sit up straight and relax your shoulders.",
                'title': "Posture Reminder"
            }
        }
        
        self.setup_ui()
        self.setup_system_tray()
        self.setup_logging()
        self.show_purpose_dialog()
        
        # Start monitoring
        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self.check_active_window)
        self.monitor_timer.start(2000)  # Check every 2 seconds
        
        # Health reminder timer (check every 30 seconds)
        self.health_timer = QTimer(self)
        self.health_timer.timeout.connect(self.check_health_reminders)
        self.health_timer.start(30000)  # Check every 30 seconds
        
        # Track last notification time to avoid notification spam
        self.last_notification_time = {}
        self.notification_cooldown = 5 * 60  # 5 minutes cooldown between same type of notifications
    
    def setup_ui(self):
        """Set up the main application UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Session info
        self.session_label = QLabel("No active session")
        self.session_label.setAlignment(Qt.AlignCenter)
        self.session_label.setStyleSheet("font-size: 18px; margin: 20px;")
        
        # Timer display
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 36px; font-weight: bold; margin: 20px;")
        
        # Allowed apps
        self.apps_label = QLabel("Allowed Applications:")
        self.apps_list = QLabel("None")
        
        # Health status
        self.health_label = QLabel("Next health check: 24:59")
        
        # End session button
        self.end_button = QPushButton("End Focus Session")
        self.end_button.clicked.connect(self.end_session)
        
        # Add widgets to layout
        layout.addWidget(self.session_label)
        layout.addWidget(self.timer_label)
        layout.addWidget(self.apps_label)
        layout.addWidget(self.apps_list)
        layout.addWidget(self.health_label)
        layout.addStretch()
        layout.addWidget(self.end_button)
    
    def setup_system_tray(self):
        # Set up system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        # Create a simple icon if theme icon is not available
        if not self.tray_icon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(QIcon(), self)
        else:
            # Try to use a theme icon, fallback to a simple one
            self.tray_icon.setIcon(QIcon.fromTheme("appointment-new", QIcon(":/icons/icon.png")))
        
        # Create tray menu
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close_application)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def setup_logging(self):
        """Set up logging to file."""
        log_dir = os.path.join(os.path.expanduser("~"), ".focusflow_logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def show_purpose_dialog(self):
        """Show dialog to get user's work purpose."""
        purpose, ok = QInputDialog.getText(
            self, 
            "ZenFlow - Work Purpose",
            "What are you working on today?"
        )
        
        if ok and purpose:
            self.session_data['purpose'] = purpose
            self.session_data['start_time'] = datetime.now().isoformat()
            # Update the task display label in the session page
            if hasattr(self, 'task_display'):
                self.task_display.setText(f"Focusing on: {purpose}")
            self.start_session_timer()
            logging.info(f"Session started. Purpose: {purpose}")
        else:
            QMessageBox.warning(
                self,
                "Purpose Required",
                "Please enter a purpose to start your focus session.",
                QMessageBox.Ok
            )
            self.show_purpose_dialog()
    
    def start_session_timer(self):
        """Start the session timer."""
        self.session_start_time = datetime.now()
        self.session_timer = QTimer(self)
        self.session_timer.timeout.connect(self.update_timer)
        self.session_timer.start(1000)  # Update every second
    
    def check_active_window(self):
        """Check the currently active window and handle app blocking."""
        try:
            if PLATFORM == 'windows':
                window = win32gui.GetForegroundWindow()
                _, pid = win32process.GetWindowThreadProcessId(window)
                process = psutil.Process(pid)
                app_name = process.name()
                window_title = win32gui.GetWindowText(window)
            elif PLATFORM == 'darwin':
                app_name = NSWorkspace.sharedWorkspace().activeApplication().get('NSApplicationName', '')
                window_title = ""  # Not easily available on macOS
            else:  # Linux
                result = subprocess.run(['xdotool', 'getwindowfocus', 'getwindowname'], 
                                      capture_output=True, text=True)
                window_title = result.stdout.strip()
                app_name = window_title.split(' - ')[-1]  # Simple heuristic
            
            # Skip if no app name or same as last check
            if not app_name or app_name == self.last_active_window:
                return
                
            self.last_active_window = app_name
            
            # Check if app is allowed
            if app_name and app_name not in self.session_data['allowed_apps']:
                self.handle_blocked_app(app_name, window_title)
                
        except Exception as e:
            logging.error(f"Error checking active window: {e}")
            # Don't show error to user to avoid distraction
    
    def handle_blocked_app(self, app_name, window_title):
        """Handle when a blocked app is detected by showing a full-screen overlay."""
        # Log the distraction
        self.session_data['distractions'] += 1
        self.distractions_label.setText(f"Distractions Blocked: {self.session_data['distractions']}")
        
        # Log the blocked event
        self.session_data['blocked_events'].append({
            'time': datetime.now().isoformat(),
            'app': app_name,
            'window_title': window_title
        })
        
        # Only show overlay if not already showing for this app
        if not self.overlay and app_name != self.current_blocked_app:
            self.current_blocked_app = app_name
            
            # Create and show the overlay
            self.overlay = FullScreenOverlay(
                self.session_data['purpose'],
                app_name,
                self
            )
            
            # Connect overlay closed signal
            self.overlay.overlay_closed.connect(self.on_overlay_closed)
            
            # Show the overlay
            self.overlay.showFullScreen()
            
            # Bring the overlay to front
            self.overlay.raise_()
            self.overlay.activateWindow()
            
            logging.info(f"Showing overlay for blocked app: {app_name}")
    
    def on_overlay_closed(self):
        """Handle when the overlay is closed."""
        if self.overlay:
            if not self.overlay.emergency_override:
                # User chose to go back to work
                self.bring_allowed_app_to_front()
            
            # Clean up the overlay
            self.overlay.deleteLater()
            self.overlay = None
            self.current_blocked_app = None
    
    def bring_allowed_app_to_front(self):
        """Bring an allowed app to the front."""
        if not self.session_data['allowed_apps']:
            return
            
        # Try to find and focus an allowed app
        if PLATFORM == 'windows':
            try:
                # Get list of all windows
                def enum_windows_callback(hwnd, allowed_apps):
                    if win32gui.IsWindowVisible(hwnd):
                        try:
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            process = psutil.Process(pid)
                            if process.name() in allowed_apps:
                                # Found an allowed app, bring it to front
                                win32gui.ShowWindow(hwnd, 9)  # SW_RESTORE
                                win32gui.SetForegroundWindow(hwnd)
                                return False  # Stop enumeration
                        except:
                            pass
                    return True  # Continue enumeration
                
                # Enumerate windows
                win32gui.EnumWindows(enum_windows_callback, self.session_data['allowed_apps'])
                
            except Exception as e:
                logging.error(f"Error bringing allowed app to front: {e}")
    
    def check_health_reminders(self):
        """Check and trigger health reminders based on configured intervals."""
        current_time = datetime.now()
        
        for reminder_type, config in self.health_config.items():
            if not config['enabled']:
                continue
                
            # Check if it's time to show the reminder
            if (config['last_triggered'] is None or 
                (current_time - config['last_triggered']).total_seconds() >= config['interval']):
                
                # Check cooldown to avoid notification spam
                last_notif = self.last_notification_time.get(reminder_type, None)
                if last_notif and (current_time - last_notif).total_seconds() < self.notification_cooldown:
                    continue
                    
                self.show_health_reminder(reminder_type)
                config['last_triggered'] = current_time
                self.last_notification_time[reminder_type] = current_time
                
                # Log the health event
                self.session_data['health_events'].append({
                    'time': current_time.isoformat(),
                    'type': reminder_type,
                    'title': config['title'],
                    'message': config['message']
                })
                
                # Don't show multiple reminders at the exact same time
                time.sleep(1)  # Small delay between reminders
    
    def show_health_reminder(self, reminder_type):
        """Show a non-intrusive health reminder notification."""
        config = self.health_config.get(reminder_type, {})
        if not config:
            return
            
        # Show system tray notification
        self.tray_icon.showMessage(
            config['title'],
            config['message'],
            QSystemTrayIcon.Information,
            10000  # Show for 10 seconds
        )
        
        # Optional: Flash the taskbar icon
        if hasattr(self, 'isVisible') and not self.isVisible():
            self.tray_icon.setIcon(QIcon("icon_alert.png"))
            QTimer.singleShot(1000, lambda: self.tray_icon.setIcon(QIcon("icon_normal.png")))
            
    def setup_ui(self):
        """Set up the main application UI with health tracking controls."""
        # Create the central widget and set it
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create stacked widget for different pages
        self.stacked_widget = QStackedWidget()
        
        # Create pages
        self.task_page = TaskSelectionPage(self)
        self.app_selection_page = AppSelectionPage(self)
        self.session_page = self.create_session_page()
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.task_page)
        self.stacked_widget.addWidget(self.app_selection_page)
        self.stacked_widget.addWidget(self.session_page)
        
        # Set initial page
        self.stacked_widget.setCurrentIndex(0)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stacked_widget)
        self.central_widget.setLayout(main_layout)
        
        # Initialize session timer
        self.session_timer = QTimer(self)
        self.session_timer.timeout.connect(self.update_timer)
        
        # Initialize overlay
        self.overlay = None
        self.current_blocked_app = None
        
        # Track last active window
        self.last_active_window = None
        
        # Load settings
        self.load_settings()
    
    def create_session_page(self):
        """Create the session page with timer and stats."""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Timer display
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("""
            font-size: 48px; 
            font-weight: bold;
            color: #2c3e50;
            margin: 20px 0;
        """)
        
        # Task display
        self.task_display = QLabel("Task: ")
        self.task_display.setAlignment(Qt.AlignCenter)
        self.task_display.setStyleSheet("""
            font-size: 18px;
            color: #34495e;
            margin-bottom: 20px;
        """)
        
        # Stats group
        stats_group = QGroupBox("Session Stats")
        stats_layout = QVBoxLayout()
        
        # Stats labels
        self.focus_time_label = QLabel("Focus Time: 00:00:00")
        self.distractions_label = QLabel("Distractions Blocked: 0")
        self.productivity_label = QLabel("Productivity Score: 100%")
        
        for label in [self.focus_time_label, self.distractions_label, self.productivity_label]:
            label.setStyleSheet("font-size: 14px; margin: 5px 0;")
            stats_layout.addWidget(label)
        
        stats_group.setLayout(stats_layout)
        
        # Health reminders
        health_group = QGroupBox("Upcoming Health Reminders")
        health_layout = QVBoxLayout()
        
        self.reminder_labels = {
            'break': QLabel("Next break: 25:00"),
            'eye_strain': QLabel("Next eye break: 20:00"),
            'hydration': QLabel("Next hydration: 60:00"),
            'posture': QLabel("Posture check: 30:00")
        }
        
        for label in self.reminder_labels.values():
            label.setStyleSheet("font-size: 12px; color: #7f8c8d; margin: 2px 0;")
            health_layout.addWidget(label)
        
        health_group.setLayout(health_layout)
        
        # End session button
        end_btn = QPushButton("End Session")
        end_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 4px;
                margin: 20px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        end_btn.clicked.connect(self.end_session)
        
        # Add widgets to layout
        layout.addWidget(self.timer_label)
        layout.addWidget(self.task_display)
        layout.addWidget(stats_group)
        layout.addWidget(health_group)
        layout.addStretch()
        layout.addWidget(end_btn, alignment=Qt.AlignCenter)
        
        page.setLayout(layout)
        return page
    
    def update_apps_list(self):
        """Update the displayed list of allowed apps."""
        self.apps_list.clear()
        if not self.session_data['allowed_apps']:
            self.apps_list.addItem("No applications allowed")
        else:
            for app in self.session_data['allowed_apps']:
                self.apps_list.addItem(app)
    
    def end_session(self):
        """End the current focus session and show summary."""
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "End Session",
            "Are you sure you want to end this focus session?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
            
        try:
            # Record end time
            self.session_data['end_time'] = datetime.now().isoformat()
            
            # Stop all timers
            if hasattr(self, 'session_timer') and self.session_timer.isActive():
                self.session_timer.stop()
            if hasattr(self, 'monitor_timer') and self.monitor_timer.isActive():
                self.monitor_timer.stop()
            if hasattr(self, 'health_timer') and self.health_timer.isActive():
                self.health_timer.stop()
            
            # Calculate session duration
            start_time = datetime.fromisoformat(self.session_data['start_time'])
            end_time = datetime.fromisoformat(self.session_data['end_time'])
            duration = end_time - start_time
            
            # Calculate productivity score (simplified)
            total_seconds = duration.total_seconds()
            distraction_penalty = min(self.session_data['distractions'] * 5, 50)  # Max 50% penalty
            productivity_score = max(0, 100 - distraction_penalty)
            
            # Create summary dialog
            summary = f"""
            <h2>Session Complete! 🎉</h2>
            <p><b>Task:</b> {self.session_data['purpose']}</p>
            <p><b>Duration:</b> {str(duration).split('.')[0]}</p>
            <p><b>Distractions Blocked:</b> {self.session_data['distractions']}</p>
            <p><b>Health Reminders:</b> {len(self.session_data['health_events'])}</p>
            <p><b>Productivity Score:</b> {productivity_score:.0f}%</p>
            """
            
            # Show summary dialog
            msg = QMessageBox()
            msg.setWindowTitle("Session Summary")
            msg.setTextFormat(Qt.RichText)
            msg.setText(summary)
            
            # Add export button
            export_btn = msg.addButton("Export Session Data", QMessageBox.ActionRole)
            export_btn.clicked.connect(lambda: self.export_session_data())
            
            # Add close button
            close_btn = msg.addButton("Close", QMessageBox.AcceptRole)
            
            # Save session data
            self.save_session_data()
            
            # Show the dialog
            msg.exec_()
            
            # Reset for next session
            self.reset_to_task_selection()
            
        except Exception as e:
            logging.error(f"Error ending session: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while ending the session:\n{str(e)}",
                QMessageBox.Ok
            )
    
    def save_session_data(self):
        """Save session data to a JSON file."""
        data_dir = os.path.join(os.path.expanduser("~"), ".focusflow_sessions")
        os.makedirs(data_dir, exist_ok=True)
        
        filename = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(data_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(self.session_data, f, indent=2)
        
        logging.info(f"Session data saved to {filepath}")
    
    def close_application(self):
        """Handle application shutdown."""
        if hasattr(self, 'timer'):
            self.timer.stop()
        if hasattr(self, 'monitor_timer'):
            self.monitor_timer.stop()
        if hasattr(self, 'health_timer'):
            self.health_timer.stop()
        
        self.tray_icon.hide()
        QApplication.quit()
    
    def closeEvent(self, event):
        """Handle window close event."""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "FocusFlow",
            "The application is still running in the system tray.",
            QSystemTrayIcon.Information,
            2000
        )

    # New methods for navigation
    def task_selected(self, task):
        """Handle task selection from the task page."""
        self.session_data['purpose'] = task
        self.stacked_widget.setCurrentIndex(1)  # Show app selection page
    
    def show_task_selection(self):
        """Show the task selection page."""
        self.stacked_widget.setCurrentIndex(0)
    
    def start_session(self, allowed_apps):
        """Start a new focus session with the given allowed apps."""
        self.session_data = {
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'purpose': self.session_data.get('purpose', ''),
            'allowed_apps': allowed_apps,
            'blocked_events': [],
            'health_events': [],
            'distractions': 0,
            'focus_time': 0
        }
        
        # Update UI
        self.task_display.setText(f"Task: {self.session_data['purpose']}")
        self.distractions_label.setText("Distractions Blocked: 0")
        self.focus_time_label.setText("Focus Time: 00:00:00")
        self.productivity_label.setText("Productivity Score: 100%")
        
        # Start timers
        self.session_start_time = datetime.now()
        self.session_timer.start(1000)  # Update every second
        
        # Start monitoring
        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self.check_active_window)
        self.monitor_timer.start(1000)  # Check every second
        
        # Start health reminders
        self.health_timer = QTimer(self)
        self.health_timer.timeout.connect(self.check_health_reminders)
        self.health_timer.start(30000)  # Check every 30 seconds
        
        # Show session page
        self.stacked_widget.setCurrentIndex(2)  # Show session page
        
        # Log session start
        logging.info(f"Started focus session: {self.session_data['purpose']}")
    
    def reset_to_task_selection(self):
        """Reset the UI to the task selection page."""
        # Stop all timers
        if hasattr(self, 'session_timer') and self.session_timer.isActive():
            self.session_timer.stop()
        if hasattr(self, 'monitor_timer') and self.monitor_timer.isActive():
            self.monitor_timer.stop()
        if hasattr(self, 'health_timer') and self.health_timer.isActive():
            self.health_timer.stop()
        
        # Close overlay if open
        if self.overlay:
            self.overlay.close()
            self.overlay = None
        
        # Reset session data
        self.session_data = {
            'start_time': None,
            'end_time': None,
            'purpose': '',
            'allowed_apps': [],
            'blocked_events': [],
            'health_events': [],
            'distractions': 0,
            'focus_time': 0
        }
        
        # Reset UI
        self.task_display.setText("Task: ")
        self.timer_label.setText("00:00:00")
        
        # Show task selection page
        self.stacked_widget.setCurrentIndex(0)
    
    def update_timer(self):
        """Update the timer display and session data."""
        if not hasattr(self, 'session_start_time'):
            self.session_start_time = datetime.now()
            
        current_time = datetime.now()
        elapsed = current_time - self.session_start_time
        self.session_data['focus_time'] = int(elapsed.total_seconds())
        
        # Update timer display
        hours, remainder = divmod(elapsed.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.timer_label.setText(time_str)
        
        # Update focus time label if it exists
        if hasattr(self, 'focus_time_label'):
            self.focus_time_label.setText(f"Focus Time: {time_str}")
        
        # Update productivity score if the label exists
        if hasattr(self, 'productivity_label'):
            distraction_penalty = min(self.session_data.get('distractions', 0) * 5, 50)
            productivity_score = max(0, 100 - distraction_penalty)
            self.productivity_label.setText(f"Productivity Score: {productivity_score:.0f}%")
    
    def export_session_data(self):
        """Export session data to a JSON file."""
        try:
            # Create data directory if it doesn't exist
            data_dir = os.path.join(
                QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation),
                "ZenFlowSessions"
            )
            os.makedirs(data_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ZenFlow_Session_{timestamp}.json"
            filepath = os.path.join(data_dir, filename)
            
            # Prepare data for export
            export_data = {
                'session': self.session_data,
                'health_config': self.health_config,
                'export_timestamp': datetime.now().isoformat()
            }
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            # Show success message
            QMessageBox.information(
                self,
                "Export Successful",
                f"Session data has been exported to:\n{filepath}",
                QMessageBox.Ok
            )
            
            return filepath
            
        except Exception as e:
            logging.error(f"Error exporting session data: {e}")
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export session data:\n{str(e)}",
                QMessageBox.Ok
            )
            return None
    
    def load_settings(self):
        """Load application settings."""
        # Load window geometry if it exists
        geometry = self.settings.value("window_geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        
        # Load health reminder settings
        for reminder_type in self.health_config.keys():
            enabled = self.settings.value(f"reminder_{reminder_type}", True, type=bool)
            if enabled is not None:  # Only update if the setting exists
                self.health_config[reminder_type]['enabled'] = enabled
    
    def save_settings(self):
        """Save application settings."""
        # Save window geometry
        self.settings.setValue("window_geometry", self.saveGeometry())
        
        # Save health reminder settings
        for reminder_type, config in self.health_config.items():
            self.settings.setValue(f"reminder_{reminder_type}", config['enabled'])
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.save_settings()
        
        if hasattr(self, 'session_timer') and self.session_timer.isActive():
            # If session is active, minimize to system tray instead of closing
            event.ignore()
            self.hide()
            
            self.tray_icon.showMessage(
                "ZenFlow",
                "ZenFlow is still running in the system tray.",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            # No active session, close the application
            event.accept()


def main():
    # Set up logging
    log_dir = os.path.join(os.path.expanduser("~"), ".zenflow")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "zenflow.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("ZenFlow")
    app.setApplicationDisplayName("ZenFlow - Focus & Productivity")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show the main window
    window = ProductivityTracker()
    
    # Register cleanup function
    atexit.register(window.save_settings)
    
    # Show the window
    window.show()
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
