"""
Desktop entry point for AI QA Platform.

Starts the FastAPI backend server in a background thread,
then launches the PySide6 desktop UI.
"""
import multiprocessing
import os
import sys
import threading
import uvicorn
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from frontend_pyqt.window import MainWindow


class ServerThread(threading.Thread):
    def __init__(self, port=8765):
        super().__init__(daemon=True)
        self.port = port

    def run(self):
        from backend.app import app
        uvicorn.run(app, host="127.0.0.1", port=self.port, log_level="warning")


def main():
    multiprocessing.freeze_support()
    port = int(os.getenv("PORT", "8765"))
    output_dir = os.getenv("OUTPUT_DIR", "")

    server = ServerThread(port)
    server.start()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    from frontend_pyqt.theme import DARK_THEME
    app.setStyleSheet(DARK_THEME)
    app.setApplicationName("AI QA Platform")

    window = MainWindow(output_dir=output_dir)
    window.show()

    exit_code = app.exec()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
