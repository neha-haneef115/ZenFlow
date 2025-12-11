from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
import src.theme as theme


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

BROWSER_APPS = [
    "Google Chrome",
    "Mozilla Firefox",
    "Microsoft Edge",
    "Safari",
    "Opera",
]


class IntentScreen(QWidget):
    def __init__(self, parent=None, state=None):
        super().__init__(parent)
        self.parent = parent
        self.state = state or {}
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
                    "QPushButton {background:#f5f5f5;border:1px solid #d4d4d4;"
                    f"border-radius:12px;font-size:15px;font-weight:500;color:{theme.COLOR_TEXT_MAIN};"
                    "}"
                    f"QPushButton:checked {{background:#f5f5f5;color:#6E260E;border:2px solid #6E260E;}}"
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
        self.state["sessionRules"] = self._compute_session_rules()
        if hasattr(self.parent, "save_state"):
            self.parent.save_state(self.state)
        if hasattr(self.parent, "show_app_setup_screen"):
            self.parent.show_app_setup_screen()
