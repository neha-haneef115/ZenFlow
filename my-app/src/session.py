""
Session management for FocusFlow.
Handles focus sessions, allowed/blocked apps, and session data.
"""
import json
import time
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal

class SessionManager(QObject):
    """Manages focus sessions and application blocking."""
    
    session_started = pyqtSignal()
    session_ended = pyqtSignal(dict)  # session_data
    app_blocked = pyqtSignal(str)     # app_name
    app_allowed = pyqtSignal(str)     # app_name
    
    def __init__(self, config, logger):
        super().__init__()
        self.config = config
        self.logger = logger
        self.current_session = None
        self.allowed_apps = set(config.get("app_blocking", {}).get("allowed_apps", []))
        self.blocked_apps = set(config.get("app_blocking", {}).get("blocked_apps", []))
        self.session_data = {
            "start_time": None,
            "end_time": None,
            "purpose": "",
            "allowed_apps": [],
            "blocked_events": [],
            "health_events": []
        }
    
    def start_session(self, purpose):
        """Start a new focus session."""
        self.session_data = {
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "purpose": purpose,
            "allowed_apps": list(self.allowed_apps),
            "blocked_events": [],
            "health_events": []
        }
        self.current_session = {
            "start_time": time.time(),
            "purpose": purpose
        }
        self.session_started.emit()
        self.logger.log_event("session_started", {"purpose": purpose})
    
    def end_session(self):
        """End the current focus session."""
        if not self.current_session:
            return
            
        self.session_data["end_time"] = datetime.now().isoformat()
        session_duration = time.time() - self.current_session["start_time"]
        
        # Log session data
        self.logger.log_event("session_ended", {
            "purpose": self.current_session["purpose"],
            "duration_seconds": session_duration,
            "blocked_events": len(self.session_data["blocked_events"]),
            "health_events": len(self.session_data["health_events"])
        })
        
        # Save session data
        self.save_session_data()
        
        # Emit signal with session data
        self.session_ended.emit(self.session_data)
        
        # Reset current session
        self.current_session = None
    
    def allow_app(self, app_name):
        """Add an application to the allowed list."""
        if app_name not in self.allowed_apps:
            self.allowed_apps.add(app_name)
            self.config.setdefault("app_blocking", {})
            self.config["app_blocking"].setdefault("allowed_apps", [])
            if app_name not in self.config["app_blocking"]["allowed_apps"]:
                self.config["app_blocking"]["allowed_apps"].append(app_name)
            self.app_allowed.emit(app_name)
    
    def block_app(self, app_name):
        """Add an application to the blocked list."""
        if app_name not in self.blocked_apps:
            self.blocked_apps.add(app_name)
            self.config.setdefault("app_blocking", {})
            self.config["app_blocking"].setdefault("blocked_apps", [])
            if app_name not in self.config["app_blocking"]["blocked_apps"]:
                self.config["app_blocking"]["blocked_apps"].append(app_name)
    
    def is_app_allowed(self, app_name):
        """Check if an application is allowed."""
        # If app is in blocked list, it's not allowed
        if app_name in self.blocked_apps:
            return False
        
        # If app is in allowed list, it's allowed
        if app_name in self.allowed_apps:
            return True
            
        # If we're in a session and the app isn't explicitly allowed, it's blocked
        if self.current_session is not None:
            return False
            
        # Default to allowing the app if no session is active
        return True
    
    def log_blocked_app(self, app_name):
        """Log a blocked app event."""
        if self.current_session:
            self.session_data["blocked_events"].append({
                "time": datetime.now().isoformat(),
                "app": app_name
            })
    
    def log_health_event(self, event_type, data=None):
        """Log a health-related event."""
        if self.current_session:
            event = {
                "time": datetime.now().isoformat(),
                "type": event_type
            }
            if data:
                event.update(data)
            self.session_data["health_events"].append(event)
    
    def save_session_data(self):
        """Save session data to a file."""
        if not self.session_data.get("start_time"):
            return
            
        try:
            # Create sessions directory if it doesn't exist
            sessions_dir = os.path.join(os.path.expanduser("~"), ".focusflow", "sessions")
            os.makedirs(sessions_dir, exist_ok=True)
            
            # Generate filename from session start time
            start_time = self.session_data["start_time"].replace(":", "-").replace(".", "-")
            filename = f"session_{start_time}.json"
            filepath = os.path.join(sessions_dir, filename)
            
            # Save session data
            with open(filepath, 'w') as f:
                json.dump(self.session_data, f, indent=2)
                
        except Exception as e:
            self.logger.log_error(f"Failed to save session data: {str(e)}")
    
    def get_session_stats(self):
        """Get statistics about the current session."""
        if not self.current_session:
            return None
            
        duration = int(time.time() - self.current_session["start_time"])
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return {
            "purpose": self.current_session["purpose"],
            "duration": {
                "total_seconds": duration,
                "hours": hours,
                "minutes": minutes,
                "seconds": seconds,
                "formatted": f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            },
            "blocked_events": len(self.session_data["blocked_events"]),
            "health_events": len(self.session_data["health_events"])
        }
