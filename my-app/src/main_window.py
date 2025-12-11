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


class SplashScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self._setup_ui()
        QTimer.singleShot(1500, self._go_next)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        logo = QLabel("ZenFlow")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(
            f"font-size: 48px; font-weight: 700; color: {theme.COLOR_PRIMARY};"
        )

        glow = QFrame()
        glow.setFixedSize(260, 260)
        glow.setStyleSheet(
            "background-color: rgba(79,70,229,0.08);"
            "border-radius: 130px;"
        )

        inner = QVBoxLayout(glow)
        inner.addWidget(logo, 0, Qt.AlignCenter)

        layout.addWidget(glow)

        self.setStyleSheet(
            "background-color: #020617;"
        )

    def _go_next(self):
        if hasattr(self.parent, "show_intent_screen"):
            self.parent.show_intent_screen()


class IntentScreen(QWidget):
    def __init__(self, parent=None, state=None):
        super().__init__(parent)
        self.parent = parent
        self.state = state or load_state()
        self.selected = set(self.state.get("selectedCategories", []))
        self.buttons = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        title = QLabel("What are you working on today")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: 600; color: {theme.COLOR_TEXT_MAIN};"
        )
        subtitle = QLabel(
            "Your choice decides which apps stay allowed and which apps get blocked"
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(
            "color: #64748b; font-size: 13px;"
        )

        grid_container = QWidget()
        grid_layout = QVBoxLayout(grid_container)
        grid_layout.setSpacing(12)

        categories = [
            "Coding",
            "Designing",
            "Studying",
            "Writing",
            "Editing",
            "Other",
        ]

        tooltips = {
            "Coding": "Dev tools like VS Code, PyCharm, Terminal, GitKraken will be allowed.",
            "Designing": "Design tools like Figma, Adobe XD, Photoshop will be allowed.",
            "Studying": "Study tools like PDF Reader, Notion, Anki will be allowed.",
            "Writing": "Writing tools like Word, Notepad, Notion will be allowed.",
            "Editing": "Video editing tools like Premiere Pro, DaVinci Resolve will be allowed.",
            "Other": "Custom work that you can configure later in the next step.",
        }

        row = QHBoxLayout()
        for i, name in enumerate(categories):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setChecked(name in self.selected)
            btn.setFixedHeight(72)
            btn.setToolTip(tooltips.get(name, ""))
            btn.setStyleSheet(
                (
                    "QPushButton {background:#eff6ff;border:1px solid #dbeafe;"
                    f"border-radius:12px;font-size:15px;font-weight:500;color:{theme.COLOR_TEXT_MAIN};"
                    "}"
                    f"QPushButton:checked {{background:{theme.COLOR_PRIMARY};color:white;border-color:{theme.COLOR_PRIMARY};}}"
                )
            )

            btn.clicked.connect(lambda _=False, n=name: self._toggle_category(n))
            self.buttons[name] = btn
            row.addWidget(btn)
            if i % 2 == 1:
                grid_layout.addLayout(row)
                row = QHBoxLayout()
        if row.count() > 0:
            grid_layout.addLayout(row)

        self.continue_btn = QPushButton("Continue")
        self.continue_btn.setFixedHeight(44)
        # Enabled and disabled: white text
        self.continue_btn.setStyleSheet(
            f"QPushButton {{background:{theme.COLOR_PRIMARY};color:white;border:none;border-radius:10px;"
            "font-size:15px;font-weight:500;}"
            "QPushButton:disabled {background:#FFFFFF;color:white;border:1px solid #D1D5DB;}"
        )

        self.continue_btn.clicked.connect(self._on_continue)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(grid_container)
        layout.addStretch()
        layout.addWidget(self.continue_btn)

        self._update_continue_visibility()

    def _toggle_category(self, name):
        if name in self.selected:
            self.selected.remove(name)
        else:
            self.selected.add(name)
        self._update_continue_visibility()

    def _update_continue_visibility(self):
        has_any = bool(self.selected)
        self.continue_btn.setEnabled(has_any)
        self.continue_btn.setVisible(has_any)

    def _compute_session_rules(self):
        """Compute allowed/blocked app lists from selected categories."""
        allowed = set()
        for c in self.selected:
            for app in PRESET_APPS.get(c, []):
                allowed.add(app)

        for browser in BROWSER_APPS:
            allowed.add(browser)

        blocked = set(DISTRACTION_APPS)

        return {
            "allowedApps": sorted(allowed),
            "blockedApps": sorted(blocked),
        }

    def _on_continue(self):
        self.state["selectedCategories"] = list(self.selected)
        # Pre-compute intelligent defaults for allowed/blocked apps
        self.state["sessionRules"] = self._compute_session_rules()
        save_state(self.state)
        if hasattr(self.parent, "show_app_setup_screen"):
            self.parent.show_app_setup_screen()


PRESET_APPS = {
    "Coding": ["VS Code", "PyCharm", "Terminal", "GitKraken"],
    "Designing": ["Figma", "Adobe XD", "Photoshop"],
    "Studying": ["PDF Reader", "Notion", "Anki"],
    "Writing": ["Word", "Notepad", "Notion"],
    "Editing": ["Premiere Pro", "DaVinci Resolve"],
    "Other": [],
}

DISTRACTION_APPS = [
    "YouTube",
    "Instagram",
    "TikTok",
    "Twitter",
    "Facebook",
    "Reddit",
    "Netflix",
]

# Browsers are kept allowed by default for productivity use
BROWSER_APPS = ["Chrome", "Edge", "Firefox"]


class AppSetupScreen(QWidget):
    def __init__(self, parent=None, state=None):
        super().__init__(parent)
        self.parent = parent
        self.state = state or load_state()
        self.allowed_checks = {}
        self.blocked_checks = {}
        self._init_from_state_or_categories()
        self._setup_ui()

    def _init_from_categories(self):
        cats = self.state.get("selectedCategories", [])
        for c in cats:
            for app in PRESET_APPS.get(c, []):
                self.allowed.add(app)

    def _init_from_state_or_categories(self):
        rules = self.state.get("sessionRules")
        if rules:
            self.allowed = set(rules.get("allowedApps", []))
            self.blocked = set(rules.get("blockedApps", DISTRACTION_APPS))
        else:
            self.allowed = set()
            self.blocked = set(DISTRACTION_APPS)
            self._init_from_categories()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Your focus setup")
        title.setStyleSheet(f"font-size: 20px;font-weight:600;color:{theme.COLOR_TEXT_MAIN};")

        subtitle = QLabel("Choose which apps stay allowed")
        subtitle.setStyleSheet("color:#64748b;font-size:13px;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        scroll_layout = QVBoxLayout(container)
        scroll_layout.setSpacing(12)

        allowed_label = QLabel("Allowed apps")
        allowed_label.setStyleSheet(f"font-weight:600;color:{theme.COLOR_ALLOWED};")
        scroll_layout.addWidget(allowed_label)
        for app in sorted(self.allowed):
            cb = QCheckBox(app)
            cb.setChecked(True)
            cb.stateChanged.connect(self._on_allowed_changed)
            self.allowed_checks[app] = cb
            scroll_layout.addWidget(cb)

        blocked_label = QLabel("Distracting apps")
        blocked_label.setStyleSheet(f"font-weight:600;color:{theme.COLOR_BLOCKED};margin-top:12px;")
        scroll_layout.addWidget(blocked_label)
        for app in sorted(self.blocked):
            cb = QCheckBox(app)
            cb.setChecked(True)
            cb.stateChanged.connect(self._on_blocked_changed)
            self.blocked_checks[app] = cb
            scroll_layout.addWidget(cb)

        # Custom app inputs
        custom_allowed_row = QHBoxLayout()
        allowed_input = QLineEdit()
        allowed_input.setPlaceholderText("Add allowed app or site (e.g. Notion)")
        allowed_input.returnPressed.connect(
            lambda: self._add_custom_allowed(allowed_input.text(), scroll_layout, allowed_input)
        )
        add_allowed_btn = QPushButton("Add to allowed")
        add_allowed_btn.setFixedHeight(32)
        add_allowed_btn.setStyleSheet(
            f"QPushButton {{background:{theme.COLOR_PRIMARY};color:white;border:none;border-radius:8px;"
            "font-size:12px;font-weight:500;padding:6px 14px;}"
        )
        add_allowed_btn.clicked.connect(
            lambda: self._add_custom_allowed(allowed_input.text(), scroll_layout, allowed_input)
        )
        custom_allowed_row.addWidget(allowed_input)
        custom_allowed_row.addWidget(add_allowed_btn)
        scroll_layout.addLayout(custom_allowed_row)

        custom_blocked_row = QHBoxLayout()
        blocked_input = QLineEdit()
        blocked_input.setPlaceholderText("Add blocked app or site (e.g. Instagram)")
        blocked_input.returnPressed.connect(
            lambda: self._add_custom_blocked(blocked_input.text(), scroll_layout, blocked_input)
        )
        add_blocked_btn = QPushButton("Add to blocked")
        add_blocked_btn.setFixedHeight(32)
        add_blocked_btn.setStyleSheet(
            "QPushButton {background:#000000;color:white;border:none;border-radius:8px;"
            "font-size:12px;font-weight:500;padding:6px 14px;}"
        )
        add_blocked_btn.clicked.connect(
            lambda: self._add_custom_blocked(blocked_input.text(), scroll_layout, blocked_input)
        )
        custom_blocked_row.addWidget(blocked_input)
        custom_blocked_row.addWidget(add_blocked_btn)
        scroll_layout.addLayout(custom_blocked_row)

        scroll_layout.addStretch()
        scroll.setWidget(container)

        start_btn = QPushButton("Start Session")
        start_btn.setFixedHeight(44)
        start_btn.setStyleSheet(
            f"QPushButton {{background:{theme.COLOR_PRIMARY};color:white;border:none;border-radius:10px;"
            "font-size:15px;font-weight:500;}"
        )
        start_btn.clicked.connect(self._on_start_session)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(scroll, 1)
        layout.addWidget(start_btn)

    def _on_allowed_changed(self, _state):
        self.allowed = {name for name, cb in self.allowed_checks.items() if cb.isChecked()}

    def _on_blocked_changed(self, _state):
        self.blocked = {name for name, cb in self.blocked_checks.items() if cb.isChecked()}

    def _on_start_session(self):
        rules = {
            "allowedApps": sorted(self.allowed),
            "blockedApps": sorted(self.blocked),
        }
        self.state["sessionRules"] = rules
        self.state["activeSessionData"] = {
            "startTime": datetime.now().isoformat(),
            "distractionAttempts": 0,
        }
        save_state(self.state)
        if hasattr(self.parent, "show_dashboard_screen"):
            self.parent.show_dashboard_screen()

    def _add_custom_allowed(self, name, scroll_layout, line_edit):
        text = (name or "").strip()
        if not text:
            return
        if text in self.allowed:
            line_edit.clear()
            return
        self.allowed.add(text)
        if text in self.blocked:
            self.blocked.discard(text)
            if text in self.blocked_checks:
                cb = self.blocked_checks.pop(text)
                cb.setParent(None)
        cb = QCheckBox(text)
        cb.setChecked(True)
        cb.stateChanged.connect(self._on_allowed_changed)
        self.allowed_checks[text] = cb
        scroll_layout.insertWidget(scroll_layout.count() - 1, cb)
        line_edit.clear()

    def _add_custom_blocked(self, name, scroll_layout, line_edit):
        text = (name or "").strip()
        if not text:
            return
        if text in self.blocked:
            line_edit.clear()
            return
        self.blocked.add(text)
        if text in self.allowed:
            self.allowed.discard(text)
            if text in self.allowed_checks:
                cb = self.allowed_checks.pop(text)
                cb.setParent(None)
        cb = QCheckBox(text)
        cb.setChecked(True)
        cb.stateChanged.connect(self._on_blocked_changed)
        self.blocked_checks[text] = cb
        scroll_layout.insertWidget(scroll_layout.count() - 1, cb)
        line_edit.clear()


class FocusDashboardScreen(QWidget):
    def __init__(self, parent=None, state=None):
        super().__init__(parent)
        self.parent = parent
        self.state = state or load_state()
        self.elapsed_seconds = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.tip_timer = QTimer(self)
        self.tip_timer.timeout.connect(self._add_tip)
        self.feed_layout = None
        self.timer_label = None
        self.distraction_label = None
        self._setup_ui()
        self._start_timers()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Focus Session")
        title.setStyleSheet(f"font-size:20px;font-weight:600;color:{theme.COLOR_TEXT_MAIN};")

        self.timer_label = QLabel("00:00:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet(
            f"font-size:26px;font-weight:600;color:{theme.COLOR_TEXT_MAIN};margin:8px 0;"
        )

        gradient = QFrame()
        gradient.setFixedHeight(120)
        gradient.setStyleSheet(
            "background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #eef2ff, stop:1 #e0f2fe);border-radius:16px;"
        )

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.feed_layout = QVBoxLayout(container)
        self.feed_layout.setSpacing(8)

        def card(title_text, body_text):
            f = QFrame()
            f.setFrameShape(QFrame.StyledPanel)
            f.setStyleSheet(
                "background:white;border-radius:12px;border:1px solid #e5e7eb;"
            )
            v = QVBoxLayout(f)
            t = QLabel(title_text)
            t.setStyleSheet(f"font-weight:600;color:{theme.COLOR_TEXT_MAIN};")
            b = QLabel(body_text)
            b.setStyleSheet("color:#6b7280;font-size:12px;")
            v.addWidget(t)
            v.addWidget(b)
            return f

        self.feed_layout.addWidget(card("Focus time", "Tracking your deep work block."))
        self.feed_layout.addWidget(card("Eye strain", "Keep your eyes relaxed and blink often."))
        self.feed_layout.addWidget(card("Posture", "Sit upright and keep shoulders relaxed."))
        self.feed_layout.addWidget(card("Brightness", "Use a comfortable screen brightness."))
        self.distraction_label = QLabel("Distractions: 0")
        self.distraction_label.setStyleSheet("color:#6b7280;font-size:12px;")
        self.feed_layout.addWidget(self.distraction_label)
        self.feed_layout.addStretch()

        scroll.setWidget(container)

        bottom = QHBoxLayout()
        end_btn = QPushButton("End Session")
        end_btn.setStyleSheet(
            "QPushButton {background:#000000;color:white;border:none;border-radius:10px;"
            "padding:8px 16px;font-weight:500;}"
        )
        end_btn.clicked.connect(self._end_session)
        settings_btn = QPushButton("Settings")
        settings_btn.setStyleSheet(
            "QPushButton {background:#e5e7eb;color:#111827;border:none;border-radius:10px;"
            "padding:8px 16px;font-weight:500;}"
        )
        settings_btn.clicked.connect(self._open_settings)
        bottom.addWidget(end_btn)
        bottom.addStretch()
        bottom.addWidget(settings_btn)

        layout.addWidget(title)
        layout.addWidget(self.timer_label)
        layout.addWidget(gradient)
        layout.addWidget(scroll, 1)
        layout.addLayout(bottom)

    def _start_timers(self):
        self.timer.start(1000)
        self.tip_timer.start(20 * 60 * 1000)

    def _tick(self):
        self.elapsed_seconds += 1
        h = self.elapsed_seconds // 3600
        m = (self.elapsed_seconds % 3600) // 60
        s = self.elapsed_seconds % 60
        self.timer_label.setText(f"{h:02d}:{m:02d}:{s:02d}")

    def _add_tip(self):
        tips = [
            "Blink more to reduce dryness.",
            "Adjust posture for comfort.",
            "Take a soft focus break for your eyes.",
        ]
        tip = tips[self.elapsed_seconds % len(tips)]
        f = QFrame()
        f.setStyleSheet(
            "background:#f9fafb;border-radius:12px;border:1px dashed #e5e7eb;"
        )
        v = QVBoxLayout(f)
        t = QLabel("Focus tip")
        t.setStyleSheet(f"font-weight:600;color:{theme.COLOR_TEXT_MAIN};")
        b = QLabel(tip)
        b.setStyleSheet("color:#6b7280;font-size:12px;")
        v.addWidget(t)
        v.addWidget(b)
        self.feed_layout.insertWidget(self.feed_layout.count() - 1, f)

    def record_distraction(self, app_name):
        self.state = load_state()
        active = self.state.get("activeSessionData", {})
        active["distractionAttempts"] = active.get("distractionAttempts", 0) + 1
        self.state["activeSessionData"] = active
        save_state(self.state)
        self.distraction_label.setText(f"Distractions: {active['distractionAttempts']}")

    def _end_session(self):
        self.timer.stop()
        self.tip_timer.stop()
        if hasattr(self.parent, "show_summary_screen"):
            self.parent.show_summary_screen(self.elapsed_seconds)

    def _open_settings(self):
        if hasattr(self.parent, "show_settings_screen"):
            self.parent.show_settings_screen()


class BlockedOverlayScreen(QWidget):
    def __init__(self, parent=None, app_name="Blocked app"):
        super().__init__(parent)
        self.parent = parent
        self.app_name = app_name
        self._setup_ui()

    def _setup_ui(self):
        # Full-screen, always-on-top, frameless overlay
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowSystemMenuHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background-color: rgba(15,23,42,0.85);")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setStyleSheet(
            "background:white;border-radius:16px;padding:24px;min-width:260px;"
        )
        v = QVBoxLayout(card)
        title = QLabel("This app breaks your focus")
        title.setStyleSheet(f"font-size:18px;font-weight:600;color:{theme.COLOR_TEXT_MAIN};")
        subtitle = QLabel(
            "You can return to your work or allow it for this session"
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color:#6b7280;font-size:13px;")
        btn_row = QHBoxLayout()
        back_btn = QPushButton("Return to Focus")
        back_btn.setStyleSheet(
            f"QPushButton {{background:{theme.COLOR_PRIMARY};color:white;border:none;border-radius:8px;"
            "padding:8px 16px;font-weight:500;}"
        )
        allow_btn = QPushButton("Allow for this session")
        allow_btn.setStyleSheet(
            "QPushButton {background:#e5e7eb;color:#111827;border:none;border-radius:8px;"
            "padding:8px 20px;font-weight:500;}"
        )
        back_btn.clicked.connect(self._return_focus)
        allow_btn.clicked.connect(self._allow_once)
        btn_row.addWidget(back_btn)
        btn_row.addWidget(allow_btn)

        v.addWidget(title)
        v.addWidget(subtitle)
        v.addLayout(btn_row)
        layout.addWidget(card)

    def _return_focus(self):
        if hasattr(self.parent, "hide_blocked_overlay"):
            self.parent.hide_blocked_overlay()

    def _allow_once(self):
        state = load_state()
        rules = state.get("sessionRules", {})
        allowed = set(rules.get("allowedApps", []))
        allowed.add(self.app_name)
        rules["allowedApps"] = sorted(allowed)
        state["sessionRules"] = rules
        save_state(state)

        # Also mark this exe as allowed for the current session in MainWindow
        if hasattr(self.parent, "allow_exe_for_session"):
            self.parent.allow_exe_for_session(self.app_name)

        # And allow as a domain for this session if applicable (web blocking)
        if hasattr(self.parent, "allow_domain_for_session"):
            self.parent.allow_domain_for_session(self.app_name)

        if hasattr(self.parent, "hide_blocked_overlay"):
            self.parent.hide_blocked_overlay()


class SummaryScreen(QWidget):
    def __init__(self, parent=None, state=None, elapsed_seconds=0):
        super().__init__(parent)
        self.parent = parent
        self.state = state or load_state()
        self.elapsed_seconds = elapsed_seconds
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Session Summary")
        title.setStyleSheet(f"font-size:20px;font-weight:600;color:{theme.COLOR_TEXT_MAIN};")

        active = self.state.get("activeSessionData", {})
        rules = self.state.get("sessionRules", {})
        minutes = self.elapsed_seconds // 60
        distractions = active.get("distractionAttempts", 0)

        def line(text):
            l = QLabel(text)
            l.setStyleSheet(f"color:{theme.COLOR_TEXT_MAIN};font-size:13px;")
            return l

        layout.addWidget(title)
        layout.addWidget(line(f"Total minutes focused: {minutes}"))
        layout.addWidget(line(f"Number of distraction attempts: {distractions}"))
        layout.addWidget(line("Allowed apps: " + ", ".join(rules.get("allowedApps", []))))
        layout.addWidget(line("Blocked apps: " + ", ".join(rules.get("blockedApps", []))))
        layout.addWidget(line("Eye strain indicator: balanced"))
        layout.addWidget(line("Posture reminders: gentle"))

        closing = QLabel("You built strong focus today")
        closing.setStyleSheet(
            f"margin-top:12px;font-weight:500;color:{theme.COLOR_ALLOWED};"
        )
        layout.addWidget(closing)

        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(44)
        close_btn.setStyleSheet(
            f"QPushButton {{background:{theme.COLOR_PRIMARY};color:white;border:none;border-radius:10px;"
            "font-size:15px;font-weight:500;margin-top:12px;}"
        )
        close_btn.clicked.connect(self._close_summary)
        layout.addStretch()
        layout.addWidget(close_btn)

    def _close_summary(self):
        session_entry = {
            "endedAt": datetime.now().isoformat(),
            "elapsedSeconds": self.elapsed_seconds,
            "selectedCategories": self.state.get("selectedCategories", []),
            "sessionRules": self.state.get("sessionRules", {}),
            "distractionAttempts": self.state.get("activeSessionData", {}).get(
                "distractionAttempts", 0
            ),
        }
        history = self.state.get("sessionHistory", [])
        history.insert(0, session_entry)
        self.state["sessionHistory"] = history
        self.state["activeSessionData"] = {}
        save_state(self.state)
        if hasattr(self.parent, "show_home_screen"):
            self.parent.show_home_screen()


class HistoryScreen(QWidget):
    def __init__(self, parent=None, state=None):
        super().__init__(parent)
        self.parent = parent
        self.state = state or load_state()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title = QLabel("Your Focus History")
        title.setStyleSheet("font-size:20px;font-weight:600;color:#0f172a;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        v = QVBoxLayout(container)
        v.setSpacing(8)

        for session in self.state.get("sessionHistory", []):
            card = QFrame()
            card.setStyleSheet(
                "background:white;border-radius:12px;border:1px solid #e5e7eb;"
            )
            cv = QVBoxLayout(card)
            dt = session.get("endedAt") or session.get("startTime", "")
            try:
                dt_display = datetime.fromisoformat(dt).strftime("%Y-%m-%d %H:%M")
            except Exception:
                dt_display = dt
            cats = ", ".join(session.get("selectedCategories", []))
            mins = session.get("elapsedSeconds", 0) // 60
            dist = session.get("distractionAttempts", 0)
            top = QLabel(f"{dt_display} • {mins} min • distractions: {dist}")
            top.setStyleSheet("font-weight:500;color:#111827;")
            cats_lbl = QLabel(f"Categories: {cats}")
            cats_lbl.setStyleSheet("color:#6b7280;font-size:12px;")
            apps = session.get("sessionRules", {})
            detail = QLabel(
                "Allowed: "
                + ", ".join(apps.get("allowedApps", []))
                + "\nBlocked: "
                + ", ".join(apps.get("blockedApps", []))
            )
            detail.setStyleSheet("color:#6b7280;font-size:12px;")
            cv.addWidget(top)
            cv.addWidget(cats_lbl)
            cv.addWidget(detail)
            v.addWidget(card)

        v.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)


class SettingsScreen(QWidget):
    def __init__(self, parent=None, state=None):
        super().__init__(parent)
        self.parent = parent
        self.state = state or load_state()
        self.prefs = self.state.get("userPreferences", {})
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Settings")
        title.setStyleSheet("font-size:20px;font-weight:600;color:#0f172a;")

        dur_row = QHBoxLayout()
        dur_label = QLabel("Default session duration (minutes)")
        dur_spin = QSpinBox()
        dur_spin.setRange(10, 240)
        dur_spin.setValue(int(self.prefs.get("defaultSessionMinutes", 50)))
        dur_spin.valueChanged.connect(self._update_duration)
        dur_row.addWidget(dur_label)
        dur_row.addStretch()
        dur_row.addWidget(dur_spin)

        posture_cb = QCheckBox("Show posture tips")
        posture_cb.setChecked(bool(self.prefs.get("postureTips", True)))
        posture_cb.stateChanged.connect(self._update_posture)

        eye_cb = QCheckBox("Show eye strain reminders")
        eye_cb.setChecked(bool(self.prefs.get("eyeStrainReminders", True)))
        eye_cb.stateChanged.connect(self._update_eye)

        clear_btn = QPushButton("Clear all session history")
        clear_btn.setStyleSheet(
            "QPushButton {background:#fee2e2;color:#b91c1c;border:none;border-radius:8px;"
            "padding:8px 12px;font-weight:500;}"
        )
        clear_btn.clicked.connect(self._clear_history)

        allowed_label = QLabel("Allowed domains for this session")
        allowed_label.setStyleSheet("font-weight:600;color:#0369a1;margin-top:12px;")
        allowed_input = QLineEdit()
        allowed_input.setPlaceholderText("Enter a domain (e.g. google.com)")
        allowed_input.returnPressed.connect(lambda: self._add_allowed_domain(allowed_input.text()))
        allowed_input.setStyleSheet("background:white;border:1px solid #e5e7eb;border-radius:8px;padding:8px;")

        blocked_label = QLabel("Blocked domains for this session")
        blocked_label.setStyleSheet("font-weight:600;color:#b91c1c;margin-top:12px;")
        blocked_input = QLineEdit()
        blocked_input.setPlaceholderText("Enter a domain (e.g. facebook.com)")
        blocked_input.returnPressed.connect(lambda: self._add_blocked_domain(blocked_input.text()))
        blocked_input.setStyleSheet("background:white;border:1px solid #e5e7eb;border-radius:8px;padding:8px;")

        layout.addWidget(title)
        layout.addLayout(dur_row)
        layout.addWidget(posture_cb)
        layout.addWidget(eye_cb)
        layout.addStretch()
        layout.addWidget(clear_btn)
        layout.addWidget(allowed_label)
        layout.addWidget(allowed_input)
        layout.addWidget(blocked_label)
        layout.addWidget(blocked_input)

    def _save_prefs(self):
        self.state["userPreferences"] = self.prefs
        save_state(self.state)

    def _update_duration(self, value):
        self.prefs["defaultSessionMinutes"] = int(value)
        self._save_prefs()

    def _update_posture(self, state_val):
        self.prefs["postureTips"] = bool(state_val)
        self._save_prefs()

    def _update_eye(self, state_val):
        self.prefs["eyeStrainReminders"] = bool(state_val)
        self._save_prefs()

    def _clear_history(self):
        self.state["sessionHistory"] = []
        save_state(self.state)

    def _add_allowed_domain(self, domain: str):
        d = domain.lower().strip()
        if not d:
            return
        parent = self.parent
        if hasattr(parent, "add_allowed_domain"):
            parent.add_allowed_domain(d)

    def _add_blocked_domain(self, domain: str):
        d = domain.lower().strip()
        if not d:
            return
        parent = self.parent
        if hasattr(parent, "add_blocked_domain"):
            parent.add_blocked_domain(d)


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
        title.setStyleSheet("font-size:24px;font-weight:700;color:#0f172a;")
        subtitle = QLabel("Your offline focus companion")
        subtitle.setStyleSheet("color:#6b7280;font-size:13px;")

        start_btn = QPushButton("Start New Session")
        start_btn.setFixedHeight(44)
        theme.style_primary_button(start_btn)
        start_btn.clicked.connect(self._start_session)

        history_btn = QPushButton("History")
        theme.style_secondary_button(history_btn)
        history_btn.clicked.connect(self._open_history)
        settings_btn = QPushButton("Settings")
        theme.style_secondary_button(settings_btn)
        settings_btn.clicked.connect(self._open_settings)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()
        layout.addWidget(start_btn)
        layout.addWidget(history_btn)
        layout.addWidget(settings_btn)

    def _start_session(self):
        if hasattr(self.parent, "show_intent_screen"):
            self.parent.show_intent_screen()

    def _open_history(self):
        if hasattr(self.parent, "show_history_screen"):
            self.parent.show_history_screen()

    def _open_settings(self):
        if hasattr(self.parent, "show_settings_screen"):
            self.parent.show_settings_screen()


class DesktopWatcher:
    """Background thread that reports foreground window exe + title via a Queue."""

    def __init__(self, event_queue: Queue, poll_interval: float = 0.2):
        self.event_queue = event_queue
        self.poll_interval = poll_interval
        self._stop_event = threading.Event()
        self._thread = None
        self._last_state = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def _run(self):
        while not self._stop_event.is_set():
            try:
                exe, title = self._get_foreground_exe_and_title()
                state = {"exe": (exe or "").lower(), "title": title or ""}
                if state != self._last_state:
                    self._last_state = state
                    self.event_queue.put(
                        {
                            "type": "desktop_foreground",
                            "exe": state["exe"],
                            "title": state["title"],
                        }
                    )
            except Exception:
                # Never crash the watcher
                pass
            time.sleep(self.poll_interval)

    @staticmethod
    def _get_foreground_exe_and_title():
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None, None
        title = win32gui.GetWindowText(hwnd) or ""
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc = psutil.Process(pid)
            exe_path = proc.exe()
            exe_name = exe_path.split("\\")[-1]
            return exe_name, title
        except Exception:
            return None, title


class MainWindow(QMainWindow):
    def __init__(self, config=None):
        super().__init__()
        self.config = config or {}
        self.setWindowTitle("ZenFlow")
        self.resize(500, 700)
        self.setMinimumSize(420, 640)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.stacked_widget = QStackedWidget()

        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stacked_widget)

        # Apply global base theme to the main window background
        self.central_widget.setStyleSheet(theme.base_window_stylesheet)

        self.state = load_state()

        self.splash_screen = SplashScreen(self)
        self.intent_screen = None
        self.app_setup_screen = None
        self.dashboard_screen = None
        self.summary_screen = None
        self.history_screen = None
        self.settings_screen = None
        self.home_screen = HomeScreen(self)
        self.blocked_overlay = None

        self.stacked_widget.addWidget(self.splash_screen)
        self.stacked_widget.addWidget(self.home_screen)
        self.stacked_widget.setCurrentWidget(self.splash_screen)

        icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "zenflow.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # --- Desktop app blocking session state ---
        self.blocked_exes = {"chrome.exe", "msedge.exe", "firefox.exe"}
        self.allowed_exes_session = set()

        # --- Website blocking session state (per run, not persisted) ---
        self.blocked_domains = {
            "instagram.com",
            "tiktok.com",
            "youtube.com",
            "facebook.com",
            "twitter.com",
            "discord.com",
            "reddit.com",
        }
        self.allowed_domains_session = set()

        # Queue and watcher for desktop foreground windows
        self.desktop_event_queue = Queue()
        self.desktop_watcher = DesktopWatcher(self.desktop_event_queue, poll_interval=0.2)
        self.desktop_watcher.start()

        # Timer in main thread to process watcher events
        self.desktop_event_timer = QTimer(self)
        self.desktop_event_timer.timeout.connect(self._process_desktop_events)
        self.desktop_event_timer.start(100)

        self.current_blocked_exe = None

        # Queue and watcher for browser tab URLs (WebSocket from extension)
        self.web_event_queue = Queue()
        self.web_watcher = WebWatcher(self.web_event_queue)
        self.web_watcher.start()

        self.web_event_timer = QTimer(self)
        self.web_event_timer.timeout.connect(self._process_web_events)
        self.web_event_timer.start(100)

        self.current_blocked_domain = None

    def show_intent_screen(self):
        self.state = load_state()
        self.intent_screen = IntentScreen(self, self.state)
        self._add_and_show(self.intent_screen)

    def show_app_setup_screen(self):
        self.state = load_state()
        self.app_setup_screen = AppSetupScreen(self, self.state)
        self._add_and_show(self.app_setup_screen)

    def show_dashboard_screen(self):
        self.state = load_state()
        self.dashboard_screen = FocusDashboardScreen(self, self.state)
        self._add_and_show(self.dashboard_screen)

    def show_blocked_overlay(self, app_name="Blocked app"):
        # Create a full-screen overlay that sits above all windows
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

    def show_summary_screen(self, elapsed_seconds):
        self.state = load_state()
        self.summary_screen = SummaryScreen(self, self.state, elapsed_seconds)
        self._add_and_show(self.summary_screen)

    def show_home_screen(self):
        self._add_and_show(self.home_screen)

    def show_history_screen(self):
        self.state = load_state()
        self.history_screen = HistoryScreen(self, self.state)
        self._add_and_show(self.history_screen)

    def show_settings_screen(self):
        self.state = load_state()
        self.settings_screen = SettingsScreen(self, self.state)
        self._add_and_show(self.settings_screen)

    def _add_and_show(self, widget):
        if self.stacked_widget.indexOf(widget) == -1:
            self.stacked_widget.addWidget(widget)
        self.stacked_widget.setCurrentWidget(widget)

    def allow_exe_for_session(self, exe_name: str):
        """Mark an exe as allowed for the remainder of this run."""
        self.allowed_exes_session.add(exe_name.lower())

    def allow_domain_for_session(self, domain: str):
        """Mark a website domain as allowed for the remainder of this run."""
        self.allowed_domains_session.add(domain.lower())

    def add_allowed_domain(self, domain: str):
        """Add a domain to the allowed list for this run (and remove from blocked)."""
        d = domain.lower().strip()
        if not d:
            return
        self.allowed_domains_session.add(d)
        if d in self.blocked_domains:
            self.blocked_domains.remove(d)

    def add_blocked_domain(self, domain: str):
        """Add a domain to the blocked list for this run (and remove from allowed)."""
        d = domain.lower().strip()
        if not d:
            return
        self.blocked_domains.add(d)
        if d in self.allowed_domains_session:
            self.allowed_domains_session.remove(d)

    def _process_desktop_events(self):
        """Handle foreground app changes from DesktopWatcher."""
        latest = None
        while True:
            try:
                ev = self.desktop_event_queue.get_nowait()
                latest = ev
            except Empty:
                break

        if not latest:
            return

        if latest.get("type") != "desktop_foreground":
            return

        exe = latest.get("exe", "").lower()
        title = latest.get("title", "")

        is_blocked = (
            exe
            and exe in self.blocked_exes
            and exe not in self.allowed_exes_session
        )

        if is_blocked:
            if self.current_blocked_exe == exe:
                return
            self.current_blocked_exe = exe
            self.show_blocked_overlay(exe)
        else:
            if self.current_blocked_exe is not None:
                self.current_blocked_exe = None
                self.hide_blocked_overlay()

    def _process_web_events(self):
        """Handle active tab URL changes from WebWatcher (browser extension)."""
        latest = None
        while True:
            try:
                ev = self.web_event_queue.get_nowait()
                latest = ev
            except Empty:
                break

        if not latest:
            return

        if latest.get("type") != "web_foreground":
            return

        url = (latest.get("url", "") or "").lower()
        title = latest.get("title", "") or ""

        # Decide if this URL is blocked based on blocked_domains and allowed_domains_session
        blocked_domain = None
        for domain in self.blocked_domains:
            if domain in url and domain not in self.allowed_domains_session:
                blocked_domain = domain
                break

        if blocked_domain:
            # Already showing for this domain? do nothing.
            if self.current_blocked_domain == blocked_domain:
                return
            self.current_blocked_domain = blocked_domain
            # Use overlay with the domain label
            self.show_blocked_overlay(blocked_domain)
        else:
            if self.current_blocked_domain is not None:
                self.current_blocked_domain = None
                self.hide_blocked_overlay()

    def closeEvent(self, event):
        try:
            if hasattr(self, "desktop_watcher") and self.desktop_watcher:
                self.desktop_watcher.stop()
            if hasattr(self, "web_watcher") and self.web_watcher:
                self.web_watcher.stop()
        except Exception:
            pass
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())