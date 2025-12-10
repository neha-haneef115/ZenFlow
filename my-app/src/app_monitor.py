"""
App Monitor for ZenFlow

This module handles monitoring of running applications and enforces focus session rules.
It can block distracting apps and notify the user when they try to access them.
"""
import time
import psutil
import platform
import subprocess
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from PyQt5.QtWidgets import QMessageBox

class AppMonitor(QObject):
    """Monitors and controls application usage during focus sessions."""
    
    # Signals
    app_blocked = pyqtSignal(str)  # Emitted when an app is blocked
    app_allowed = pyqtSignal(str)  # Emitted when an app is allowed
    distraction_detected = pyqtSignal(str)  # Emitted when a distraction is detected
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.running = False
        self.allowed_apps = set()
        self.blocked_apps = set()
        self.ignored_apps = set()  # Temporarily ignored apps
        self.current_app = None
        self.last_check_time = 0
        self.check_interval = 2  # seconds
        self.os_type = platform.system().lower()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_apps)
    
    def start(self):
        """Start monitoring applications."""
        if not self.running:
            self.running = True
            self.timer.start(self.check_interval * 1000)
            print("App monitoring started")
    
    def stop(self):
        """Stop monitoring applications."""
        if self.running:
            self.running = False
            self.timer.stop()
            print("App monitoring stopped")
    
    def set_allowed_apps(self, apps):
        """Set the list of allowed applications."""
        self.allowed_apps = set(apps)
        print(f"Allowed apps updated: {self.allowed_apps}")
    
    def set_blocked_apps(self, apps):
        """Set the list of blocked applications."""
        self.blocked_apps = set(apps)
        print(f"Blocked apps updated: {self.blocked_apps}")
    
    def ignore_app_once(self, app_name):
        """Temporarily ignore an app for the current session."""
        self.ignored_apps.add(app_name.lower())
        print(f"Temporarily ignoring app: {app_name}")
    
    def check_apps(self):
        """Check currently running applications and enforce rules."""
        if not self.running:
            return
            
        current_time = time.time()
        if current_time - self.last_check_time < self.check_interval:
            return
            
        self.last_check_time = current_time
        
        try:
            current_app = self._get_foreground_app()
            
            if not current_app or current_app == self.current_app:
                return
                
            self.current_app = current_app
            print(f"Current app: {current_app}")
            
            if self._should_block_app(current_app):
                self._handle_blocked_app(current_app)
                
        except Exception as e:
            print(f"Error checking apps: {e}")
    
    def _get_foreground_app(self):
        """Get the name of the currently active application."""
        try:
            if self.os_type == 'windows':
                import win32gui
                import win32process
                
                hwnd = win32gui.GetForegroundWindow()
                if not hwnd:
                    return None
                    
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                return process.name().lower()
                
            elif self.os_type == 'darwin':  # macOS
                script = '''
                tell application "System Events"
                    set frontApp to name of first application process whose frontmost is true
                    return frontApp
                end tell
                '''
                result = subprocess.run(['osascript', '-e', script], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip().lower()
                    
            elif self.os_type == 'linux':
                try:
                    result = subprocess.run(
                        ['xprop', '-root', '_NET_ACTIVE_WINDOW'], 
                        capture_output=True, text=True
                    )
                    window_id = result.stdout.split()[-1]
                    
                    if window_id != '0x0':
                        result = subprocess.run(
                            ['xprop', '-id', window_id, 'WM_CLASS'], 
                            capture_output=True, text=True
                        )
                        if result.returncode == 0:
                            parts = result.stdout.strip().split('=')
                            if len(parts) > 1:
                                return parts[1].strip(' "\n').split(',')[-1].strip('"').lower()
                except:
                    pass
                    
            return None
            
        except Exception as e:
            print(f"Error getting foreground app: {e}")
            return None
    
    def _should_block_app(self, app_name):
        """Determine if an app should be blocked."""
        if not app_name:
            return False
            
        app_name = app_name.lower()
        
        if app_name in self.ignored_apps:
            return False
            
        if app_name in self.allowed_apps:
            return False
            
        if app_name in self.blocked_apps:
            return True
            
        # Check for common distracting apps (simplified list)
        distracting_keywords = [
            'facebook', 'instagram', 'twitter', 'tiktok', 'youtube', 'netflix',
            'discord', 'slack', 'whatsapp', 'telegram', 'reddit', 'twitch',
            'steam', 'epicgames', 'battle.net', 'spotify', 'prime video',
            'disney+', 'hbo max', 'hulu', 'pinterest', 'tumblr', '9gag'
        ]
        
        return any(keyword in app_name for keyword in distracting_keywords)
    
    def _handle_blocked_app(self, app_name):
        """Handle when a blocked app is detected."""
        print(f"Blocked app detected: {app_name}")
        self.distraction_detected.emit(app_name)
        
        # Show a notification to the user
        self._show_block_notification(app_name)
        
        # Try to minimize the blocked app (platform-specific)
        self._minimize_app()
    
    def _show_block_notification(self, app_name):
        """Show a notification when an app is blocked."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Focus Interrupted")
        msg.setText(f"You're trying to open {app_name}")
        msg.setInformativeText("This app is currently blocked during your focus session.")
        
        # Add custom buttons
        allow_once = msg.addButton("Allow Once", QMessageBox.AcceptRole)
        allow_always = msg.addButton("Always Allow", QMessageBox.YesRole)
        msg.addButton("Got it", QMessageBox.RejectRole)
        
        msg.exec_()
        
        # Handle button clicks
        if msg.clickedButton() == allow_once:
            self.ignore_app_once(app_name)
            print(f"Temporarily allowed {app_name}")
        elif msg.clickedButton() == allow_always:
            self.allowed_apps.add(app_name.lower())
            print(f"Permanently allowed {app_name}")
    
    def _minimize_app(self):
        """Minimize the currently active window."""
        try:
            if self.os_type == 'windows':
                import win32gui
                import win32con
                
                hwnd = win32gui.GetForegroundWindow()
                if hwnd:
                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                    
            elif self.os_type == 'darwin':
                script = '''
                tell application "System Events"
                    set frontApp to first application process whose frontmost is true
                    set visible of frontApp to false
                end tell
                '''
                subprocess.run(['osascript', '-e', script])
                
            elif self.os_type == 'linux':
                # This is a basic implementation for Linux
                try:
                    subprocess.run(['xdotool', 'windowminimize', '$(xdotool getactivewindow)'])
                except:
                    pass
                    
        except Exception as e:
            print(f"Error minimizing app: {e}")


if __name__ == "__main__":
    # Example usage
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Create a simple config
    config = {
        'allowed_apps': ['code', 'pycharm', 'sublime_text'],
        'blocked_apps': ['chrome', 'firefox', 'discord']
    }
    
    monitor = AppMonitor(config)
    monitor.start()
    
    print("App monitor started. Press Ctrl+C to exit.")
    
    # Keep the application running
    sys.exit(app.exec_())
