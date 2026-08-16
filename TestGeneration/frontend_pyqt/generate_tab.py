import json
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QComboBox, QTabWidget,
    QGroupBox, QScrollArea, QFileDialog, QMessageBox, QProgressDialog,
    QDialog, QRadioButton, QFrame,
)
from PySide6.QtCore import Qt, QThread, Signal
import frontend_pyqt.api as api


class GenerateWorker(QThread):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, fn, payload):
        super().__init__()
        self.fn = fn
        self.payload = payload

    def run(self):
        try:
            result = self.fn(self.payload)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class GenerateTab(QWidget):
    def __init__(self, mode, title, requires_feature_name=False, requires_test_file_name=False):
        super().__init__()
        self.mode = mode
        self.tab_title = title
        self.requires_feature_name = requires_feature_name
        self.requires_test_file_name = requires_test_file_name
        self.result_data = None
        self.last_payload = None
        self.pending_actions = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)

        title_lbl = QLabel(f"<h2>{self.tab_title}</h2>")
        form_layout.addWidget(title_lbl)

        grid = QWidget()
        grid_layout = QFormLayout(grid)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        grid_layout.addRow("Application URL:", self.url_input)

        if self.requires_feature_name:
            self.feature_name_input = QLineEdit()
            self.feature_name_input.setPlaceholderText("e.g., User Authentication")
            grid_layout.addRow("Feature Name *:", self.feature_name_input)

        if self.requires_test_file_name:
            self.test_file_name_input = QLineEdit()
            self.test_file_name_input.setPlaceholderText("e.g., auth.spec.ts")
            grid_layout.addRow("Test File Name *:", self.test_file_name_input)

        self.requirement_input = QTextEdit()
        self.requirement_input.setPlaceholderText(
            "Paste requirements, user stories, or test steps here...\n\n"
            "Examples:\n"
            "- Raw steps: 1. Navigate to login page | 2. Enter email | 3. Click Sign In\n"
            "- User story: As a user, I want to log in so that I can access my dashboard\n"
            "- Requirements: The login page should have email, password fields and a Sign In button"
        )
        self.requirement_input.setMinimumHeight(150)
        grid_layout.addRow("Requirement / Steps:", self.requirement_input)

        self.prd_path = ""
        prd_btn_layout = QHBoxLayout()
        self.prd_label = QLabel("No file selected")
        prd_btn = QPushButton("Browse")
        prd_btn.setObjectName("secondary")
        prd_btn.clicked.connect(lambda: self._browse_file("prd"))
        prd_btn_layout.addWidget(self.prd_label)
        prd_btn_layout.addWidget(prd_btn)
        grid_layout.addRow("PRD File:", prd_btn_layout)

        self.manual_test_path = ""
        mt_btn_layout = QHBoxLayout()
        self.mt_label = QLabel("No file selected")
        mt_btn = QPushButton("Browse")
        mt_btn.setObjectName("secondary")
        mt_btn.clicked.connect(lambda: self._browse_file("manual_tests"))
        mt_btn_layout.addWidget(self.mt_label)
        mt_btn_layout.addWidget(mt_btn)
        grid_layout.addRow("Manual Test Cases:", mt_btn_layout)

        self.openapi_path = ""
        oa_btn_layout = QHBoxLayout()
        self.oa_label = QLabel("No file selected")
        oa_btn = QPushButton("Browse")
        oa_btn.setObjectName("secondary")
        oa_btn.clicked.connect(lambda: self._browse_file("openapi"))
        oa_btn_layout.addWidget(self.oa_label)
        oa_btn_layout.addWidget(oa_btn)
        grid_layout.addRow("OpenAPI Spec:", oa_btn_layout)

        self.env_path = ""
        env_btn_layout = QHBoxLayout()
        self.env_label = QLabel("No file selected")
        env_btn = QPushButton("Browse")
        env_btn.setObjectName("secondary")
        env_btn.clicked.connect(lambda: self._browse_file("env"))
        env_btn_layout.addWidget(self.env_label)
        env_btn_layout.addWidget(env_btn)
        grid_layout.addRow(".env File:", env_btn_layout)

        self.confluence_url_input = QLineEdit()
        self.confluence_url_input.setPlaceholderText("https://confluence.company.com/...")
        grid_layout.addRow("Confluence URL:", self.confluence_url_input)

        self.jira_ticket_input = QLineEdit()
        self.jira_ticket_input.setPlaceholderText("PROJ-123")
        grid_layout.addRow("Jira Ticket ID:", self.jira_ticket_input)

        self.jira_sprint_input = QLineEdit()
        self.jira_sprint_input.setPlaceholderText("123")
        grid_layout.addRow("Jira Sprint ID:", self.jira_sprint_input)

        self.jira_project_input = QLineEdit()
        self.jira_project_input.setPlaceholderText("PROJ")
        grid_layout.addRow("Jira Project Key:", self.jira_project_input)

        codebase_layout = QHBoxLayout()
        self.codebase_input = QLineEdit()
        self.codebase_input.setPlaceholderText("C:\\project")
        codebase_browse = QPushButton("Browse")
        codebase_browse.setObjectName("secondary")
        codebase_browse.clicked.connect(self._browse_codebase)
        codebase_layout.addWidget(self.codebase_input)
        codebase_layout.addWidget(codebase_browse)
        grid_layout.addRow("Codebase Path:", codebase_layout)

        self.output_path_label = QLabel("Not configured")
        self.output_path_label.setStyleSheet("color: #a6adc8;")
        grid_layout.addRow("Output Path:", self.output_path_label)

        form_layout.addWidget(grid)

        btn_layout = QHBoxLayout()
        self.preview_ctx_btn = QPushButton("Preview Context")
        self.preview_ctx_btn.setObjectName("secondary")
        self.preview_ctx_btn.clicked.connect(self._preview_context)
        btn_layout.addWidget(self.preview_ctx_btn)
        self.preview_plan_btn = QPushButton("Preview Plan")
        self.preview_plan_btn.setObjectName("secondary")
        self.preview_plan_btn.clicked.connect(self._preview_plan)
        btn_layout.addWidget(self.preview_plan_btn)
        self.generate_btn = QPushButton("Fresh Generate" if self.mode == "fresh" else "Add Feature" if self.mode == "add" else "Modify Tests")
        self.generate_btn.clicked.connect(self._generate)
        btn_layout.addWidget(self.generate_btn)
        form_layout.addLayout(btn_layout)

        self.error_label = QLabel()
        self.error_label.setObjectName("errorLabel")
        self.error_label.setStyleSheet("color: #ef4444;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        form_layout.addWidget(self.error_label)

        form_layout.addStretch()
        scroll.setWidget(form_widget)
        layout.addWidget(scroll)

        self.result_tabs = QTabWidget()
        self.result_tabs.hide()
        layout.addWidget(self.result_tabs)

    def set_output_path(self, path):
        self.output_path_label.setText(path or "Not configured")

    def _browse_file(self, kind):
        filters = {
            "prd": "Documents (*.pdf *.docx *.txt *.md *.xlsx *.csv)",
            "manual_tests": "Excel/CSV (*.xlsx *.csv)",
            "openapi": "YAML/JSON (*.yaml *.json)",
            "env": "Env files (*.env)",
        }
        path, _ = QFileDialog.getOpenFileName(self, "Select File", "", filters.get(kind, "All Files (*)"))
        if path:
            setattr(self, f"{kind}_path", path)
            label = getattr(self, f"{kind.replace('_', '')}_label" if kind != "manual_tests" else "mt_label")
            label.setText(os.path.basename(path))

    def _browse_codebase(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Codebase Directory")
        if folder:
            self.codebase_input.setText(folder)

    def _build_payload(self):
        payload = {}
        if self.url_input.text():
            payload["url"] = self.url_input.text()
        if self.requirement_input.toPlainText():
            payload["requirement"] = self.requirement_input.toPlainText()
        if self.confluence_url_input.text():
            payload["confluence_url"] = self.confluence_url_input.text()
        if self.jira_ticket_input.text():
            payload["jira_ticket_id"] = self.jira_ticket_input.text()
        if self.jira_sprint_input.text():
            payload["jira_sprint_id"] = self.jira_sprint_input.text()
        if self.jira_project_input.text():
            payload["jira_project_key"] = self.jira_project_input.text()
        if self.codebase_input.text():
            payload["codebase_path"] = self.codebase_input.text()
        return payload

    def _show_error(self, msg):
        self.error_label.setText(msg)
        self.error_label.show()

    def _clear_error(self):
        self.error_label.hide()

    def _set_buttons_enabled(self, enabled):
        self.preview_ctx_btn.setEnabled(enabled)
        self.preview_plan_btn.setEnabled(enabled)
        self.generate_btn.setEnabled(enabled)

    def _preview_context(self):
        self._clear_error()
        self._set_buttons_enabled(False)
        self.result_tabs.hide()
        self.worker = GenerateWorker(api.ingest_context, self._build_payload())
        self.worker.finished.connect(self._on_preview_done)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_preview_done(self, result):
        self._set_buttons_enabled(True)
        self._show_result_tab("Context Preview", json.dumps(result, indent=2))

    def _preview_plan(self):
        self._clear_error()
        self._set_buttons_enabled(False)
        self.result_tabs.hide()
        self.worker = GenerateWorker(api.preview_plan, self._build_payload())
        self.worker.finished.connect(self._on_plan_done)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_plan_done(self, result):
        self._set_buttons_enabled(True)
        plan = result.get("plan", result)
        self._show_result_tab("Test Plan", json.dumps(plan, indent=2))

    def _generate(self):
        self._clear_error()
        self._set_buttons_enabled(False)
        self.result_tabs.hide()
        payload = self._build_payload()
        self.last_payload = payload

        if self.mode == "add":
            payload["feature_name"] = getattr(self, "feature_name_input", None).text() if hasattr(self, "feature_name_input") else ""
            fn = api.add_feature
        elif self.mode == "modify":
            payload["test_file_name"] = getattr(self, "test_file_name_input", None).text() if hasattr(self, "test_file_name_input") else ""
            fn = api.modify_tests
        else:
            fn = api.generate_tests

        self.worker = GenerateWorker(fn, payload)
        self.worker.finished.connect(self._on_generate_done)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_generate_done(self, result):
        self._set_buttons_enabled(True)
        self.result_data = result

        dup = result.get("duplicate_result", {})
        if dup.get("has_duplicates") and dup.get("pending_actions"):
            self.pending_actions = list(dup["pending_actions"])
            self._show_duplicate_dialog()
            return

        self._show_result(result)

    def _show_duplicate_dialog(self):
        dialog = DuplicateDialog(self.pending_actions, self)
        if dialog.exec():
            actions = dialog.get_resolved_actions()
            payload = dict(self.last_payload)
            payload["scenario_actions"] = actions
            self._set_buttons_enabled(False)

            if self.mode == "add":
                fn = api.add_feature
            elif self.mode == "modify":
                fn = api.modify_tests
            else:
                fn = api.generate_tests

            self.worker = GenerateWorker(fn, payload)
            self.worker.finished.connect(self._show_result)
            self.worker.error.connect(self._on_error)
            self.worker.start()

    def _show_result(self, result):
        self.result_tabs.clear()
        self.result_tabs.show()

        locators = result.get("locators", {})
        scenarios = result.get("scenarios", [])
        test_code = result.get("test_code", result.get("test_file_path", ""))
        execution = result.get("execution_result", {})
        org = result.get("organization", {})
        test_plan = result.get("test_plan", {})

        if locators:
            self._add_text_tab("Locators", json.dumps(locators, indent=2))
        if scenarios:
            self._add_text_tab("Scenarios", json.dumps(scenarios, indent=2))
        if test_plan:
            self._add_text_tab("Test Plan", json.dumps(test_plan, indent=2))
            self._add_download_plan_button(test_plan, result)
        self._add_text_tab("Test Code", str(test_code))
        if execution:
            self._add_text_tab("Execution", json.dumps(execution, indent=2))

        info = QWidget()
        info_layout = QVBoxLayout(info)
        status = result.get("status", "")
        msg = result.get("message", "")
        if status:
            info_layout.addWidget(QLabel(f"Status: {status}"))
        if msg:
            info_layout.addWidget(QLabel(f"Message: {msg}"))
        if result.get("test_file_path"):
            info_layout.addWidget(QLabel(f"File: {result['test_file_path']}"))
        if result.get("project_scaffold", {}).get("scaffolded"):
            info_layout.addWidget(QLabel(f"Playwright project initialized: {result['project_scaffold'].get('message', '')}"))
        info_layout.addStretch()
        self.result_tabs.addTab(info, "Info")

    def _add_download_plan_button(self, test_plan, result):
        from PySide6.QtWidgets import QPushButton, QHBoxLayout
        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.addStretch()
        download_btn = QPushButton("Download Test Plan (.md)")
        download_btn.setObjectName("secondary")
        download_btn.clicked.connect(lambda: self._download_test_plan(test_plan, result))
        btn_layout.addWidget(download_btn)
        btn_layout.addStretch()
        idx = self.result_tabs.count() - 1
        self.result_tabs.insertTab(idx, btn_widget, "Plan Actions")

    def _download_test_plan(self, test_plan, result):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        default_name = f"{result.get('organization', {}).get('module', 'test-plan')}_test_plan.md"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Test Plan", default_name, "Markdown Files (*.md)"
        )
        if not save_path:
            return
        try:
            feature_name = result.get("organization", {}).get("module", "test-plan")
            resp = api.export_test_plan(test_plan, feature_name)
            filename = resp.get("filename", default_name)
            save_dir = os.path.dirname(save_path)
            api.download_plan(filename, save_path)
            QMessageBox.information(self, "Saved", f"Test plan saved to:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save test plan:\n{str(e)}")

    def _add_text_tab(self, title, text):
        from PySide6.QtWidgets import QPlainTextEdit
        editor = QPlainTextEdit()
        editor.setReadOnly(True)
        editor.setPlainText(text)
        editor.setFont(__import__("PySide6.QtGui").QtGui.QFont("Consolas", 10))
        self.result_tabs.addTab(editor, title)

    def _show_result_tab(self, title, text):
        self.result_tabs.clear()
        self.result_tabs.show()
        self._add_text_tab(title, text)

    def _on_error(self, msg):
        self._set_buttons_enabled(True)
        self._show_error(msg)


class DuplicateDialog(QDialog):
    def __init__(self, pending_actions, parent=None):
        super().__init__(parent)
        self.pending_actions = pending_actions
        self.radio_groups = []
        self.setWindowTitle("Duplicate Scenarios Found")
        self.setMinimumWidth(500)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Choose how to handle each duplicate:"))

        for item in self.pending_actions:
            frame = QFrame()
            frame.setFrameStyle(QFrame.StyledPanel)
            fl = QVBoxLayout(frame)
            fl.addWidget(QLabel(
                f"<b>New:</b> {item.get('scenario_name', '')}<br>"
                f"<b>Existing:</b> {item.get('existing_name', '')}<br>"
                f"<b>Similarity:</b> {item.get('name_similarity', 0) * 100:.0f}%"
            ))

            radio_layout = QHBoxLayout()
            skip_rb = QRadioButton("Skip (keep existing)")
            skip_rb.setChecked(item.get("action", "skip") == "skip")
            override_rb = QRadioButton("Override (replace)")
            override_rb.setChecked(item.get("action") == "override")
            remove_rb = QRadioButton("Remove (delete existing)")
            remove_rb.setChecked(item.get("action") == "remove")
            radio_layout.addWidget(skip_rb)
            radio_layout.addWidget(override_rb)
            radio_layout.addWidget(remove_rb)
            fl.addLayout(radio_layout)
            layout.addWidget(frame)
            self.radio_groups.append((skip_rb, override_rb, remove_rb))

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        apply_btn = QPushButton("Apply & Regenerate")
        apply_btn.clicked.connect(self.accept)
        btn_layout.addWidget(apply_btn)
        layout.addLayout(btn_layout)

    def get_resolved_actions(self):
        actions = []
        for i, item in enumerate(self.pending_actions):
            skip, override, remove = self.radio_groups[i]
            action = "skip"
            if override.isChecked():
                action = "override"
            elif remove.isChecked():
                action = "remove"
            actions.append({
                "name": item.get("scenario_name", ""),
                "existing_name": item.get("existing_name", ""),
                "action": action,
            })
        return actions
