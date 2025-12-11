from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QListWidget, QListWidgetItem, QFrame
)
from PyQt5.QtCore import Qt
import src.theme as theme


class SessionSummaryScreen(QWidget):
    def __init__(self, parent=None, state=None):
        super().__init__(parent)
        self.parent = parent
        self.state = state or {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        title = QLabel("Session Complete")
        title.setStyleSheet(
            f"font-size:20px;font-weight:500;color:{theme.COLOR_TEXT_MAIN};letter-spacing:0.5px;"
        )
        title.setAlignment(Qt.AlignCenter)
        
        subtitle = QLabel("Great job staying focused!")
        subtitle.setStyleSheet("color:#6b7280;font-size:14px;margin-bottom:8px;")
        subtitle.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Get the most recent session
        history = self.state.get("sessionHistory", [])
        if history:
            session = history[0]
            
            # Main stats container
            stats_container = QFrame()
            stats_container.setStyleSheet(
                f"background:{theme.COLOR_PRIMARY};border-radius:16px;"
            )
            stats_layout = QVBoxLayout(stats_container)
            stats_layout.setContentsMargins(24, 24, 24, 24)
            stats_layout.setSpacing(16)
            
            # Duration
            duration_label = QLabel("Session Duration")
            duration_label.setStyleSheet(
                "color:rgba(255,255,255,0.8);font-size:12px;font-weight:500;letter-spacing:1px;text-transform:uppercase;"
            )
            duration_label.setAlignment(Qt.AlignCenter)
            
            duration_value = QLabel(self._format_duration(session.get('elapsedSeconds', 0)))
            duration_value.setStyleSheet(
                "color:white;font-size:28px;font-weight:300;font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;"
            )
            duration_value.setAlignment(Qt.AlignCenter)
            
            stats_layout.addWidget(duration_label)
            stats_layout.addWidget(duration_value)
            
            layout.addWidget(stats_container)
            
            # Secondary stats
            secondary_layout = QHBoxLayout()
            secondary_layout.setSpacing(12)
            
            # Distractions card
            dist = session.get("distractionAttempts", 0)
            distractions_card = self._create_mini_card(
                "Distractions", 
                str(dist),
                "#fef3c7"
            )
            secondary_layout.addWidget(distractions_card)
            
            # Categories card
            cats = len(session.get("selectedCategories", []))
            categories_card = self._create_mini_card(
                "Categories", 
                str(cats),
                "#dbeafe"
            )
            secondary_layout.addWidget(categories_card)
            
            # Apps card
            rules = session.get("sessionRules", {})
            apps_count = len(rules.get('allowedApps', [])) + len(rules.get('blockedApps', []))
            apps_card = self._create_mini_card(
                "Apps", 
                str(apps_count),
                "#e0e7ff"
            )
            secondary_layout.addWidget(apps_card)
            
            layout.addLayout(secondary_layout)
            
            # Details section
            details_container = QFrame()
            details_container.setStyleSheet(
                "background:#fafafa;border-radius:12px;"
            )
            details_layout = QVBoxLayout(details_container)
            details_layout.setContentsMargins(20, 20, 20, 20)
            details_layout.setSpacing(12)
            
            details_title = QLabel("Session Details")
            details_title.setStyleSheet(
                f"font-size:12px;font-weight:600;color:{theme.COLOR_TEXT_MAIN};text-transform:uppercase;letter-spacing:1px;"
            )
            
            # Categories detail
            cats_list = ", ".join(session.get("selectedCategories", []))
            if cats_list:
                categories_detail = QLabel(f"Categories: {cats_list}")
                categories_detail.setStyleSheet("color:#6b7280;font-size:13px;")
                categories_detail.setWordWrap(True)
                details_layout.addWidget(categories_detail)
            
            # Apps detail
            allowed_count = len(rules.get('allowedApps', []))
            blocked_count = len(rules.get('blockedApps', []))
            apps_detail = QLabel(f"App Rules: {allowed_count} allowed, {blocked_count} blocked")
            apps_detail.setStyleSheet("color:#6b7280;font-size:13px;")
            details_layout.addWidget(apps_detail)
            
            details_layout.addWidget(details_title)
            details_layout.addWidget(categories_detail if cats_list else QLabel())
            details_layout.addWidget(apps_detail)
            
            layout.addWidget(details_container)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        new_session_btn = QPushButton("Start New Session")
        new_session_btn.setStyleSheet(
            "QPushButton {background:#6E260E;color:white;border:none;border-radius:8px;"
            "padding:10px 20px;font-size:13px;font-weight:500;}"
        )
        new_session_btn.clicked.connect(self._start_new_session)
        
        home_btn = QPushButton("Back to Home")
        home_btn.setStyleSheet(
            "QPushButton {background:#000000;color:white;border:none;border-radius:8px;"
            "padding:10px 20px;font-size:13px;font-weight:500;}"
        )
        home_btn.clicked.connect(self._go_home)
        
        button_layout.addStretch()
        button_layout.addWidget(new_session_btn)
        button_layout.addWidget(home_btn)
        
        layout.addLayout(button_layout)

    def _create_mini_card(self, title_text, value_text, bg_color):
        """Create a small stat card with background color."""
        card = QFrame()
        card.setStyleSheet(
            f"background:{bg_color};border-radius:12px;"
        )
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel(title_text)
        title.setStyleSheet(
            "color:#6b7280;font-size:11px;font-weight:500;text-transform:uppercase;letter-spacing:0.5px;"
        )
        title.setAlignment(Qt.AlignCenter)
        
        value = QLabel(value_text)
        value.setStyleSheet(
            f"font-size:20px;font-weight:600;color:{theme.COLOR_TEXT_MAIN};"
        )
        value.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(value)
        
        return card
        
    def _create_card(self, title_text, content_text):
        """Legacy card method - kept for compatibility."""
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
