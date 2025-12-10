import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QStackedWidget, QMessageBox,
                            QSystemTrayIcon, QMenu, QAction, QStyle)
from PyQt5.QtCore import Qt, QTimer, QSettings, QStandardPaths
from PyQt5.QtGui import QIcon

# Import screens
from .splash_screen import SplashScreen
from .task_selection import TaskSelectionScreen
from .app_selection import AppSelectionScreen
from .main_window import MainWindow  # We'll create this next
from .session import FocusSession  # We'll create this next

class ZenFlowApp(QMainWindow):
    """Main application window for ZenFlow"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize settings
        self.settings = QSettings("ZenFlow", "ZenFlow")
        
        # Set up the UI
        self.init_ui()
        
        # Initialize session data
        self.current_session = None
        
        # Show the splash screen first
        self.show_splash()
    
    def init_ui(self):
        """Initialize the main application UI"""
        # Main window properties
        self.setWindowTitle("ZenFlow")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
        """)
        
        # Create stacked widget to manage screens
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create screens (but don't show them yet)
        self.splash_screen = SplashScreen()
        self.task_selection = TaskSelectionScreen()
        
        # Add screens to stacked widget
        self.stacked_widget.addWidget(self.splash_screen)
        self.stacked_widget.addWidget(self.task_selection)
        
        # Connect signals
        self.splash_screen.finished.connect(self.show_task_selection)
        self.task_selection.task_selected.connect(self.on_task_selected)
        
        # Set up system tray
        self.setup_system_tray()
    
    def setup_system_tray(self):
        """Set up the system tray icon and menu"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))  # Placeholder icon
        
        # Create tray menu
        tray_menu = QMenu()
        
        self.show_action = QAction("Show ZenFlow", self)
        self.show_action.triggered.connect(self.showNormal)
        
        self.pause_action = QAction("Pause Monitoring", self)
        self.pause_action.setCheckable(True)
        self.pause_action.triggered.connect(self.toggle_pause_monitoring)
        
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(QApplication.quit)
        
        tray_menu.addAction(self.show_action)
        tray_menu.addAction(self.pause_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
    
    def tray_icon_activated(self, reason):
        """Handle system tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.showNormal()
            self.activateWindow()
    
    def toggle_pause_monitoring(self, paused):
        """Pause or resume monitoring"""
        if hasattr(self, 'main_window'):
            self.main_window.set_monitoring_paused(paused)
    
    def show_splash(self):
        """Show the splash screen"""
        self.stacked_widget.setCurrentWidget(self.splash_screen)
        self.show()
    
    def show_task_selection(self):
        """Show the task selection screen"""
        self.stacked_widget.setCurrentWidget(self.task_selection)
        self.show()
    
    def on_task_selected(self, task_name):
        """Handle task selection"""
        # Create app selection screen for this task if it doesn't exist
        if not hasattr(self, 'app_selection'):
            self.app_selection = AppSelectionScreen(task_name)
            self.app_selection.session_started.connect(self.on_session_started)
            self.stacked_widget.addWidget(self.app_selection)
        else:
            self.app_selection.task_name = task_name
            self.app_selection.load_app_suggestions()
        
        # Show the app selection screen
        self.stacked_widget.setCurrentWidget(self.app_selection)
    
    def on_session_started(self, app_states):
        """Start a new focus session with the selected apps"""
        # Create a new session
        self.current_session = FocusSession(app_states)
        
        # Create main window if it doesn't exist
        if not hasattr(self, 'main_window'):
            self.main_window = MainWindow(self.current_session)
            self.main_window.session_ended.connect(self.on_session_ended)
            self.stacked_widget.addWidget(self.main_window)
        else:
            self.main_window.set_session(self.current_session)
        
        # Show the main window
        self.stacked_widget.setCurrentWidget(self.main_window)
        
        # Start the session
        self.current_session.start()
        
        # Minimize to system tray
        self.hide()
    
    def on_session_ended(self):
        """Handle session end"""
        # Show a notification
        if hasattr(self, 'tray_icon'):
            self.tray_icon.showMessage(
                "ZenFlow Session Complete",
                "Your focus session has ended. Great job!",
                QSystemTrayIcon.Information,
                3000
            )
        
        # Show the task selection screen again
        self.show_task_selection()
    
    def closeEvent(self, event):
        """Handle application close"""
        # Don't close, just minimize to tray
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
            
            # Show a message to inform the user
            self.tray_icon.showMessage(
                "ZenFlow is still running",
                "ZenFlow will continue to run in the background. Click here to show the window.",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            # If there's no system tray, confirm before quitting
            reply = QMessageBox.question(
                self, 'Exit ZenFlow',
                'Are you sure you want to exit? This will end your current session.',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Clean up and quit
                if hasattr(self, 'current_session') and self.current_session:
                    self.current_session.end()
                event.accept()
            else:
                event.ignore()


def main():
    """Main entry point for the application"""
    # Set up the application
    app = QApplication(sys.argv)
    app.setApplicationName("ZenFlow")
    app.setApplicationDisplayName("ZenFlow")
    app.setQuitOnLastWindowClosed(False)  # Keep running in the background
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show the main window
    window = ZenFlowApp()
    
    # Run the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
