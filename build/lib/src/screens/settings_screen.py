from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QListWidget, QListWidgetItem, QGroupBox, QSpinBox, QCheckBox
)
from PyQt5.QtCore import Qt
import src.theme as theme


class SettingsScreen(QWidget):
    def __init__(self, parent=None, state=None):
        super().__init__(parent)
        self.parent = parent
        self.state = state or {}
        self.prefs = self.state.get("userPreferences", {})
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Settings")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: 600; color: {theme.COLOR_TEXT_MAIN};"
        )

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        v_layout = QVBoxLayout(container)
        v_layout.setSpacing(16)

        # Session duration
        session_group = QGroupBox("Session Settings")
        session_layout = QVBoxLayout(session_group)
        
        dur_row = QHBoxLayout()
        dur_label = QLabel("Default session duration (minutes)")
        dur_spin = QSpinBox()
        dur_spin.setRange(5, 180)
        dur_spin.setValue(int(self.prefs.get("defaultSessionMinutes", 50)))
        dur_spin.valueChanged.connect(self._on_duration_changed)
        dur_row.addWidget(dur_label)
        dur_row.addWidget(dur_spin)
        dur_row.addStretch()
        session_layout.addLayout(dur_row)

        # Health reminders
        health_group = QGroupBox("Health Reminders")
        health_layout = QVBoxLayout(health_group)
        
        from PyQt5.QtWidgets import QCheckBox
        posture_check = QCheckBox("Posture reminders")
        posture_check.setChecked(self.prefs.get("postureTips", True))
        posture_check.stateChanged.connect(self._on_posture_changed)
        health_layout.addWidget(posture_check)
        
        eye_check = QCheckBox("Eye strain reminders")
        eye_check.setChecked(self.prefs.get("eyeStrainReminders", True))
        eye_check.stateChanged.connect(self._on_eye_strain_changed)
        health_layout.addWidget(eye_check)

        # Session history
        history_group = QGroupBox("Data Management")
        history_layout = QVBoxLayout(history_group)
        
        clear_btn = QPushButton("Clear all session history")
        clear_btn.setStyleSheet(
            "QPushButton {background:#000000;color:white;border:none;border-radius:8px;"
            "font-size:14px;font-weight:500;padding:10px 16px;}"
        )
        clear_btn.clicked.connect(self._clear_history)
        history_layout.addWidget(clear_btn)

        # Website blocking settings
        web_group = QGroupBox("Website Blocking")
        web_layout = QVBoxLayout(web_group)
        
        allowed_label = QLabel("Allowed domains for this session")
        allowed_label.setStyleSheet("color:#6b7280;font-size:12px;")
        web_layout.addWidget(allowed_label)
        
        blocked_label = QLabel("Blocked domains for this session")
        blocked_label.setStyleSheet("color:#6b7280;font-size:12px;")
        web_layout.addWidget(blocked_label)

        v_layout.addWidget(session_group)
        v_layout.addWidget(health_group)
        v_layout.addWidget(history_group)
        v_layout.addWidget(web_group)
        v_layout.addStretch()

        scroll.setWidget(container)

        # Back button
        back_btn = QPushButton("Back to Dashboard")
        back_btn.setFixedSize(180, 44)
        back_btn.setStyleSheet(
            "QPushButton {background:#6E260E;color:white;border:none;border-radius:8px;"
            "font-size:14px;font-weight:500;padding:8px 16px;}"
        )
        back_btn.clicked.connect(self._go_back)

        layout.addWidget(title)
        layout.addWidget(scroll, 1)
        layout.addWidget(back_btn)

    def _on_duration_changed(self, value):
        self.prefs["defaultSessionMinutes"] = int(value)
        self.state["userPreferences"] = self.prefs
        if hasattr(self.parent, "save_state"):
            self.parent.save_state(self.state)

    def _on_posture_changed(self, state):
        self.prefs["postureTips"] = state == Qt.Checked
        self.state["userPreferences"] = self.prefs
        if hasattr(self.parent, "save_state"):
            self.parent.save_state(self.state)

    def _on_eye_strain_changed(self, state):
        self.prefs["eyeStrainReminders"] = state == Qt.Checked
        self.state["userPreferences"] = self.prefs
        if hasattr(self.parent, "save_state"):
            self.parent.save_state(self.state)

    def _clear_history(self):
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "Clear History", 
            "Are you sure you want to clear all session history?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.state["sessionHistory"] = []
            if hasattr(self.parent, "save_state"):
                self.parent.save_state(self.state)

    def _go_back(self):
        if hasattr(self.parent, "show_dashboard"):
            self.parent.show_dashboard()
