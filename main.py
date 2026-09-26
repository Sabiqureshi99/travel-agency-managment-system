"""
Travel Agency Management System (TAMS)
Company: Hamza Travels & Tours
Entry Point

This is the main entry point for the TAMS application.
It initialises the QApplication, shows the splash screen,
performs startup checks (database connection, migrations),
and then launches the login window.
"""
import sys
import os
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so all imports work correctly
# regardless of how the script is invoked.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Fix for matplotlib PyInstaller NameError "name 'Qt' is not defined"
os.environ["QT_API"] = "PySide6"

# ---------------------------------------------------------------------------
# Load environment variables BEFORE importing anything else that needs them.
# ---------------------------------------------------------------------------
from dotenv import load_dotenv  # noqa: E402
load_dotenv(PROJECT_ROOT / ".env", override=False)

# ---------------------------------------------------------------------------
# Set up logging as early as possible so every subsequent import can log.
# ---------------------------------------------------------------------------
from utils.logger import setup_logging  # noqa: E402
setup_logging()

import logging  # noqa: E402
logger = logging.getLogger(__name__)

def global_exception_handler(exctype, value, tb):
    """Catch all unhandled exceptions, log them, and show an error dialogue."""
    from PySide6.QtWidgets import QMessageBox, QApplication
    
    # Format the traceback
    tb_text = "".join(traceback.format_exception(exctype, value, tb))
    
    # Log it
    logger.critical(f"UNHANDLED EXCEPTION:\n{tb_text}")
    
    # Save to error.log
    with open("error.log", "a", encoding="utf-8") as f:
        f.write(f"--- {import_datetime().now().isoformat()} ---\n")
        f.write(tb_text + "\n")
        
    # Show to user if Qt is running
    app = QApplication.instance()
    if app:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Critical Application Error")
        msg.setText(f"An unexpected error occurred:\n{value}")
        msg.setDetailedText(tb_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
        
def import_datetime():
    from datetime import datetime
    return datetime

sys.excepthook = global_exception_handler


def main() -> None:
    """Application entry point — bootstraps Qt and all subsystems."""
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont

    logger.info("=" * 60)
    logger.info("Starting Hamza Travels & Tours — TAMS v1.0.0")
    logger.info("=" * 60)

    # -----------------------------------------------------------------------
    # Create QApplication
    # -----------------------------------------------------------------------
    app = QApplication(sys.argv)
    app.setApplicationName("Hamza Travels & Tours")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Hamza Travels & Tours")
    app.setOrganizationDomain("hamzatravels.com")

    # High-DPI support (Qt6 handles this automatically — no explicit flag needed)
    # AA_UseHighDpiPixmaps is deprecated in Qt6; remove to silence DeprecationWarning

    # Default font
    default_font = QFont("Segoe UI", 10)
    app.setFont(default_font)

    # -----------------------------------------------------------------------
    # Show splash screen immediately
    # -----------------------------------------------------------------------
    from ui.windows.splash_screen import SplashScreen
    splash = SplashScreen()
    splash.show()
    app.processEvents()

    try:
        # -------------------------------------------------------------------
        # Initialise required directories
        # -------------------------------------------------------------------
        splash.set_status("Initialising directories...")
        app.processEvents()
        _ensure_directories()

        # -------------------------------------------------------------------
        # Initialise database (run migrations if needed)
        # -------------------------------------------------------------------
        splash.set_status("Connecting to database...")
        app.processEvents()
        from config.database import init_database
        db_ok = init_database()
        if not db_ok:
            raise RuntimeError(
                "Failed to connect to the database.\n"
                "Please check your database settings in the .env file."
            )

        # -------------------------------------------------------------------
        # Apply theme
        # -------------------------------------------------------------------
        splash.set_status("Loading theme...")
        app.processEvents()
        from ui.styles.theme import ThemeManager
        ThemeManager.apply(app)

        # -------------------------------------------------------------------
        # Show login window
        # -------------------------------------------------------------------
        splash.set_status("Ready!")
        app.processEvents()

        from ui.windows.login_window import LoginWindow
        from ui.windows.main_window import MainWindow

        login_window = LoginWindow()
        
        # We need to keep a reference to main_window to prevent garbage collection
        global_state = {"main_window": None}

        def on_login_success(user):
            login_window.close()
            main_window = MainWindow(user)
            global_state["main_window"] = main_window
            main_window.show()

        login_window.login_successful.connect(on_login_success)

        # Close splash and show login
        splash.finish(login_window)
        login_window.show()

        logger.info("Application launched successfully.")
        sys.exit(app.exec())

    except Exception as exc:  # pylint: disable=broad-except
        logger.critical("Fatal error during startup: %s", exc, exc_info=True)
        splash.close()
        QMessageBox.critical(
            None,
            "Startup Error",
            f"A fatal error occurred during startup:\n\n{exc}\n\n"
            "Please check the log file for details.",
        )
        sys.exit(1)


def _ensure_directories() -> None:
    """Create all required application directories if they do not exist."""
    dirs = [
        os.getenv("LOG_DIR", "logs"),
        os.getenv("BACKUP_DIR", "backups"),
        os.getenv("DOCUMENTS_DIR", "documents"),
        os.getenv("PHOTOS_DIR", "documents/photos"),
        os.getenv("TEMP_DIR", "temp"),
        os.getenv("REPORTS_OUTPUT_DIR", "reports/output"),
        "data",
    ]
    for directory in dirs:
        path = PROJECT_ROOT / directory
        path.mkdir(parents=True, exist_ok=True)
    logger.debug("Application directories verified.")


if __name__ == "__main__":
    main()
