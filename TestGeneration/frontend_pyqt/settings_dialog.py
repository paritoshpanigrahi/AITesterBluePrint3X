from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QComboBox, QLineEdit, QPushButton, QTabWidget, QWidget,
    QMessageBox, QFileDialog, QGroupBox, QScrollArea,
)
from PySide6.QtCore import Qt
import frontend_pyqt.api as api

PROVIDERS = {
    "openai": "OpenAI",
    "anthropic": "Anthropic Claude",
    "google": "Google Gemini",
    "groq": "Groq",
    "ollama": "Ollama (Local)",
    "github-copilot": "VS Code GitHub Copilot",
}

PROVIDER_KEYS = {
    "openai": "openaiApiKey",
    "anthropic": "anthropicApiKey",
    "google": "googleApiKey",
    "groq": "groqApiKey",
    "ollama": None,
    "github-copilot": None,
}


class SettingsDialog(QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.settings = dict(current_settings)
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        self._build_ui()
        self._populate()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        layout.addWidget(tabs)

        tabs.addTab(self._build_llm_tab(), "LLM Provider")
        tabs.addTab(self._build_output_tab(), "Output")
        tabs.addTab(self._build_atlassian_tab(), "Jira & Confluence")

        btns = QHBoxLayout()
        btns.addStretch()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        btns.addWidget(save_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

    def _build_llm_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        w = QWidget()
        layout = QVBoxLayout(w)

        prov_group = QGroupBox("Provider")
        prov_layout = QFormLayout()
        self.provider_combo = QComboBox()
        for k, v in PROVIDERS.items():
            self.provider_combo.addItem(v, k)
        prov_layout.addRow("Provider:", self.provider_combo)
        prov_group.setLayout(prov_layout)
        layout.addWidget(prov_group)

        keys_group = QGroupBox("API Keys")
        keys_layout = QFormLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        keys_layout.addRow("API Key:", self.api_key_input)
        self.anthropic_key_input = QLineEdit()
        self.anthropic_key_input.setEchoMode(QLineEdit.Password)
        keys_layout.addRow("Anthropic Key:", self.anthropic_key_input)
        self.google_key_input = QLineEdit()
        self.google_key_input.setEchoMode(QLineEdit.Password)
        keys_layout.addRow("Google Key:", self.google_key_input)
        self.groq_key_input = QLineEdit()
        self.groq_key_input.setEchoMode(QLineEdit.Password)
        keys_layout.addRow("Groq Key:", self.groq_key_input)
        self.ollama_url_input = QLineEdit()
        keys_layout.addRow("Ollama Base URL:", self.ollama_url_input)
        self.github_token_input = QLineEdit()
        self.github_token_input.setEchoMode(QLineEdit.Password)
        keys_layout.addRow("GitHub Token:", self.github_token_input)
        keys_group.setLayout(keys_layout)
        layout.addWidget(keys_group)

        model_group = QGroupBox("Model")
        model_layout = QFormLayout()
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        model_layout.addRow("Model:", self.model_combo)
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        layout.addStretch()

        scroll.setWidget(w)
        return scroll

    def _build_output_tab(self):
        w = QWidget()
        layout = QFormLayout(w)
        self.output_dir_input = QLineEdit()
        output_btn_layout = QHBoxLayout()
        output_btn_layout.addWidget(self.output_dir_input)
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("secondary")
        browse_btn.clicked.connect(self._browse_output)
        output_btn_layout.addWidget(browse_btn)
        layout.addRow("Output Directory:", output_btn_layout)
        return w

    def _build_atlassian_tab(self):
        w = QWidget()
        layout = QFormLayout(w)
        self.jira_url_input = QLineEdit()
        layout.addRow("Jira URL:", self.jira_url_input)
        self.jira_email_input = QLineEdit()
        layout.addRow("Jira Email:", self.jira_email_input)
        self.jira_token_input = QLineEdit()
        self.jira_token_input.setEchoMode(QLineEdit.Password)
        layout.addRow("Jira API Token:", self.jira_token_input)
        self.confluence_url_input = QLineEdit()
        layout.addRow("Confluence URL:", self.confluence_url_input)
        self.confluence_email_input = QLineEdit()
        layout.addRow("Confluence Email:", self.confluence_email_input)
        self.confluence_token_input = QLineEdit()
        self.confluence_token_input.setEchoMode(QLineEdit.Password)
        layout.addRow("Confluence API Token:", self.confluence_token_input)
        test_btn = QPushButton("Test Credentials")
        test_btn.setObjectName("secondary")
        test_btn.clicked.connect(self._test_creds)
        layout.addRow("", test_btn)
        return w

    def _populate(self):
        idx = self.provider_combo.findData(self.settings.get("llmProvider", "openai"))
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)
        self.api_key_input.setText(self.settings.get("openaiApiKey", ""))
        self.anthropic_key_input.setText(self.settings.get("anthropicApiKey", ""))
        self.google_key_input.setText(self.settings.get("googleApiKey", ""))
        self.groq_key_input.setText(self.settings.get("groqApiKey", ""))
        self.ollama_url_input.setText(self.settings.get("ollamaBaseUrl", "http://localhost:11434"))
        self.github_token_input.setText(self.settings.get("githubCopilotToken", ""))
        self.output_dir_input.setText(self.settings.get("outputDir", ""))
        self.jira_url_input.setText(self.settings.get("jiraUrl", ""))
        self.jira_email_input.setText(self.settings.get("jiraEmail", ""))
        self.jira_token_input.setText(self.settings.get("jiraApiToken", ""))
        self.confluence_url_input.setText(self.settings.get("confluenceUrl", ""))
        self.confluence_email_input.setText(self.settings.get("confluenceEmail", ""))
        self.confluence_token_input.setText(self.settings.get("confluenceApiToken", ""))
        self.model_combo.addItem(self.settings.get("llmModel", "gpt-4o"))

    def _browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.output_dir_input.setText(folder)

    def _save(self):
        self.settings["llmProvider"] = self.provider_combo.currentData()
        self.settings["llmModel"] = self.model_combo.currentText()
        self.settings["openaiApiKey"] = self.api_key_input.text()
        self.settings["anthropicApiKey"] = self.anthropic_key_input.text()
        self.settings["googleApiKey"] = self.google_key_input.text()
        self.settings["groqApiKey"] = self.groq_key_input.text()
        self.settings["ollamaBaseUrl"] = self.ollama_url_input.text()
        self.settings["githubCopilotToken"] = self.github_token_input.text()
        self.settings["outputDir"] = self.output_dir_input.text()
        self.settings["jiraUrl"] = self.jira_url_input.text()
        self.settings["jiraEmail"] = self.jira_email_input.text()
        self.settings["jiraApiToken"] = self.jira_token_input.text()
        self.settings["confluenceUrl"] = self.confluence_url_input.text()
        self.settings["confluenceEmail"] = self.confluence_email_input.text()
        self.settings["confluenceApiToken"] = self.confluence_token_input.text()
        self.accept()

    def _test_creds(self):
        try:
            result = api.test_atlassian_credentials()
            parts = []
            for k, v in result.items():
                status = "OK" if v.get("success") else f"FAIL: {v.get('error', 'unknown')}"
                parts.append(f"{k}: {status}")
            QMessageBox.information(self, "Credential Test", "\n".join(parts))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
