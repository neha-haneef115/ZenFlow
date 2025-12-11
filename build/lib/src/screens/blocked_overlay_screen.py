from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QApplication, QStyle
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase
import src.theme as theme


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

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Overlay background - clean blur effect
        overlay = QWidget()
        overlay.setStyleSheet(
            "background: rgba(0, 0, 0, 0.88);"
        )
        overlay_layout = QVBoxLayout(overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setAlignment(Qt.AlignCenter)

        # Content card - minimal and clean
        card = QWidget()
        card.setFixedWidth(420)
        card.setStyleSheet(
            "background-color: #ffffff;"
            "border-radius: 16px;"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setAlignment(Qt.AlignCenter)

        # Icon - simple and minimal
        icon_label = QLabel()
        icon = QApplication.style().standardIcon(QStyle.SP_MessageBoxCritical)
        pixmap = icon.pixmap(48, 48)
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("background: transparent;")

        # Title - clean typography
        title = QLabel("App Blocked")
        title.setStyleSheet(
            "font-size: 24px; font-weight: 600; color: #111827; "
            "background: transparent;"
        )
        title.setAlignment(Qt.AlignCenter)

        # App name - subtle accent
        app_label = QLabel(self.app_name)
        app_label.setStyleSheet(
            "font-size: 15px; font-weight: 500; color: #6b7280; "
            "background: transparent;"
        )
        app_label.setAlignment(Qt.AlignCenter)

        # Description - minimal
        desc = QLabel("Choose an option to continue")
        desc.setStyleSheet(
            "font-size: 13px; color: #9ca3af; "
            "background: transparent;"
        )
        desc.setAlignment(Qt.AlignCenter)

        # Buttons - clean and simple
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        back_btn = QPushButton("Return to Focus")
        back_btn.setStyleSheet(
            "QPushButton {"
            "background: #6E260E;"
            "color: white; border: none; border-radius: 8px;"
            "padding: 12px 24px; font-size: 13px; font-weight: 500;"
            "}"
            "QPushButton:hover {"
            "background: #8B3214;"
            "}"
        )
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self._return_focus)

        allow_btn = QPushButton("Allow Once")
        allow_btn.setStyleSheet(
            "QPushButton {"
            "background: #f9fafb; color: #374151; border: 1px solid #e5e7eb;"
            "border-radius: 8px; padding: 12px 24px; font-size: 13px; font-weight: 500;"
            "}"
            "QPushButton:hover {"
            "background: #f3f4f6;"
            "}"
        )
        allow_btn.setCursor(Qt.PointingHandCursor)
        allow_btn.clicked.connect(self._allow_once)

        button_layout.addWidget(back_btn)
        button_layout.addWidget(allow_btn)

        # Add to card layout
        card_layout.addWidget(icon_label)
        card_layout.addSpacing(4)
        card_layout.addWidget(title)
        card_layout.addSpacing(2)
        card_layout.addWidget(app_label)
        card_layout.addSpacing(8)
        card_layout.addWidget(desc)
        card_layout.addSpacing(12)
        card_layout.addLayout(button_layout)

        # Add card to overlay
        overlay_layout.addWidget(card, 0, Qt.AlignCenter)

        # Add overlay to main layout
        main_layout.addWidget(overlay)

    def _return_focus(self):
        # Hide the overlay first
        if hasattr(self.parent, "hide_blocked_overlay"):
            self.parent.hide_blocked_overlay()
        
        # Ensure the parent window is shown and raised
        if hasattr(self.parent, "showNormal"):
            self.parent.showNormal()
        if hasattr(self.parent, "raise_"):
            self.parent.raise_()
        if hasattr(self.parent, "activateWindow"):
            self.parent.activateWindow()
        
        # Route to dashboard
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
        
        # Mark this exe as allowed for the current session
        if hasattr(self.parent, "allow_exe_for_session"):
            self.parent.allow_exe_for_session(self.app_name)
        
        # Allow as a domain for this session if applicable
        if hasattr(self.parent, "allow_domain_for_session"):
            self.parent.allow_domain_for_session(self.app_name)

        # Hide overlay and minimize to let user access the app
        if hasattr(self.parent, "hide_blocked_overlay"):
            self.parent.hide_blocked_overlay()
        
        if hasattr(self.parent, "showMinimized"):
            self.parent.showMinimized()

    def keyPressEvent(self, event):
        # Allow Escape to close
        if event.key() == Qt.Key_Escape:
            self._return_focus()
        else:
            event.ignore()