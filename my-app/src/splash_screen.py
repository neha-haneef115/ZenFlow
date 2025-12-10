from PyQt5.QtWidgets import QSplashScreen, QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QFontMetrics, QLinearGradient, QBrush
import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ZenFlowSplashScreen(QSplashScreen):
    def __init__(self):
        # Create a simple white pixmap
        pixmap = QPixmap(400, 200)
        pixmap.fill(Qt.white)
        
        super().__init__(pixmap)
        
        # Set window flags for frameless and always on top
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.SplashScreen)
        
        # Set the size and position
        self.setFixedSize(400, 200)
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.center() - self.rect().center())
        
        # Set up the timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.close)
        self.timer.start(2000)  # Close after 2 seconds
        
        # Show the splash screen
        self.show()
        
    def drawContents(self, painter):
        """Draw the splash screen with app name and version."""
        # Set up painter
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.setBrush(Qt.white)
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())
        
        # Draw border
        painter.setPen(QColor(200, 200, 200))
        painter.drawRect(0, 0, self.width()-1, self.height()-1)
        
        # Draw app name
        painter.setPen(QColor(60, 60, 80))
        font = QFont("Arial", 28, QFont.Bold)
        painter.setFont(font)
        
        app_name = "ZenFlow"
        fm = QFontMetrics(font)
        text_width = fm.width(app_name)
        
        painter.drawText(
            (self.width() - text_width) // 2, 
            self.height() // 2 - 20, 
            app_name
        )
        
        # Draw tagline
        tagline_font = QFont("Arial", 10)
        painter.setFont(tagline_font)
        painter.setPen(QColor(100, 100, 120))
        
        tagline = "Flow without distraction"
        tagline_width = QFontMetrics(tagline_font).width(tagline)
        
        painter.drawText(
            (self.width() - tagline_width) // 2,
            self.height() // 2 + 20,
            tagline
        )
        
        # Draw version
        version = "v1.0.0"
        version_font = QFont("Arial", 8)
        painter.setFont(version_font)
        painter.setPen(QColor(150, 150, 170))
        
        version_width = QFontMetrics(version_font).width(version)
        painter.drawText(
            (self.width() - version_width) // 2,
            self.height() - 30,
            version
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = ZenFlowSplashScreen()
    splash.show()
    sys.exit(app.exec_())
