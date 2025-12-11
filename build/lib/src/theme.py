"""
theme.py

Global ZenFlow theme (font, colors, and common styles).

Call theme.apply_global_theme(app) once after creating QApplication.
Then use the exported styles on windows, buttons, checkboxes, inputs, and overlays.
"""

from __future__ import annotations
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QApplication

# Color palette
COLOR_PRIMARY = "#6E260E"  # primary brown
COLOR_ALLOWED = "#27AE60"  # green
COLOR_BLOCKED = "#E74C3C"  # red
COLOR_NEUTRAL = "#BDC3C7"  # gray
COLOR_BACKGROUND = "#F5F5F5"  # main screens
COLOR_OVERLAY_BG = "rgba(28,28,28,0.94)"  # dark overlay
COLOR_TEXT_MAIN = "#111827"
COLOR_TEXT_SUBTLE = "#6B7280"
COLOR_TEXT_OVERLAY = "#FFFFFF"


def load_inter_font() -> None:
    """Try to load Inter font from bundled assets (if present)."""
    try:
        QFontDatabase.addApplicationFont("assets/fonts/Inter-Regular.ttf")
        QFontDatabase.addApplicationFont("assets/fonts/Inter-Medium.ttf")
        QFontDatabase.addApplicationFont("assets/fonts/Inter-Bold.ttf")
    except Exception:
        pass


def apply_global_theme(app: QApplication) -> None:
    """Apply global Inter font to the whole application."""
    load_inter_font()
    app.setStyleSheet(
        """
        * {
            font-family: Inter, "Segoe UI", sans-serif;
        }
        """
    )


# Base window stylesheet for all normal screens
base_window_stylesheet = f"""
QWidget {{
    background: {COLOR_BACKGROUND};
    color: {COLOR_TEXT_MAIN};
}}

QLabel {{
    color: {COLOR_TEXT_MAIN};
}}

QLineEdit {{
    background: #FFFFFF;
    border: 1px solid #CCCCCC;
    border-radius: 8px;
    padding: 6px 8px;
    font-size: 13px;
}}

QScrollArea {{
    border: none;
}}

QToolTip {{
    background-color: #111827;
    color: #F9FAFB;
    border: 1px solid #4B5563;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
}}
"""

# Card / panel style
panel_style = """
QFrame {
    background: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #E5E7EB;
}
"""

# Buttons
primary_button_style = f"""
QPushButton {{
    background: {COLOR_PRIMARY};
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton:disabled {{
    background: #D1D5DB;
    color: #9CA3AF;
}}
"""

secondary_button_style = f"""
QPushButton {{
    background: #FFFFFF;
    color: #FFFFFF;
    border: 1px solid #D1D5DB;
    border-radius: 10px;
    padding: 8px 16px;
    font-size: 13px;
}}
"""

small_button_style = f"""
QPushButton {{
    background: {COLOR_PRIMARY};
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 12px;
}}
"""

# Checkbox styles
def _base_checkbox_style() -> str:
    return """
QCheckBox {
    spacing: 4px;
    font-size: 13px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
}
QCheckBox::indicator:unchecked {
    border: 1px solid #9CA3AF;
    border-radius: 4px;
    background: #FFFFFF;
}
QCheckBox::indicator:checked {
    border: 1px solid #4B5563;
    border-radius: 4px;
    background: #4B5563;
}
"""

checkbox_style = _base_checkbox_style()
checkbox_allowed_style = checkbox_style.replace("#4B5563", COLOR_ALLOWED)
checkbox_blocked_style = checkbox_style.replace("#4B5563", COLOR_BLOCKED)
checkbox_neutral_style = checkbox_style.replace("#4B5563", COLOR_NEUTRAL)

# Overlay styles
overlay_window_stylesheet = f"""
QWidget {{
    background-color: {COLOR_OVERLAY_BG};
    color: {COLOR_TEXT_OVERLAY};
}}
QLabel {{
    color: {COLOR_TEXT_OVERLAY};
}}
"""

overlay_card_style = """
QFrame {
    background: #111827;
    border-radius: 16px;
    border: 1px solid #374151;
}
"""

overlay_button_style = primary_button_style


# Helper functions for applying styles to widgets

def style_primary_button(btn) -> None:
    btn.setStyleSheet(primary_button_style)


def style_secondary_button(btn) -> None:
    btn.setStyleSheet(secondary_button_style)


def style_small_button(btn) -> None:
    btn.setStyleSheet(small_button_style)
