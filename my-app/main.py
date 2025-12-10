import sys
import os
import json
import logging
import time
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, 
                            QPushButton, QInputDialog, QMessageBox, QSystemTrayIcon, 
                            QMenu, QAction, QGroupBox, QCheckBox, QListWidget, QHBoxLayout)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon

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

class ProductivityTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FocusFlow - Productivity & Health Tracker")
        self.setMinimumSize(800, 600)
        
        # Initialize app data
        self.session_data = {
            'start_time': None,
            'end_time': None,
            'purpose': '',
            'allowed_apps': [],
            'blocked_events': [],
            'health_events': []
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
            "FocusFlow - Work Purpose",
            "What are you working on today?"
        )
        
        if ok and purpose:
            self.session_data['purpose'] = purpose
            self.session_data['start_time'] = datetime.now().isoformat()
            self.session_label.setText(f"Focusing on: {purpose}")
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
        self.start_time = datetime.now()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)  # Update every second
    
    def update_timer(self):
        """Update the timer display."""
        elapsed = datetime.now() - self.start_time
        self.timer_label.setText(str(elapsed).split('.')[0])  # Remove microseconds
    
    def check_active_window(self):
        """Check the currently active window and handle app blocking."""
        try:
            if PLATFORM == 'windows':
                window = win32gui.GetForegroundWindow()
                _, pid = win32process.GetWindowThreadProcessId(window)
                process = psutil.Process(pid)
                app_name = process.name()
            elif PLATFORM == 'darwin':
                app_name = NSWorkspace.sharedWorkspace().activeApplication().get('NSApplicationName', '')
            else:  # Linux
                result = subprocess.run(['xdotool', 'getwindowfocus', 'getwindowname'], 
                                      capture_output=True, text=True)
                app_name = result.stdout.strip()
            
            # Check if app is allowed
            if app_name and app_name not in self.session_data['allowed_apps']:
                self.handle_blocked_app(app_name)
                
        except Exception as e:
            logging.error(f"Error checking active window: {e}")
    
    def handle_blocked_app(self, app_name):
        """Handle when a blocked app is detected."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Blocked Application")
        msg.setText(f"You opened {app_name} which is not in your allowed apps.")
        msg.setInformativeText("What are you doing with this app?")
        
        work_btn = msg.addButton("Work-related (Allow)", QMessageBox.AcceptRole)
        distr_btn = msg.addButton("Distraction (Block)", QMessageBox.RejectRole)
        
        msg.exec_()
        
        if msg.clickedButton() == work_btn:
            self.session_data['allowed_apps'].append(app_name)
            self.update_apps_list()
            logging.info(f"Added to allowed apps: {app_name}")
        else:
            logging.info(f"Blocked app: {app_name}")
            # On Windows, we can try to minimize the window
            if PLATFORM == 'windows':
                try:
                    window = win32gui.GetForegroundWindow()
                    win32gui.ShowWindow(window, 6)  # Minimize window
                except:
                    pass
    
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
        
        # Health status
        health_widget = QGroupBox("Health Tracking")
        health_layout = QVBoxLayout()
        
        # Create toggle buttons for each health reminder
        self.health_buttons = {}
        for reminder_type, config in self.health_config.items():
            btn = QCheckBox(f"{config['title']} (every {config['interval']//60} min)")
            btn.setChecked(config['enabled'])
            btn.toggled.connect(lambda checked, rt=reminder_type: self.toggle_reminder(rt, checked))
            health_layout.addWidget(btn)
            self.health_buttons[reminder_type] = btn
        
        health_widget.setLayout(health_layout)
        
        # Allowed apps
        apps_widget = QGroupBox("Allowed Applications")
        apps_layout = QVBoxLayout()
        self.apps_list = QListWidget()
        apps_layout.addWidget(self.apps_list)
        
        # Add/Remove app buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Application")
        remove_btn = QPushButton("Remove Selected")
        add_btn.clicked.connect(self.add_allowed_app)
        remove_btn.clicked.connect(self.remove_allowed_app)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        apps_layout.addLayout(btn_layout)
        apps_widget.setLayout(apps_layout)
        
        # End session button
        self.end_button = QPushButton("End Focus Session")
        self.end_button.clicked.connect(self.end_session)
        
        # Add widgets to main layout
        layout.addWidget(self.session_label)
        layout.addWidget(self.timer_label)
        layout.addWidget(health_widget)
        layout.addWidget(apps_widget, 1)  # Allow the apps list to expand
        layout.addWidget(self.end_button)
    
    def update_apps_list(self):
        """Update the displayed list of allowed apps."""
        self.apps_list.clear()
        if not self.session_data['allowed_apps']:
            self.apps_list.addItem("No applications allowed")
        else:
            for app in self.session_data['allowed_apps']:
                self.apps_list.addItem(app)
    
    def toggle_reminder(self, reminder_type, enabled):
        """Enable or disable a specific health reminder."""
        if reminder_type in self.health_config:
            self.health_config[reminder_type]['enabled'] = enabled
            logging.info(f"{reminder_type} reminder {'enabled' if enabled else 'disabled'}")
    
    def add_allowed_app(self):
        """Add an application to the allowed list."""
        app_name, ok = QInputDialog.getText(
            self, 
            "Add Allowed Application",
            "Enter application name (e.g., chrome.exe, code.exe):"
        )
        
        if ok and app_name and app_name not in self.session_data['allowed_apps']:
            self.session_data['allowed_apps'].append(app_name)
            self.update_apps_list()
            logging.info(f"Added to allowed apps: {app_name}")
    
    def remove_allowed_app(self):
        """Remove selected application from the allowed list."""
        current_item = self.apps_list.currentItem()
        if current_item and current_item.text() != "No applications allowed":
            app_name = current_item.text()
            self.session_data['allowed_apps'].remove(app_name)
            self.update_apps_list()
            logging.info(f"Removed from allowed apps: {app_name}")
    
    def end_session(self):
        """End the current focus session and show summary."""
        self.session_data['end_time'] = datetime.now().isoformat()
        self.timer.stop()
        self.monitor_timer.stop()
        self.health_timer.stop()
        
        # Save session data
        self.save_session_data()
        
        # Show summary
        duration = (datetime.fromisoformat(self.session_data['end_time']) - 
                   datetime.fromisoformat(self.session_data['start_time']))
        
        summary = (
            f"Session Summary:\n"
            f"Purpose: {self.session_data['purpose']}\n"
            f"Duration: {str(duration).split('.')[0]}\n"
            f"Allowed Apps: {len(self.session_data['allowed_apps'])}\n"
            f"Blocked Apps: {len(self.session_data['blocked_events'])}\n"
            f"Health Reminders: {len(self.session_data['health_events'])}"
        )
        
        QMessageBox.information(
            self,
            "Session Complete",
            summary,
            QMessageBox.Ok
        )
        
        # Reset for next session
        self.close()
    
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

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show the main window
    window = ProductivityTracker()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
