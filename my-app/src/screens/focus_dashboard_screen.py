from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QFrame, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer, QTime, QDateTime
import theme


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
        ]
        import random
        tip = random.choice(tips)
        
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Health Reminder", tip)

    def record_distraction(self, app_name):
        self.distraction_count += 1
        self.distraction_label.setText(f"Distractions: {self.distraction_count}")
        
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
