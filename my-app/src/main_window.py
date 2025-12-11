from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QScrollArea,
    QListWidget,
    QListWidgetItem,
    QCheckBox,
    QFrame,
    QSpinBox,
    QLineEdit,
)
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtGui import QPixmap, QIcon
import os
import sys
import json
from datetime import datetime

# Desktop app detection imports
from queue import Queue, Empty
import threading
import time

import psutil
import win32gui
import win32process

from web_watcher import WebWatcher
import theme

# Import separated screens
from screens.splash_screen import SplashScreen
from screens.intent_screen import IntentScreen
from screens.app_setup_screen import AppSetupScreen
from screens.focus_dashboard_screen import FocusDashboardScreen
from screens.settings_screen import SettingsScreen
from screens.session_summary_screen import SessionSummaryScreen

DATA_FILE = os.path.join(os.path.dirname(__file__), "zenflow_data.json")


def load_state():
    if not os.path.exists(DATA_FILE):
        return {
            "selectedCategories": [],
            "sessionRules": {},
            "activeSessionData": {},
            "sessionHistory": [],
            "userPreferences": {
                "defaultSessionMinutes": 50,
                "postureTips": True,
                "eyeStrainReminders": True,
                "presets": {},
            },
        }
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "selectedCategories": [],
            "sessionRules": {},
            "activeSessionData": {},
            "sessionHistory": [],
            "userPreferences": {
                "defaultSessionMinutes": 50,
                "postureTips": True,
                "eyeStrainReminders": True,
                "presets": {},
            },
        }


def save_state(state):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


class MainWindow(QMainWindow):
    def __init__(self, config=None):
        super().__init__()
        self.config = config
        self.state = load_state()
        self.setWindowTitle("ZenFlow")
        self.setMinimumSize(500, 600)
        self.setMaximumSize(600, 700)
        
        # Initialize screens
        self.splash_screen = None
        self.intent_screen = None
        self.app_setup_screen = None
        self.dashboard_screen = None
        self.settings_screen = None
        self.session_summary_screen = None
        self.blocked_overlay = None
        
        # Desktop app blocking session state
        self.allowed_exes_session = set()
        self.blocked_exes_session = set()
        self.current_blocked_exe = None
        
        # Website blocking session state (per run, not persisted)
        self.allowed_domains_session = set()
        self.blocked_domains_session = set()
        self.current_blocked_domain = None
        
        self._setup_ui()
        self._setup_monitoring()
        self.show_splash()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.stacked_widget = QStackedWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.stacked_widget)

    def _setup_monitoring(self):
        # Queue and watcher for browser tab URLs (WebSocket from extension)
        self.web_event_queue = Queue()
        self.web_watcher = WebWatcher(self.web_event_queue)
        self.web_watcher.start()

        self.web_event_timer = QTimer(self)
        self.web_event_timer.timeout.connect(self._process_web_events)
        self.web_event_timer.start(1000)
        
        # Desktop app monitoring
        self.desktop_timer = QTimer(self)
        self.desktop_timer.timeout.connect(self._check_active_window)
        self.desktop_timer.start(500)  # Check every 500ms

    def save_state(self, state):
        save_state(state)
        self.state = state

    def show_splash(self):
        self.splash_screen = SplashScreen(self)
        self._add_and_show(self.splash_screen)

    def show_intent_screen(self):
        if not self.intent_screen:
            self.intent_screen = IntentScreen(self, self.state)
        self._add_and_show(self.intent_screen)

    def show_app_setup_screen(self):
        if not self.app_setup_screen:
            self.app_setup_screen = AppSetupScreen(self, self.state)
        self._add_and_show(self.app_setup_screen)

    def show_dashboard(self):
        if not self.dashboard_screen:
            self.dashboard_screen = FocusDashboardScreen(self, self.state)
        self._add_and_show(self.dashboard_screen)

    def show_settings(self):
        if not self.settings_screen:
            self.settings_screen = SettingsScreen(self, self.state)
        self._add_and_show(self.settings_screen)

    def show_session_summary(self):
        if not self.session_summary_screen:
            self.session_summary_screen = SessionSummaryScreen(self, self.state)
        self._add_and_show(self.session_summary_screen)

    def _add_and_show(self, screen):
        # Remove existing screen if it exists
        existing_index = self.stacked_widget.indexOf(screen)
        if existing_index == -1:
            self.stacked_widget.addWidget(screen)
        self.stacked_widget.setCurrentWidget(screen)

    def show_blocked_overlay(self, app_name="Blocked app"):
        from screens.blocked_overlay_screen import BlockedOverlayScreen
        self.blocked_overlay = BlockedOverlayScreen(self, app_name)
        self.blocked_overlay.showFullScreen()
        if self.dashboard_screen is not None:
            self.dashboard_screen.record_distraction(app_name)

    def hide_blocked_overlay(self):
        if self.blocked_overlay is not None:
            self.blocked_overlay.hide()
            self.blocked_overlay.deleteLater()
            self.blocked_overlay = None
        if self.dashboard_screen is not None:
            self._add_and_show(self.dashboard_screen)

    def allow_exe_for_session(self, exe_name: str):
        self.allowed_exes_session.add(exe_name.lower())

    def allow_domain_for_session(self, domain: str):
        self.allowed_domains_session.add(domain.lower())

    def _check_active_window(self):
        """Check the currently active window and show overlay if it's a blocked app or website."""
        try:
            # Get the foreground window
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # Get the process name
            process = psutil.Process(pid)
            exe_name = os.path.basename(process.exe()).lower()
            
            # Get the window title
            window_title = win32gui.GetWindowText(hwnd).lower()
            
            # Check if this is a blocked app
            rules = self.state.get("sessionRules", {})
            blocked_apps = [app.lower() for app in rules.get("blockedApps", [])]
            
            # Check if exe name contains any blocked app names
            is_blocked_app = any(blocked_app in exe_name for blocked_app in blocked_apps)
            
            # Check if window title contains any blocked website names
            is_blocked_site = any(blocked_site.lower() in window_title for blocked_site in blocked_apps)
            
            # Special handling for browsers - check window title for blocked sites
            is_browser = exe_name in ['chrome.exe', 'firefox.exe', 'msedge.exe', 'opera.exe', 'brave.exe']
            if is_browser and not is_blocked_app:
                # Check window title for blocked sites
                blocked_sites = ['instagram', 'youtube', 'facebook', 'twitter', 'tiktok', 'reddit', 'netflix', 'linkedin']
                is_blocked_site = any(site in window_title for site in blocked_sites)
            
            combined_blocked = is_blocked_app or is_blocked_site
            
            if combined_blocked and exe_name not in self.allowed_exes_session:
                if exe_name != self.current_blocked_exe:
                    self.current_blocked_exe = exe_name
                    # Show the overlay with a user-friendly name
                    if is_blocked_site:
                        # Extract the blocked site name from window title
                        friendly_name = self._extract_site_from_title(window_title)
                    else:
                        friendly_name = self._get_friendly_app_name(exe_name)
                    self.show_blocked_overlay(friendly_name)
            else:
                if self.current_blocked_exe is not None:
                    self.current_blocked_exe = None
                    self.hide_blocked_overlay()
                    
        except Exception:
            # If we can't detect the window, just continue
            pass
    
    def _extract_site_from_title(self, window_title):
        """Extract the website name from the browser window title."""
        blocked_sites = {
            'instagram': 'Instagram',
            'youtube': 'YouTube', 
            'facebook': 'Facebook',
            'twitter': 'Twitter',
            'tiktok': 'TikTok',
            'reddit': 'Reddit',
            'netflix': 'Netflix',
            'linkedin': 'LinkedIn',
            'twitch': 'Twitch',
            'discord': 'Discord',
            'spotify': 'Spotify',
        }
        
        for site_key, site_name in blocked_sites.items():
            if site_key in window_title.lower():
                return site_name
        
        # Fallback to generic browser detection
        return "Blocked Website"
    
    def _get_friendly_app_name(self, exe_name):
        """Convert exe name to a more user-friendly name."""
        app_names = {
            'chrome.exe': 'Google Chrome',
            'firefox.exe': 'Mozilla Firefox',
            'msedge.exe': 'Microsoft Edge',
            'iexplore.exe': 'Internet Explorer',
            'opera.exe': 'Opera',
            'brave.exe': 'Brave Browser',
            'code.exe': 'Visual Studio Code',
            'pycharm.exe': 'PyCharm',
            'idea64.exe': 'IntelliJ IDEA',
            'sublime_text.exe': 'Sublime Text',
            'notepad++.exe': 'Notepad++',
            'notepad.exe': 'Notepad',
            'winword.exe': 'Microsoft Word',
            'excel.exe': 'Microsoft Excel',
            'powerpnt.exe': 'Microsoft PowerPoint',
            'discord.exe': 'Discord',
            'slack.exe': 'Slack',
            'teams.exe': 'Microsoft Teams',
            'zoom.exe': 'Zoom',
            'spotify.exe': 'Spotify',
            'itunes.exe': 'iTunes',
            'vlc.exe': 'VLC Media Player',
            'youtube.exe': 'YouTube',
            'instagram.exe': 'Instagram',
            'tiktok.exe': 'TikTok',
            'twitter.exe': 'Twitter',
            'facebook.exe': 'Facebook',
            'reddit.exe': 'Reddit',
            'netflix.exe': 'Netflix',
        }
        
        # Remove .exe extension and convert to title case
        base_name = exe_name.replace('.exe', '').title()
        return app_names.get(exe_name, base_name)

    def _process_web_events(self):
        events = []
        try:
            while True:
                events.append(self.web_event_queue.get_nowait())
        except Empty:
            pass

        for ev in events:
            if ev.get("type") == "web_foreground":
                url = ev.get("url", "")
                title = ev.get("title", "")
                # Simple domain extraction
                domain = url.split("//")[-1].split("/")[0] if "://" in url else ""
                
                # Get blocked domains from session rules
                rules = self.state.get("sessionRules", {})
                blocked_domains = set(rules.get("blockedApps", []))
                
                # Decide if this URL is blocked based on blocked_domains and allowed_domains_session
                if any(d in url and d not in self.allowed_domains_session for d in blocked_domains):
                    if domain != self.current_blocked_domain:
                        self.current_blocked_domain = domain
                        self.show_blocked_overlay(domain)
                else:
                    if self.current_blocked_domain is not None:
                        self.current_blocked_domain = None
                        self.hide_blocked_overlay()

    def closeEvent(self, event):
        try:
            if hasattr(self, "web_watcher") and self.web_watcher:
                self.web_watcher.stop()
            if hasattr(self, "desktop_timer") and self.desktop_timer:
                self.desktop_timer.stop()
        except Exception:
            pass
        event.accept()


class HomeScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("ZenFlow")
        title.setStyleSheet(
            f"font-size: 32px; font-weight: 700; color: {theme.COLOR_PRIMARY};"
        )
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Focus without distraction")
        subtitle.setStyleSheet("color: #64748b; font-size: 16px;")
        subtitle.setAlignment(Qt.AlignCenter)

        start_btn = QPushButton("Start New Session")
        start_btn.setFixedHeight(44)
        start_btn.setStyleSheet(
            f"QPushButton {{background:{theme.COLOR_PRIMARY};color:white;border:none;border-radius:10px;"
            "font-size:15px;font-weight:500;}"
        )
        start_btn.clicked.connect(self._start_session)

        history_btn = QPushButton("Session History")
        history_btn.setFixedHeight(44)
        history_btn.setStyleSheet(
            "QPushButton {background:#000000;color:white;border:none;border-radius:10px;"
            "font-size:15px;font-weight:500;}"
        )
        history_btn.clicked.connect(self._show_history)

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(40)
        layout.addWidget(start_btn)
        layout.addWidget(history_btn)
        layout.addStretch()

    def _start_session(self):
        if hasattr(self.parent, "show_intent_screen"):
            self.parent.show_intent_screen()

    def _show_history(self):
        if hasattr(self.parent, "show_settings"):
            self.parent.show_settings()
