""
Health tracking functionality for FocusFlow.
Handles break reminders, eye strain prevention, hydration, and posture correction.
"""
import time
from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

class HealthTracker(QObject):
    """Manages health-related reminders and tracking."""
    
    reminder_triggered = pyqtSignal(str, str)  # reminder_type, message
    
    def __init__(self, config, logger):
        super().__init__()
        self.config = config
        self.logger = logger
        self.reminders = {}
        self.reminder_timers = {}
        self.last_reminder_time = {}
        self.initialize_reminders()
    
    def initialize_reminders(self):
        """Initialize health reminders from config."""
        health_config = self.config.get("health", {})
        
        self.reminders = {
            "eye_strain": {
                "enabled": health_config.get("eye_strain_enabled", True),
                "interval": health_config.get("eye_strain_interval", 20) * 60,  # Convert to seconds
                "message": "20-20-20 Rule: Look at something 20 feet away for 20 seconds.",
                "last_triggered": None
            },
            "posture": {
                "enabled": health_config.get("posture_enabled", True),
                "interval": health_config.get("posture_interval", 30) * 60,  # 30 minutes
                "message": "Posture check! Sit up straight and relax your shoulders.",
                "last_triggered": None
            },
            "hydration": {
                "enabled": health_config.get("hydration_enabled", True),
                "interval": health_config.get("hydration_interval", 60) * 60,  # 60 minutes
                "message": "Stay hydrated! Please drink some water.",
                "last_triggered": None
            },
            "break_reminder": {
                "enabled": health_config.get("break_enabled", True),
                "interval": health_config.get("break_interval", 25) * 60,  # 25 minutes
                "message": "Time for a short break! Stand up and stretch for a minute.",
                "last_triggered": None
            }
        }
        
        # Initialize timers for each reminder
        for reminder_type in self.reminders:
            self.setup_reminder_timer(reminder_type)
    
    def setup_reminder_timer(self, reminder_type):
        """Set up a timer for a specific reminder type."""
        if reminder_type in self.reminder_timers:
            self.reminder_timers[reminder_type].stop()
        
        reminder = self.reminders[reminder_type]
        if not reminder["enabled"]:
            return
        
        # Create a timer for this reminder
        timer = QTimer()
        timer.timeout.connect(lambda rt=reminder_type: self.check_reminder(rt))
        timer.start(reminder["interval"] * 1000)  # Convert to milliseconds
        self.reminder_timers[reminder_type] = timer
    
    def check_reminder(self, reminder_type):
        """Check if a reminder should be triggered."""
        if reminder_type not in self.reminders:
            return
            
        reminder = self.reminders[reminder_type]
        if not reminder["enabled"]:
            return
        
        # Check cooldown (don't show the same reminder more than once per interval)
        current_time = time.time()
        last_time = reminder["last_triggered"] or 0
        if current_time - last_time < reminder["interval"]:
            return
        
        # Update last triggered time
        reminder["last_triggered"] = current_time
        
        # Emit signal to show the reminder
        self.reminder_triggered.emit(reminder_type, reminder["message"])
        
        # Log the reminder
        self.logger.log_event("health_reminder", {
            "type": reminder_type,
            "message": reminder["message"]
        })
    
    def set_reminder_enabled(self, reminder_type, enabled):
        """Enable or disable a specific reminder type."""
        if reminder_type in self.reminders:
            self.reminders[reminder_type]["enabled"] = enabled
            self.setup_reminder_timer(reminder_type)
    
    def update_reminder_interval(self, reminder_type, minutes):
        """Update the interval for a specific reminder."""
        if reminder_type in self.reminders:
            self.reminders[reminder_type]["interval"] = minutes * 60
            self.setup_reminder_timer(reminder_type)
    
    def get_reminder_status(self, reminder_type):
        """Get the status of a specific reminder."""
        if reminder_type in self.reminders:
            return {
                "enabled": self.reminders[reminder_type]["enabled"],
                "interval_minutes": self.reminders[reminder_type]["interval"] // 60,
                "last_triggered": self.reminders[reminder_type]["last_triggered"]
            }
        return None
    
    def get_all_reminders_status(self):
        """Get the status of all reminders."""
        return {
            reminder_type: self.get_reminder_status(reminder_type)
            for reminder_type in self.reminders
        }
    
    def pause_all_reminders(self):
        """Pause all health reminders."""
        for reminder_type in self.reminders:
            if reminder_type in self.reminder_timers:
                self.reminder_timers[reminder_type].stop()
    
    def resume_all_reminders(self):
        """Resume all health reminders."""
        for reminder_type in self.reminders:
            if self.reminders[reminder_type]["enabled"]:
                self.setup_reminder_timer(reminder_type)
    
    def reset_reminder(self, reminder_type):
        """Reset the timer for a specific reminder."""
        if reminder_type in self.reminders:
            self.reminders[reminder_type]["last_triggered"] = None
            self.setup_reminder_timer(reminder_type)
    
    def cleanup(self):
        """Clean up resources."""
        for timer in self.reminder_timers.values():
            if timer.isActive():
                timer.stop()
        self.reminder_timers.clear()
    
    def __del__(self):
        self.cleanup()
