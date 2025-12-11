from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
import theme


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
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()

        # Main layout with semi-transparent background
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Overlay background
        overlay = QWidget()
        overlay.setStyleSheet(
            "background-color: rgba(0, 0, 0, 0.85);"
            "border-radius: 0px;"
        )
        overlay_layout = QVBoxLayout(overlay)
        overlay_layout.setContentsMargins(40, 40, 40, 40)
        overlay_layout.setAlignment(Qt.AlignCenter)

        # Content card
        card = QWidget()
        card.setFixedWidth(500)
        card.setStyleSheet(
            "background-color: white;"
            "border-radius: 16px;"
            "padding: 32px;"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(20)
        card_layout.setAlignment(Qt.AlignCenter)

        # Icon and title
        icon_label = QLabel("🚫")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignCenter)

        title = QLabel("This app breaks your focus")
        title.setStyleSheet(
            f"font-size: 24px; font-weight: 600; color: {theme.COLOR_TEXT_MAIN};"
        )
        title.setAlignment(Qt.AlignCenter)

        # App name
        app_label = QLabel(self.app_name)
        app_label.setStyleSheet(
            "font-size: 18px; color: #6b7280;"
        )
        app_label.setAlignment(Qt.AlignCenter)

        # Description
        desc = QLabel(
            "You can return to your work or allow it for this session"
        )
        desc.setStyleSheet("font-size: 14px; color: #6b7280;")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        back_btn = QPushButton("Return to Focus")
        back_btn.setStyleSheet(
            f"QPushButton {{background:{theme.COLOR_PRIMARY};color:white;border:none;border-radius:8px;"
            "padding:12px 24px;font-size:14px;font-weight:500;}}"
        )
        back_btn.clicked.connect(self._return_focus)

        allow_btn = QPushButton("Allow for this session")
        allow_btn.setStyleSheet(
            "QPushButton {background:#f3f4f6;color:#111827;border:none;border-radius:8px;"
            "padding:12px 20px;font-size:14px;font-weight:500;}"
        )
        allow_btn.clicked.connect(self._allow_once)

        button_layout.addStretch()
        button_layout.addWidget(back_btn)
        button_layout.addWidget(allow_btn)
        button_layout.addStretch()

        # Add to card layout
        card_layout.addWidget(icon_label)
        card_layout.addWidget(title)
        card_layout.addWidget(app_label)
        card_layout.addWidget(desc)
        card_layout.addSpacing(20)
        card_layout.addLayout(button_layout)

        # Add card to overlay
        overlay_layout.addWidget(card, 0, Qt.AlignCenter)

        # Add overlay to main layout
        main_layout.addWidget(overlay)

    def _return_focus(self):
        if hasattr(self.parent, "hide_blocked_overlay"):
            self.parent.hide_blocked_overlay()
        # Ensure we return to the dashboard screen
        if hasattr(self.parent, "show_dashboard"):
            self.parent.show_dashboard()

    def _allow_once(self):
        # Add this app to allowed list for current session
        state = self.parent.state if hasattr(self.parent, 'state') else {}
        rules = state.get("sessionRules", {})
        
        # Remove from blocked apps and add to allowed apps
        if "blockedApps" in rules and self.app_name in rules["blockedApps"]:
            rules["blockedApps"].remove(self.app_name)
        if "allowedApps" in rules and self.app_name not in rules["allowedApps"]:
            rules["allowedApps"].append(self.app_name)
        
        state["sessionRules"] = rules
        
        # Also mark this exe as allowed for the current session in MainWindow
        if hasattr(self.parent, "allow_exe_for_session"):
            self.parent.allow_exe_for_session(self.app_name)
        
        # And allow as a domain for this session if applicable (web blocking)
        if hasattr(self.parent, "allow_domain_for_session"):
            self.parent.allow_domain_for_session(self.app_name)

        if hasattr(self.parent, "hide_blocked_overlay"):
            self.parent.hide_blocked_overlay()

    def keyPressEvent(self, event):
        # Allow Escape to close
        if event.key() == Qt.Key_Escape:
            self._return_focus()
        else:
            event.ignore()
