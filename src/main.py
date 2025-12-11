import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon

from theme import apply_global_theme

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('zenflow.log')
    ]
)
logger = logging.getLogger(__name__)

try:
    # Import local modules
    from splash_screen import ZenFlowSplashScreen as SplashScreen
    from main_window import MainWindow
    from utils.config import AppConfig
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    raise

def main():
    # Initialize the application
    app = QApplication(sys.argv)
    app.setApplicationName("ZenFlow")

    # Apply global ZenFlow theme (Inter font + base palette)
    apply_global_theme(app)
    
    # Set application icon (handle missing icon gracefully)
    try:
        icon_path = os.path.join('assets', 'icons', 'zenflow.ico')
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        else:
            logger.warning(f"Icon not found at: {icon_path}")
    except Exception as e:
        logger.error(f"Error setting application icon: {e}")
    
    # Load configuration
    try:
        config = AppConfig()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        QMessageBox.critical(None, "Error", f"Failed to load configuration: {e}")
        return 1
    
    try:
        # Show splash screen
        splash = SplashScreen()
        splash.show()
        
        # Process events to make sure the splash screen is displayed
        app.processEvents()
        
        # Create main window but don't show it yet
        main_window = MainWindow(config)
        
        # Close splash screen and show main window after delay
        def show_main_window():
            try:
                splash.finish(main_window)
                main_window.show()
                logger.info("Main window displayed successfully")
            except Exception as e:
                logger.error(f"Error showing main window: {e}")
                QMessageBox.critical(None, "Error", f"Failed to show main window: {e}")
        
        # Use a single-shot timer to show the main window after the splash screen
        QTimer.singleShot(2000, show_main_window)
        
        # Start the application event loop
        return app.exec_()
        
    except Exception as e:
        logger.critical(f"Fatal error in main application: {e}", exc_info=True)
        QMessageBox.critical(None, "Fatal Error", 
                           f"A fatal error occurred: {str(e)}\n\nCheck zenflow.log for details.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        QMessageBox.critical(None, "Unexpected Error", 
                           f"An unexpected error occurred: {str(e)}\n\nCheck zenflow.log for details.")
        sys.exit(1)
