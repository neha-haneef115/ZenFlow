"""
category_screen.py

ZenFlow 'Category Selection' screen (PyQt5 version to match existing project).

Features:
- Three main categories:
    Allowed Apps/Websites – work, productivity, educational tools
    Blocked / Social Media Apps/Websites – Instagram, TikTok, Facebook, Twitter, YouTube, Discord, etc.
    Neutral / Optional Apps/Websites – Slack, Spotify, misc tools
- Each category in a collapsible panel with checkboxes.
- Add-new input per category (apps or websites).
- Global search/filter box.
- Immediate in-memory session state updates.
- Styled 'Save & Continue' and 'Cancel' buttons using coffee-brown #6F4E37.
- Inter font used throughout if installed on system.

You can embed this widget inside your existing MainWindow via a QStackedWidget.
"""

from __future__ import annotations
from typing import Dict, List, Set

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QScrollArea,
    QFrame,
    QCheckBox,
)


COFFEE_BROWN = "#6F4E37"


class CollapsibleCategoryPanel(QWidget):
    """Collapsible panel for a single category (Allowed / Blocked / Neutral)."""

    # Emitted when checkbox state changes: category_key, item_name, checked
    itemToggled = pyqtSignal(str, str, bool)
    # Emitted when a new item is added: category_key, item_name
    itemAdded = pyqtSignal(str, str)

    def __init__(
        self,
        category_key: str,
        title: str,
        color_role: str,
        tooltip: str,
        items: List[str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.category_key = category_key        # "allowed" | "blocked" | "neutral"
        self.color_role = color_role            # same, for styling
        self.items: Dict[str, QCheckBox] = {}   # name -> checkbox
        self._collapsed = False

        self._build_ui(title, tooltip, items)

    def _build_ui(self, title: str, tooltip: str, items: List[str]) -> None:
        """Build the header and content for this panel."""
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        # Header row (toggle + title)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)

        self.toggle_btn = QPushButton("−")
        self.toggle_btn.setFixedWidth(24)
        self.toggle_btn.clicked.connect(self._toggle_collapsed)
        self.toggle_btn.setStyleSheet(
            "QPushButton {border:none;font-weight:bold;font-size:16px;color:#4b5563;}"
        )

        title_label = QLabel(title)
        title_label.setToolTip(tooltip)
        title_label.setStyleSheet("font-size:14px;font-weight:600;color:#111827;")

        header.addWidget(self.toggle_btn)
        header.addWidget(title_label)
        header.addStretch()

        root.addLayout(header)

        # Content frame (items + add-new row)
        self.content_frame = QFrame()
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(8, 4, 8, 4)
        content_layout.setSpacing(4)

        # Items layout
        self.items_layout = QVBoxLayout()
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(2)

        for name in items:
            self._add_item_checkbox(name, checked=True)

        self.items_layout.addStretch()
        content_layout.addLayout(self.items_layout)

        # Add-new row
        add_row = QHBoxLayout()
        self.input_new = QLineEdit()
        self.input_new.setPlaceholderText("Add app or website...")
        self.input_new.returnPressed.connect(self._handle_add_clicked)

        add_btn = QPushButton("Add")
        add_btn.setFixedWidth(70)
        add_btn.clicked.connect(self._handle_add_clicked)
        add_btn.setStyleSheet(
            f"QPushButton {{background:{COFFEE_BROWN};color:black;"
            "border:none;border-radius:8px;padding:4px 10px;font-size:12px;}"
            "QPushButton:hover {background:#5b3e2d;}"
        )

        add_row.addWidget(self.input_new)
        add_row.addWidget(add_btn)

        content_layout.addLayout(add_row)

        root.addWidget(self.content_frame)

    def _toggle_collapsed(self) -> None:
        """Expand or collapse the content frame."""
        self._collapsed = not self._collapsed
        self.content_frame.setVisible(not self._collapsed)
        self.toggle_btn.setText("+" if self._collapsed else "−")

    def _color_for_role(self) -> str:
        """Return text color for each category type."""
        if self.color_role == "allowed":
            return "#16a34a"  # green
        if self.color_role == "blocked":
            return "#dc2626"  # red
        return "#6b7280"      # gray

    def _add_item_checkbox(self, name: str, checked: bool = True) -> None:
        """Create and add a checkbox for the given item name."""
        if name in self.items:
            return
        cb = QCheckBox(name)
        cb.setChecked(checked)
        cb.stateChanged.connect(
            lambda state, n=name: self.itemToggled.emit(
                self.category_key, n, bool(state)
            )
        )
        cb.setStyleSheet(
            f"QCheckBox {{color:{self._color_for_role()};font-size:13px;}}"
        )
        # Insert before the stretch
        self.items_layout.insertWidget(self.items_layout.count() - 1, cb)
        self.items[name] = cb

    def _handle_add_clicked(self) -> None:
        """Handle Add button or Enter in the input field."""
        text = self.input_new.text().strip()
        if not text:
            return
        self._add_item_checkbox(text, checked=True)
        self.itemAdded.emit(self.category_key, text)
        self.input_new.clear()

    def filter_items(self, query: str) -> None:
        """Filter visible items based on a case-insensitive query substring."""
        q = query.lower()
        for name, cb in self.items.items():
            cb.setVisible(q in name.lower())


class CategorySelectionScreen(QWidget):
    """ZenFlow 'Category Selection' main screen widget."""

    # Emitted when user clicks Save & Continue, with a copy of session_state
    saveRequested = pyqtSignal(dict)
    # Emitted when Cancel is clicked
    cancelRequested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # In-memory session state
        self.session_state: Dict[str, Set[str]] = {
            "allowed": set(),
            "blocked": set(),
            "neutral": set(),
        }

        self._build_ui()

    def _build_ui(self) -> None:
        """Construct the overall layout and widgets."""
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        header = QLabel("Category Selection")
        header.setStyleSheet("font-size:18px;font-weight:600;color:#0f172a;")

        subtitle = QLabel(
            "Choose which apps and websites are allowed, blocked, or neutral "
            "for this ZenFlow session."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color:#6b7280;font-size:12px;")

        # Search / filter row
        search_row = QHBoxLayout()
        search_label = QLabel("Search:")
        search_label.setStyleSheet("font-size:12px;color:#374151;")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter apps or websites...")
        self.search_input.textChanged.connect(self._apply_filter)
        search_row.addWidget(search_label)
        search_row.addWidget(self.search_input)

        # Scroll area for panels
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(8)

        # Initial items
        allowed_items = [
            "VS Code",
            "PyCharm",
            "Figma",
            "Word",
            "Excel",
            "PDF Reader",
        ]
        blocked_items = [
            "Instagram",
            "TikTok",
            "Facebook",
            "Twitter",
            "YouTube",
            "Discord",
            "Spotify",
        ]
        neutral_items = [
            "Slack",
            "Teams",
            "Notepad",
        ]

        # Tooltips
        allowed_tip = "Work, productivity, and educational tools that support your focus."
        blocked_tip = "Social media and entertainment apps/websites that break your focus."
        neutral_tip = "Optional tools you can decide to allow or block during the session."

        # Create panels
        self.allowed_panel = CollapsibleCategoryPanel(
            "allowed",
            "Allowed Apps / Websites",
            color_role="allowed",
            tooltip=allowed_tip,
            items=allowed_items,
        )
        self.blocked_panel = CollapsibleCategoryPanel(
            "blocked",
            "Blocked / Social Media Apps / Websites",
            color_role="blocked",
            tooltip=blocked_tip,
            items=blocked_items,
        )
        self.neutral_panel = CollapsibleCategoryPanel(
            "neutral",
            "Neutral / Optional Apps / Websites",
            color_role="neutral",
            tooltip=neutral_tip,
            items=neutral_items,
        )

        # Connect signals
        for panel in (self.allowed_panel, self.blocked_panel, self.neutral_panel):
            panel.itemToggled.connect(self._on_item_toggled)
            panel.itemAdded.connect(self._on_item_added)

        # Initialize session_state as all items checked
        for n in allowed_items:
            self.session_state["allowed"].add(n)
        for n in blocked_items:
            self.session_state["blocked"].add(n)
        for n in neutral_items:
            self.session_state["neutral"].add(n)

        container_layout.addWidget(self.allowed_panel)
        container_layout.addWidget(self.blocked_panel)
        container_layout.addWidget(self.neutral_panel)
        container_layout.addStretch()

        scroll.setWidget(container)

        # Bottom buttons (coffee-brown style)
        buttons_row = QHBoxLayout()
        buttons_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        save_btn = QPushButton("Save & Continue")

        btn_style = (
            f"QPushButton {{"
            f"  background:{COFFEE_BROWN};"
            f"  color:black;"
            f"  border:none;"
            f"  border-radius:8px;"
            f"  padding:8px 18px;"
            f"  font-size:13px;"
            f"  font-weight:500;"
            f"}}"
            "QPushButton:hover {background:#5b3e2d;}"
        )
        cancel_btn.setStyleSheet(btn_style)
        save_btn.setStyleSheet(btn_style)

        cancel_btn.clicked.connect(self._on_cancel)
        save_btn.clicked.connect(self._on_save)

        buttons_row.addWidget(cancel_btn)
        buttons_row.addWidget(save_btn)

        # Assemble layout
        root.addWidget(header)
        root.addWidget(subtitle)
        root.addLayout(search_row)
        root.addWidget(scroll, 1)
        root.addLayout(buttons_row)

        # Global style: Inter (if installed) or fallback
        self.setStyleSheet(
            """
            QWidget {
                background:white;
                font-family: Inter, "Segoe UI", sans-serif;
            }
            QLineEdit {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 6px 8px;
                font-size: 13px;
            }
            QScrollArea {
                border: none;
            }
            """
        )

    # --------- Event handlers & helpers ---------

    def _apply_filter(self, text: str) -> None:
        """Apply filter text to all category panels."""
        self.allowed_panel.filter_items(text)
        self.blocked_panel.filter_items(text)
        self.neutral_panel.filter_items(text)

    def _on_item_toggled(self, category_key: str, name: str, checked: bool) -> None:
        """Update session_state when a checkbox is toggled."""
        bucket = self.session_state.get(category_key)
        if bucket is None:
            return
        if checked:
            bucket.add(name)
        else:
            bucket.discard(name)

    def _on_item_added(self, category_key: str, name: str) -> None:
        """Handle a newly added item: include it in the session_state."""
        bucket = self.session_state.get(category_key)
        if bucket is not None:
            bucket.add(name)

    def _on_cancel(self) -> None:
        """Emit cancelRequested when user clicks Cancel."""
        self.cancelRequested.emit()

    def _on_save(self) -> None:
        """Emit saveRequested with a copy of the current session_state."""
        state_copy = {k: set(v) for k, v in self.session_state.items()}
        self.saveRequested.emit(state_copy)


# Optional local test
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    screen = CategorySelectionScreen()
    screen.resize(700, 550)

    def on_save(state: dict) -> None:
        print("Saved session_state:", state)
        app.quit()

    def on_cancel() -> None:
        print("Cancelled.")
        app.quit()

    screen.saveRequested.connect(on_save)
    screen.cancelRequested.connect(on_cancel)

    screen.show()
    sys.exit(app.exec_())
