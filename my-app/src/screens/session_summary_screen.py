from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt
import theme


class SessionSummaryScreen(QWidget):
    def __init__(self, parent=None, state=None):
        super().__init__(parent)
        self.parent = parent
        self.state = state or {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Session Summary")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: 600; color: {theme.COLOR_TEXT_MAIN};"
        )

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        v_layout = QVBoxLayout(container)
        v_layout.setSpacing(16)

        # Get the most recent session
        history = self.state.get("sessionHistory", [])
        if history:
            session = history[0]
            
            # Session duration
            duration_card = self._create_card(
                "Session Duration",
                f"{self._format_duration(session.get('elapsedSeconds', 0))}"
            )
            v_layout.addWidget(duration_card)
            
            # Categories
            cats = ", ".join(session.get("selectedCategories", []))
            categories_card = self._create_card(
                "Work Categories",
                cats or "None"
            )
            v_layout.addWidget(categories_card)
            
            # Distractions
            dist = session.get("distractionAttempts", 0)
            distractions_card = self._create_card(
                "Distraction Attempts",
                str(dist)
            )
            v_layout.addWidget(distractions_card)
            
            # Apps
            rules = session.get("sessionRules", {})
            apps_text = f"Allowed: {len(rules.get('allowedApps', []))} | Blocked: {len(rules.get('blockedApps', []))}"
            apps_card = self._create_card(
                "App Rules",
                apps_text
            )
            v_layout.addWidget(apps_card)

        scroll.setWidget(container)

        # Buttons
        button_layout = QHBoxLayout()
        
        new_session_btn = QPushButton("Start New Session")
        new_session_btn.setStyleSheet(
            f"QPushButton {{background:{theme.COLOR_PRIMARY};color:white;border:none;border-radius:10px;"
            "font-size:15px;font-weight:500;}"
        )
        new_session_btn.clicked.connect(self._start_new_session)
        
        home_btn = QPushButton("Back to Home")
        home_btn.setStyleSheet(
            "QPushButton {background:#e5e7eb;color:#111827;border:none;border-radius:10px;"
            "font-size:15px;font-weight:500;}"
        )
        home_btn.clicked.connect(self._go_home)
        
        button_layout.addWidget(new_session_btn)
        button_layout.addWidget(home_btn)

        layout.addWidget(title)
        layout.addWidget(scroll, 1)
        layout.addLayout(button_layout)

    def _create_card(self, title_text, content_text):
        from PyQt5.QtWidgets import QFrame
        card = QFrame()
        card.setFrameStyle(QFrame.StyledPanel)
        card.setStyleSheet(
            "background:white;border-radius:12px;border:1px solid #e5e7eb;padding:16px;"
        )
        
        layout = QVBoxLayout(card)
        
        title = QLabel(title_text)
        title.setStyleSheet(f"font-weight:600;color:{theme.COLOR_TEXT_MAIN};font-size:16px;")
        
        content = QLabel(content_text)
        content.setStyleSheet("color:#6b7280;font-size:14px;")
        content.setWordWrap(True)
        
        layout.addWidget(title)
        layout.addWidget(content)
        
        return card

    def _format_duration(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    def _start_new_session(self):
        if hasattr(self.parent, "show_intent_screen"):
            self.parent.show_intent_screen()

    def _go_home(self):
        if hasattr(self.parent, "show_intent_screen"):
            self.parent.show_intent_screen()
