""
Main application module for FocusFlow.
Handles application initialization, main window, and high-level functionality.
"""
import sys
import json
import os
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon

from .session import SessionManager
from .health_tracker import HealthTracker
from .window_monitor import WindowMonitor
from .alerts import AlertManager
from .logger import AppLogger

class FocusFlowApp(QMainWindow):
    def __init__(self, config_path):
        super().__init__()
        self.config_path = config_path
        self.config = self.load_config()
        
        # Initialize core components
        self.logger = AppLogger()
        self.session_manager = SessionManager(self.config, self.logger)
        self.health_tracker = HealthTracker(self.config, self.logger)
        self.window_monitor = WindowMonitor(self.config, self.logger)
        self.alert_manager = AlertManager(self.config, self.logger)
        
        self.setup_ui()
        self.setup_system_tray()
        self.setup_timers()
        
        # Connect signals
        self.setup_connections()
        
    def load_config(self):
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return default config if file doesn't exist or is invalid
            return self.get_default_config()
    
    def get_default_config(self):
        """Return default configuration."""
        return {
            "app": {"version": "1.0.0"},
            "focus": {"session_duration": 25},
            "health": {
                "eye_strain_interval": 20,
                "posture_reminder_interval": 30,
                "hydration_reminder_interval": 60,
                "break_reminder_interval": 25
            }
        }
    
    def setup_ui(self):
        """Initialize the main application UI."""
        self.setWindowTitle("FocusFlow - Productivity & Health Tracker")
        self.setMinimumSize(800, 600)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Add UI components
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Add more UI components here
        
    def setup_system_tray(self):
        """Initialize system tray icon and menu."""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Set icon (you'll need to provide an icon file)
        icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "app_icon.png")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        
        # Create menu
        tray_menu = QMenu()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def setup_timers(self):
        """Initialize application timers."""
        # Health check timer (every 30 seconds)
        self.health_timer = QTimer(self)
        self.health_timer.timeout.connect(self.check_health)
        self.health_timer.start(30000)  # 30 seconds
        
        # Window monitoring timer (every 2 seconds)
        self.window_timer = QTimer(self)
        self.window_timer.timeout.connect(self.monitor_windows)
        self.window_timer.start(2000)  # 2 seconds
    
    def setup_connections(self):
        """Connect signals between components."""
        self.health_tracker.reminder_triggered.connect(self.handle_reminder)
        self.window_monitor.blocked_app_detected.connect(self.handle_blocked_app)
    
    def check_health(self):
        """Check and trigger health-related reminders."""
        self.health_tracker.check_reminders()
    
    def monitor_windows(self):
        """Monitor active windows for blocked applications."""
        self.window_monitor.check_active_window()
    
    def handle_reminder(self, reminder_type, message):
        """Handle health reminder events."""
        self.alert_manager.show_reminder(reminder_type, message)
        self.logger.log_event("health_reminder", {"type": reminder_type, "message": message})
    
    def handle_blocked_app(self, app_name):
        """Handle detection of a blocked application."""
        response = self.alert_manager.show_blocked_app_alert(app_name)
        if response == "allow":
            self.session_manager.allow_app(app_name)
        self.logger.log_event("app_blocked", {"app": app_name, "action": response})
    
    def closeEvent(self, event):
        """Handle application close event."""
        if self.config.get("appearance", {}).get("close_to_tray", True):
            event.ignore()
            self.hide()
            return
        
        # Save session and cleanup
        self.session_manager.end_session()
        self.health_tracker.cleanup()
        self.logger.cleanup()
        
        # Stop timers
        self.health_timer.stop()
        self.window_timer.stop()
        
        event.accept()

def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    
    # Ensure config directory exists
    config_dir = os.path.join(os.path.expanduser("~"), ".focusflow")
    os.makedirs(config_dir, exist_ok=True)
    
    # Initialize and show main window
    config_path = os.path.join(config_dir, "config.json")
    window = FocusFlowApp(config_path)
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
