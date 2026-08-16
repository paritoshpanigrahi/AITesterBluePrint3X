import os, json
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QLabel, QStatusBar, QMessageBox,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction

from frontend_pyqt.generate_tab import GenerateTab
from frontend_pyqt.registry_tab import RegistryTab
from frontend_pyqt.manual_tab import ManualTab
from frontend_pyqt.settings_dialog import SettingsDialog
import frontend_pyqt.api as api


class MainWindow(QMainWindow):
    def __init__(self, output_dir=""):
        super().__init__()
        self.settings = {
            "llmProvider": "openai",
            "llmModel": "gpt-4o",
            "openaiApiKey": "",
            "anthropicApiKey": "",
            "googleApiKey": "",
            "groqApiKey": "",
            "ollamaBaseUrl": "http://localhost:11434",
            "githubCopilotToken": "",
            "outputDir": output_dir,
            "jiraUrl": "",
            "jiraEmail": "",
            "jiraApiToken": "",
            "confluenceUrl": "",
            "confluenceEmail": "",
            "confluenceApiToken": "",
        }
        self.setWindowTitle("AI QA Platform")
        self.setMinimumSize(1200, 800)
        self._build_ui()
        self._setup_menu()
        self._start_backend_poll()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.main_tabs = QTabWidget()
        layout.addWidget(self.main_tabs)

        self.automation_tab = QWidget()
        auto_layout = QVBoxLayout(self.automation_tab)

        self.sub_tabs = QTabWidget()
        auto_layout.addWidget(self.sub_tabs)

        self.fresh_tab = GenerateTab("fresh", "Fresh Generate")
        self.sub_tabs.addTab(self.fresh_tab, "Fresh Generate")

        self.add_tab = GenerateTab("add", "Add Feature", requires_feature_name=True)
        self.sub_tabs.addTab(self.add_tab, "Add Feature")

        self.modify_tab = GenerateTab("modify", "Modify Tests", requires_test_file_name=True)
        self.sub_tabs.addTab(self.modify_tab, "Modify Tests")

        self.registry_tab = RegistryTab()
        self.sub_tabs.addTab(self.registry_tab, "Test Registry")

        self.main_tabs.addTab(self.automation_tab, "Automation Tests")

        self.manual_tab = ManualTab()
        self.main_tabs.addTab(self.manual_tab, "Manual Tests")

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Initializing backend...")
        self.status_bar.addWidget(self.status_label)

        self.restart_btn = QPushButton("Restart AI Engine")
        self.restart_btn.setObjectName("secondary")
        self.restart_btn.clicked.connect(self._restart_backend)
        self.restart_btn.hide()
        self.status_bar.addPermanentWidget(self.restart_btn)

    def _setup_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        settings_action = QAction("Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)
        file_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _open_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.settings = dialog.settings
            self._on_settings_saved()

    def _on_settings_saved(self):
        output_dir = self.settings.get("outputDir", "")
        self.fresh_tab.set_output_path(output_dir)
        self.add_tab.set_output_path(output_dir)
        self.modify_tab.set_output_path(output_dir)
        try:
            if output_dir:
                api.update_config(output_dir)
        except Exception:
            pass

    def _start_backend_poll(self):
        self._poll_count = 0
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._poll_backend)
        self._poll_timer.start(500)

    def _poll_backend(self):
        self._poll_count += 1
        try:
            h = api.get_health()
            if h.get("status") == "ok":
                self._poll_timer.stop()
                self.status_label.setText("Backend ready")
                self.restart_btn.hide()
                self._on_settings_saved()
                return
        except Exception:
            pass
        if self._poll_count >= 60:
            self._poll_timer.stop()
            self.status_label.setText("Backend not available")
            self.restart_btn.show()

    def _restart_backend(self):
        self.status_label.setText("Restarting AI engine...")
        try:
            api.update_config(self.settings.get("outputDir", ""))
        except Exception:
            pass
        self._poll_count = 0
        self._start_backend_poll()

    def _show_about(self):
        QMessageBox.about(self, "About AI QA Platform",
            "AI QA Platform v1.0.0\n\n"
            "Automated test generation and execution platform powered by AI.\n\n"
            "Built with PySide6 and Python."
        )
