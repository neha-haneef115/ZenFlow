from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QFrame, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer, QTime, QDateTime
import src.theme as theme


class FocusDashboardScreen(QWidget):
    def __init__(self, parent=None, state=None):
        super().__init__(parent)
        self.parent = parent
        self.state = state or {}
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_timer)
        self.tip_timer = QTimer(self)
        self.tip_timer.timeout.connect(self._show_health_tip)
        self.session_start_time = QTime.currentTime()
        self.elapsed_seconds = 0
        self.distraction_count = 0
        self._setup_ui()
        self._start_timers()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header with title and timer
        header = QVBoxLayout()
        header.setSpacing(8)
        
        title = QLabel("Focus Session")
        title.setStyleSheet(
            f"font-size:18px;font-weight:500;color:{theme.COLOR_TEXT_MAIN};letter-spacing:0.5px;"
        )
        title.setAlignment(Qt.AlignCenter)
        
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet(
            f"font-size:32px;font-weight:300;color:{theme.COLOR_TEXT_MAIN};margin:4px 0 16px 0;"
            "font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;"
        )
        
        header.addWidget(title)
        header.addWidget(self.timer_label)
        layout.addLayout(header)

        # Minimalist status indicator
        status_frame = QFrame()
        status_frame.setFixedHeight(80)
        status_frame.setStyleSheet(
            "background:#6E260E;border-radius:12px;"
        )
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(16, 16, 16, 16)
        
        status_text = QLabel("In Focus")
        status_text.setStyleSheet(
            "color:white;font-size:14px;font-weight:500;letter-spacing:1px;"
        )
        status_text.setAlignment(Qt.AlignCenter)
        
        self.distraction_label = QLabel("0 distractions")
        self.distraction_label.setStyleSheet(
            "color:rgba(255,255,255,0.8);font-size:11px;font-weight:400;"
        )
        self.distraction_label.setAlignment(Qt.AlignCenter)
        
        status_layout.addWidget(status_text)
        status_layout.addWidget(self.distraction_label)
        
        layout.addWidget(status_frame)

        # Minimalist tips section
        tips_container = QFrame()
        tips_container.setStyleSheet(
            "background:#fafafa;border-radius:12px;"
        )
        tips_layout = QVBoxLayout(tips_container)
        tips_layout.setContentsMargins(20, 20, 20, 20)
        tips_layout.setSpacing(12)
        
        tips_title = QLabel("Wellness Tips")
        tips_title.setStyleSheet(
            f"font-size:12px;font-weight:600;color:{theme.COLOR_TEXT_MAIN};text-transform:uppercase;letter-spacing:1px;"
        )
        
        self.tip_label = QLabel("Take a deep breath and stay focused")
        self.tip_label.setStyleSheet(
            "color:#6b7280;font-size:13px;line-height:1.4;"
        )
        self.tip_label.setWordWrap(True)
        
        tips_layout.addWidget(tips_title)
        tips_layout.addWidget(self.tip_label)
        
        layout.addWidget(tips_container)
        layout.addStretch()

        # Clean button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        end_btn = QPushButton("End Session")
        end_btn.setStyleSheet(
            "QPushButton {background:#6E260E;color:white;border:none;border-radius:8px;"
            "padding:10px 20px;font-size:13px;font-weight:500;}"
        )
        end_btn.clicked.connect(self._end_session)
        
        settings_btn = QPushButton("Settings")
        settings_btn.setStyleSheet(
            "QPushButton {background:#000000;color:white;border:none;border-radius:8px;"
            "padding:10px 20px;font-size:13px;font-weight:500;}"
        )
        settings_btn.clicked.connect(self._open_settings)
        
        button_layout.addStretch()
        button_layout.addWidget(end_btn)
        button_layout.addWidget(settings_btn)
        
        layout.addLayout(button_layout)

    def _start_timers(self):
        self.timer.start(1000)
        self.tip_timer.start(20 * 60 * 1000)

    def _update_timer(self):
        self.elapsed_seconds += 1
        hours = self.elapsed_seconds // 3600
        minutes = (self.elapsed_seconds % 3600) // 60
        seconds = self.elapsed_seconds % 60
        self.timer_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def _show_health_tip(self):
        tips = [
            "Take a deep breath and stretch your shoulders.",
            "Look away from your screen for 20 seconds.",
            "Stand up and walk around for a minute.",
            "Drink some water to stay hydrated.",
            "Check your posture and straighten your back.",
            "Blink your eyes to reduce strain.",
            "Take three slow, deep breaths.",
            "Roll your shoulders gently.",
            "Stretch your neck side to side.",
            "Wiggle your fingers and toes.",
            "Focus on your breathing for 30 seconds.",
            "Adjust your screen brightness to comfort.",
            "Uncross your legs and sit straight.",
            "Massage your temples gently.",
            "Do a quick wrist stretch.",
            "Take a moment to smile.",
            "Gently roll your head in circles.",
            "Stretch your arms overhead.",
            "Focus on a distant object for 20 seconds.",
            "Take a mental break for 60 seconds."
        ]
        import random
        tip = random.choice(tips)
        
        # Update the tip label instead of showing a popup
        if hasattr(self, 'tip_label'):
            self.tip_label.setText(tip)

    def record_distraction(self, app_name):
        self.distraction_count += 1
        self.distraction_label.setText(f"{self.distraction_count} distraction{'s' if self.distraction_count != 1 else ''}")
        
        # Update session data
        active = self.state.get("activeSessionData", {})
        active["distractionAttempts"] = self.distraction_count
        self.state["activeSessionData"] = active
        if hasattr(self.parent, "save_state"):
            self.parent.save_state(self.state)

    def _end_session(self):
        self.timer.stop()
        self.tip_timer.stop()
        
        # Update session data
        active = self.state.get("activeSessionData", {})
        active["endTime"] = str(QDateTime.currentDateTime().toString())
        active["elapsedSeconds"] = self.elapsed_seconds
        self.state["activeSessionData"] = active
        
        # Add to history
        session_entry = {
            "startTime": active.get("startTime"),
            "endedAt": active.get("endTime"),
            "elapsedSeconds": self.elapsed_seconds,
            "selectedCategories": self.state.get("selectedCategories", []),
            "sessionRules": self.state.get("sessionRules", {}),
            "distractionAttempts": self.distraction_count,
        }
        
        history = self.state.get("sessionHistory", [])
        history.insert(0, session_entry)
        self.state["sessionHistory"] = history
        self.state["activeSessionData"] = {}
        
        if hasattr(self.parent, "save_state"):
            self.parent.save_state(self.state)
        
        if hasattr(self.parent, "show_session_summary"):
            self.parent.show_session_summary()

    def _open_settings(self):
        if hasattr(self.parent, "show_settings"):
            self.parent.show_settings()
