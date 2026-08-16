import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QTabWidget, QSplitter,
    QComboBox,
)
from PySide6.QtCore import Qt
import frontend_pyqt.api as api


class ManualTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Vertical)

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.addWidget(QLabel("<h3>Create Manual Test Suite</h3>"))

        inputs = QFormLayout()
        self.suite_name_input = QLineEdit()
        self.suite_name_input.setPlaceholderText("e.g., Login Page Tests")
        inputs.addRow("Suite Name:", self.suite_name_input)

        self.module_input = QLineEdit()
        self.module_input.setPlaceholderText("e.g., auth")
        inputs.addRow("Module:", self.module_input)

        self.feature_input = QLineEdit()
        self.feature_input.setPlaceholderText("e.g., User Authentication")
        inputs.addRow("Feature:", self.feature_input)

        self.source_input = QComboBox()
        self.source_input.addItems(["manual_entry", "excel_import", "test_plan"])
        inputs.addRow("Source:", self.source_input)

        self.tester_input = QLineEdit()
        self.tester_input.setPlaceholderText("Tester name (optional)")
        inputs.addRow("Tester:", self.tester_input)

        form_layout.addLayout(inputs)

        form_layout.addWidget(QLabel("Test Cases (one per line):"))
        self.cases_input = QTextEdit()
        self.cases_input.setPlaceholderText(
            "TC001 | Verify login page loads | 1. Navigate to /login | Page loads successfully | high | smoke\n"
            "TC002 | Login with valid credentials | 1. Enter email 2. Enter password 3. Click Sign In | User redirected to dashboard | critical | happy path\n\n"
            "Format: ID | Title | Steps | Expected Result | Priority | Type"
        )
        self.cases_input.setMinimumHeight(120)
        form_layout.addWidget(self.cases_input)

        import_layout = QHBoxLayout()
        excel_btn = QPushButton("Import from Excel")
        excel_btn.setObjectName("secondary")
        excel_btn.clicked.connect(self._import_excel)
        import_layout.addWidget(excel_btn)
        import_layout.addStretch()
        form_layout.addLayout(import_layout)

        create_btn = QPushButton("Create Suite")
        create_btn.clicked.connect(self._create_suite)
        form_layout.addWidget(create_btn)

        splitter.addWidget(form_widget)

        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.addWidget(QLabel("<h3>Existing Suites</h3>"))

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("secondary")
        refresh_btn.clicked.connect(self._refresh)
        list_layout.addWidget(refresh_btn)

        self.suite_table = QTableWidget()
        self.suite_table.setColumnCount(3)
        self.suite_table.setHorizontalHeaderLabels(["Name", "Module", "Feature"])
        self.suite_table.horizontalHeader().setStretchLastSection(True)
        self.suite_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.suite_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.suite_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.suite_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.suite_table.cellDoubleClicked.connect(self._open_suite)
        list_layout.addWidget(self.suite_table)

        splitter.addWidget(list_widget)
        layout.addWidget(splitter)

    def _import_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx *.csv)")
        if path:
            try:
                import pandas as pd
                df = pd.read_excel(path) if path.endswith(".xlsx") else pd.read_csv(path)
                lines = []
                for _, row in df.iterrows():
                    vals = [str(row.get(c, "")) for c in df.columns[:6]]
                    lines.append(" | ".join(vals))
                self.cases_input.setPlainText("\n".join(lines))
            except Exception as e:
                QMessageBox.critical(self, "Import Error", str(e))

    def _create_suite(self):
        lines = self.cases_input.toPlainText().strip().split("\n")
        cases = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4:
                cases.append({
                    "id": parts[0],
                    "title": parts[1],
                    "steps": parts[2],
                    "expected_result": parts[3],
                    "priority": parts[4] if len(parts) > 4 else "medium",
                    "type": parts[5] if len(parts) > 5 else "functional",
                })

        if not cases:
            QMessageBox.warning(self, "Warning", "No valid test cases found.")
            return

        payload = {
            "suite_name": self.suite_name_input.text() or "Untitled Suite",
            "module": self.module_input.text() or "general",
            "feature": self.feature_input.text() or "untitled",
            "source": self.source_input.currentText(),
            "tester": self.tester_input.text() or "",
            "test_cases": cases,
        }

        try:
            result = api.create_manual_tests(payload)
            QMessageBox.information(self, "Success", f"Suite created: {result.get('suite_name', '')}")
            self._refresh()
            self.cases_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _refresh(self):
        try:
            data = api.list_manual_tests()
            suites = data.get("suites", [])
            self.suite_table.setRowCount(len(suites))
            for i, suite in enumerate(suites):
                self.suite_table.setItem(i, 0, QTableWidgetItem(suite.get("suite_name", "")))
                self.suite_table.setItem(i, 1, QTableWidgetItem(suite.get("module", "")))
                self.suite_table.setItem(i, 2, QTableWidgetItem(suite.get("feature", "")))
                self.suite_table.setProperty(f"slug_{i}", suite.get("slug", ""))
        except Exception as e:
            self.suite_table.setRowCount(0)

    def _open_suite(self, row, col):
        slug = self.suite_table.property(f"slug_{row}")
        if not slug:
            return
        try:
            suite = api.get_manual_test(slug)
            cases = suite.get("test_cases", [])
            text = json.dumps(cases, indent=2)
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QPlainTextEdit
            d = QDialog(self)
            d.setWindowTitle(f"Suite: {suite.get('suite_name', slug)}")
            d.setMinimumSize(600, 400)
            l = QVBoxLayout(d)
            te = QPlainTextEdit()
            te.setReadOnly(True)
            te.setPlainText(text)
            te.setFont(__import__("PySide6.QtGui").QtGui.QFont("Consolas", 10))
            l.addWidget(te)
            d.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))



