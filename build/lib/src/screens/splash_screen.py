from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QTimer
import src.theme as theme


class SplashScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self._setup_ui()
        QTimer.singleShot(1500, self._go_next)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        logo = QLabel("ZenFlow")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(
            f"font-size: 48px; font-weight: 700; color: {theme.COLOR_PRIMARY};"
        )

        glow = QWidget()
        glow.setFixedSize(260, 260)
        glow.setStyleSheet(
            "background-color: rgba(79,70,229,0.08);"
            "border-radius: 130px;"
        )

        inner = QVBoxLayout(glow)
        inner.addWidget(logo, 0, Qt.AlignCenter)

        layout.addWidget(glow)

        self.setStyleSheet(
            "background-color: #020617;"
        )

    def _go_next(self):
        if hasattr(self.parent, "show_intent_screen"):
            self.parent.show_intent_screen()
