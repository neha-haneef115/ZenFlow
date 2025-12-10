import os
import json
import logging
from pathlib import Path

class AppConfig:
    def __init__(self, config_file=None):
        """Initialize the application configuration.
        
        Args:
            config_file (str, optional): Path to the configuration file. 
                If not provided, a default location will be used.
        """
        self.logger = logging.getLogger(__name__)
        
        # Set default configuration values
        self.config = {
            'app_name': 'ZenFlow',
            'version': '1.0.0',
            'settings': {
                'theme': 'light',
                'auto_start': False,
                'notifications': True,
                'blocked_apps': [],
                'allowed_apps': [],
                'work_session_minutes': 25,
                'short_break_minutes': 5,
                'long_break_minutes': 15,
                'sessions_before_long_break': 4
            },
            'user_preferences': {
                'start_minimized': False,
                'minimize_to_tray': True,
                'show_notifications': True,
                'enable_sounds': True
            }
        }
        
        # Set the default config file path
        if config_file is None:
            self.config_dir = os.path.join(os.path.expanduser('~'), '.zenflow')
            os.makedirs(self.config_dir, exist_ok=True)
            self.config_file = os.path.join(self.config_dir, 'config.json')
        else:
            self.config_file = os.path.abspath(config_file)
            self.config_dir = os.path.dirname(self.config_file)
        
        # Load existing config if it exists
        self.load()
    
    def load(self):
        """Load configuration from file if it exists."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Update the default config with loaded values
                    self._update_nested_dict(self.config, loaded_config)
                self.logger.info(f"Configuration loaded from {self.config_file}")
            else:
                self.logger.info("No configuration file found, using defaults")
                self.save()  # Save default config
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
    
    def save(self):
        """Save the current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            self.logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False
    
    def get(self, key, default=None):
        """Get a configuration value by dot notation key.
        
        Example: config.get('settings.theme')
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key, value):
        """Set a configuration value by dot notation key.
        
        Example: config.set('settings.theme', 'dark')
        """
        keys = key.split('.')
        current = self.config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
        self.save()
    
    def _update_nested_dict(self, original, updates):
        """Recursively update a nested dictionary."""
        for key, value in updates.items():
            if key in original and isinstance(original[key], dict) and isinstance(value, dict):
                self._update_nested_dict(original[key], value)
            else:
                original[key] = value
