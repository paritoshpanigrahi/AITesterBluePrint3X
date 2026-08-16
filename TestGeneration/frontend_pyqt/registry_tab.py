from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QHeaderView, QMessageBox, QLabel,
)
from PySide6.QtCore import Qt
import frontend_pyqt.api as api


class RegistryTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        header.addWidget(QLabel("<h3>Test Registry</h3>"))
        header.addStretch()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("secondary")
        refresh_btn.clicked.connect(self._refresh)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "Feature", "Test File", "URL", "Actions"])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def _refresh(self):
        try:
            data = api.get_registry()
            entries = data.get("entries", [])
            self.table.setRowCount(len(entries))
            for i, entry in enumerate(entries):
                self.table.setItem(i, 0, QTableWidgetItem(entry.get("name", "")))
                self.table.setItem(i, 1, QTableWidgetItem(entry.get("feature_name", "")))
                self.table.setItem(i, 2, QTableWidgetItem(entry.get("test_file", "")))
                self.table.setItem(i, 3, QTableWidgetItem(entry.get("url", "")))

                delete_btn = QPushButton("Delete")
                delete_btn.setObjectName("danger")
                entry_id = entry.get("id", "")
                delete_btn.clicked.connect(lambda checked, eid=entry_id: self._delete(eid))
                self.table.setCellWidget(i, 4, delete_btn)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load registry: {e}")

    def _delete(self, entry_id):
        reply = QMessageBox.question(self, "Confirm", "Delete this registry entry?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                api.delete_registry_entry(entry_id)
                self._refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
