from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QListWidget, QListWidgetItem, QCheckBox, QLineEdit
)
from PyQt5.QtCore import Qt, QDateTime
import src.theme as theme


class AppSetupScreen(QWidget):
    def __init__(self, parent=None, state=None):
        super().__init__(parent)
        self.parent = parent
        self.state = state or {}
        self.allowed = set()
        self.blocked = set()
        self.allowed_checkboxes = {}
        self.blocked_checkboxes = {}
        self._init_from_state_or_categories()
        self._setup_ui()

    def _init_from_state_or_categories(self):
        """Load allowed/blocked from sessionRules or compute from categories."""
        rules = self.state.get("sessionRules", {})
        if rules.get("allowedApps") and rules.get("blockedApps"):
            self.allowed = set(rules.get("allowedApps", []))
            self.blocked = set(rules.get("blockedApps", []))
        else:
            # Fallback to category-based defaults
            selected = self.state.get("selectedCategories", [])
            from .intent_screen import PRESET_APPS, BROWSER_APPS, DISTRACTION_APPS
            for cat in selected:
                self.allowed.update(PRESET_APPS.get(cat, []))
            self.allowed.update(BROWSER_APPS)
            self.blocked = set(DISTRACTION_APPS)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Review and customize your app rules")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: 600; color: {theme.COLOR_TEXT_MAIN};"
        )
        subtitle = QLabel(
            "Allowed apps will stay accessible during your focus session. "
            "Distracting apps will be blocked."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #64748b; font-size: 13px;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea {"
            "border: none;"
            "background-color: transparent;"
            "}"
            "QScrollArea > QWidget > QWidget {"
            "background-color: transparent;"
            "}"
            "QScrollBar:vertical {"
            "border: none;"
            "background: #f3f4f6;"
            "width: 8px;"
            "border-radius: 4px;"
            "}"
            "QScrollBar::handle:vertical {"
            "background: #9ca3af;"
            "min-height: 20px;"
            "border-radius: 4px;"
            "}"
            "QScrollBar::handle:vertical:hover {"
            "background: #6b7280;"
            "}"
            "QScrollBar::handle:vertical:pressed {"
            "background: #4b5563;"
            "}"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {"
            "height: 0px;"
            "}"
        )
        container = QWidget()
        v_layout = QVBoxLayout(container)
        v_layout.setSpacing(16)

        # Allowed apps section
        allowed_label = QLabel("Allowed apps")
        allowed_label.setStyleSheet(f"font-weight:600;color:{theme.COLOR_ALLOWED};")
        v_layout.addWidget(allowed_label)

        allowed_list = QListWidget()
        allowed_list.setMaximumHeight(200)
        allowed_list.setStyleSheet(
            "QListWidget { border: 1px solid #e2e8f0; border-radius: 8px; background-color: #f8fafc; padding: 8px; }"
            "QListWidget::item { padding: 8px; border-radius: 6px; margin: 2px 0; }"
            "QListWidget::item:hover { background-color: #f1f5f9; }"
            "QListWidget::item:selected { background-color: transparent; }"
            "QCheckBox { spacing: 12px; font-size: 13px; }"
        )
        # Store reference
        self.allowed_list = allowed_list
        self._populate_allowed_list()
        v_layout.addWidget(allowed_list)

        # Custom app input for allowed
        custom_allowed_row = QHBoxLayout()
        custom_allowed_row.setSpacing(8)
        
        allowed_input = QLineEdit()
        allowed_input.setPlaceholderText("Add allowed app or site (e.g. Notion)")
        allowed_input.setStyleSheet(
            "QLineEdit {"
            "border: 1px solid #e5e7eb;"
            "border-radius: 8px;"
            "padding: 10px 12px;"
            "font-size: 13px;"
            "background-color: #ffffff;"
            "color: #374151;"
            "}"
            "QLineEdit:focus {"
            "border: 2px solid #6E260E;"
            "outline: none;"
            "}"
        )
        
        add_allowed_btn = QPushButton("Add to allowed")
        add_allowed_btn.setStyleSheet(
            "QPushButton {background:#6E260E;color:white;border:none;border-radius:8px;"
            "font-size:12px;font-weight:500;padding:10px 16px;}"
        )
        add_allowed_btn.clicked.connect(
            lambda: self._add_custom_allowed(allowed_input.text())
        )
        
        custom_allowed_row.addWidget(allowed_input, 1)
        custom_allowed_row.addWidget(add_allowed_btn)
        v_layout.addLayout(custom_allowed_row)
        
        # Store input reference
        self.allowed_input = allowed_input

        # Blocked apps section
        blocked_label = QLabel("Distracting apps")
        blocked_label.setStyleSheet(f"font-weight:600;color:{theme.COLOR_BLOCKED};margin-top:12px;")
        v_layout.addWidget(blocked_label)

        blocked_list = QListWidget()
        blocked_list.setMaximumHeight(200)
        blocked_list.setStyleSheet(
            "QListWidget { border: 1px solid #e2e8f0; border-radius: 8px; background-color: #f8fafc; padding: 8px; }"
            "QListWidget::item { padding: 8px; border-radius: 6px; margin: 2px 0; }"
            "QListWidget::item:hover { background-color: #f1f5f9; }"
            "QListWidget::item:selected { background-color: transparent; }"
            "QCheckBox { spacing: 12px; font-size: 13px; }"
        )
        # Store reference
        self.blocked_list = blocked_list
        self._populate_blocked_list()
        v_layout.addWidget(blocked_list)

        # Custom app input for blocked
        custom_blocked_row = QHBoxLayout()
        custom_blocked_row.setSpacing(8)
        
        blocked_input = QLineEdit()
        blocked_input.setPlaceholderText("Add blocked app or site (e.g. Instagram)")
        blocked_input.setStyleSheet(
            "QLineEdit {"
            "border: 1px solid #e5e7eb;"
            "border-radius: 8px;"
            "padding: 10px 12px;"
            "font-size: 13px;"
            "background-color: #ffffff;"
            "color: #374151;"
            "}"
            "QLineEdit:focus {"
            "border: 2px solid #6E260E;"
            "outline: none;"
            "}"
        )
        
        add_blocked_btn = QPushButton("Add to blocked")
        add_blocked_btn.setStyleSheet(
            "QPushButton {background:#000000;color:white;border:none;border-radius:8px;"
            "font-size:12px;font-weight:500;padding:10px 16px;}"
        )
        add_blocked_btn.clicked.connect(
            lambda: self._add_custom_blocked(blocked_input.text())
        )
        
        custom_blocked_row.addWidget(blocked_input, 1)
        custom_blocked_row.addWidget(add_blocked_btn)
        v_layout.addLayout(custom_blocked_row)
        
        # Store input reference
        self.blocked_input = blocked_input

        scroll.setWidget(container)

        # Start Session button
        start_btn = QPushButton("Start Session")
        start_btn.setFixedHeight(44)
        start_btn.setStyleSheet(
            "QPushButton {background:#6E260E;color:white;border:none;border-radius:8px;"
            "font-size:13px;font-weight:500;padding:10px 20px;}"
        )
        start_btn.clicked.connect(self._on_start_session)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(scroll, 1)
        layout.addWidget(start_btn)

    def _on_allowed_toggled(self, app, state):
        if state == Qt.Unchecked:
            self.allowed.discard(app)
            self.blocked.add(app)
        else:
            self.allowed.add(app)
            self.blocked.discard(app)

    def _on_blocked_toggled(self, app, state):
        if state == Qt.Unchecked:
            self.blocked.discard(app)
        else:
            self.blocked.add(app)
            self.allowed.discard(app)

    def _add_custom_allowed(self, app_name):
        app_name = app_name.strip()
        if app_name and app_name not in self.allowed:
            self.allowed.add(app_name)
            self.blocked.discard(app_name)
            # Clear input
            if hasattr(self, 'allowed_input'):
                self.allowed_input.clear()
            # Refresh UI
            self._refresh_ui()

    def _add_custom_blocked(self, app_name):
        app_name = app_name.strip()
        if app_name and app_name not in self.blocked:
            self.blocked.add(app_name)
            self.allowed.discard(app_name)
            # Clear input
            if hasattr(self, 'blocked_input'):
                self.blocked_input.clear()
            # Refresh UI
            self._refresh_ui()

    def _populate_allowed_list(self):
        """Populate the allowed apps list."""
        if not hasattr(self, 'allowed_list'):
            return
            
        self.allowed_list.clear()
        for app in sorted(self.allowed):
            item = QListWidgetItem()
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            checkbox.setText(app)
            checkbox.stateChanged.connect(
                lambda state, a=app: self._on_allowed_toggled(a, state)
            )
            self.allowed_checkboxes[app] = checkbox
            self.allowed_list.addItem(item)
            self.allowed_list.setItemWidget(item, checkbox)
    
    def _populate_blocked_list(self):
        """Populate the blocked apps list."""
        if not hasattr(self, 'blocked_list'):
            return
            
        self.blocked_list.clear()
        for app in sorted(self.blocked):
            item = QListWidgetItem()
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            checkbox.setText(app)
            checkbox.stateChanged.connect(
                lambda state, b=app: self._on_blocked_toggled(b, state)
            )
            self.blocked_checkboxes[app] = checkbox
            self.blocked_list.addItem(item)
            self.blocked_list.setItemWidget(item, checkbox)
    
    def _populate_lists(self):
        """Populate both allowed and blocked lists."""
        self._populate_allowed_list()
        self._populate_blocked_list()
        
    def _refresh_ui(self):
        """Refresh the UI to show updated allowed/blocked lists."""
        # Clear current checkboxes
        self.allowed_checkboxes.clear()
        self.blocked_checkboxes.clear()
        
        # Clear the lists
        if hasattr(self, 'allowed_list'):
            self.allowed_list.clear()
        if hasattr(self, 'blocked_list'):
            self.blocked_list.clear()
        
        # Repopulate the lists
        self._populate_lists()
        
    def _on_start_session(self):
        self.state["sessionRules"] = {
            "allowedApps": sorted(self.allowed),
            "blockedApps": sorted(self.blocked),
        }
        self.state["activeSessionData"] = {
            "startTime": str(QDateTime.currentDateTime().toString()),
            "distractionAttempts": 0,
        }
        if hasattr(self.parent, "save_state"):
            self.parent.save_state(self.state)
        if hasattr(self.parent, "show_dashboard"):
            self.parent.show_dashboard()
