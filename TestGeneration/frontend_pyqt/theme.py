DARK_THEME = """
QMainWindow, QWidget, QDialog {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", sans-serif;
}

QLabel {
    color: #cdd6f4;
    background: transparent;
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #3b82f6;
}
QLineEdit::placeholder, QTextEdit::placeholder, QPlainTextEdit::placeholder {
    color: #6c7086;
}

QPushButton {
    background-color: #3b82f6;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    min-height: 20px;
}
QPushButton:hover {
    background-color: #2563eb;
}
QPushButton:pressed {
    background-color: #1d4ed8;
}
QPushButton:disabled {
    background-color: #45475a;
    color: #6c7086;
}

QPushButton#secondary {
    background-color: #45475a;
}
QPushButton#secondary:hover {
    background-color: #585b70;
}
QPushButton#secondary:pressed {
    background-color: #6c7086;
}

QPushButton#danger {
    background-color: #ef4444;
}
QPushButton#danger:hover {
    background-color: #dc2626;
}
QPushButton#danger:pressed {
    background-color: #b91c1c;
}

QComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 20px;
}
QComboBox:hover, QComboBox:focus {
    border: 1px solid #3b82f6;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    selection-background-color: #3b82f6;
    border: 1px solid #45475a;
    border-radius: 4px;
}

QTabWidget::pane {
    background-color: #1e1e2e;
    border: 1px solid #45475a;
    border-radius: 6px;
}
QTabBar::tab {
    background-color: #313244;
    color: #a6adc8;
    border: none;
    border-radius: 6px 6px 0 0;
    padding: 8px 16px;
    margin-right: 2px;
    font-weight: 500;
}
QTabBar::tab:selected {
    background-color: #3b82f6;
    color: #ffffff;
}
QTabBar::tab:hover:!selected {
    background-color: #45475a;
}

QTableWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    gridline-color: #313244;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
}
QHeaderView::section {
    background-color: #313244;
    color: #cdd6f4;
    border: none;
    border-bottom: 1px solid #45475a;
    padding: 8px;
    font-weight: 600;
}
QTableWidget::item {
    padding: 6px;
}

QGroupBox {
    background-color: #2a2a3c;
    border: 1px solid #45475a;
    border-radius: 8px;
    margin-top: 12px;
    padding: 16px 12px 12px 12px;
    font-weight: 600;
    color: #cdd6f4;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #a6adc8;
}

QStatusBar {
    background-color: #2a2a3c;
    color: #a6adc8;
    border-top: 1px solid #45475a;
}
QStatusBar QLabel {
    color: #a6adc8;
}

QScrollArea {
    border: none;
}

QScrollBar:vertical {
    background-color: #1e1e2e;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: #585b70;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background-color: #1e1e2e;
    height: 10px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background-color: #45475a;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #585b70;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

QSplitter::handle {
    background-color: #45475a;
}

QFrame {
    border-radius: 6px;
}

QMenuBar {
    background-color: #2a2a3c;
    color: #cdd6f4;
    border-bottom: 1px solid #45475a;
}
QMenuBar::item:selected {
    background-color: #3b82f6;
}
QMenu {
    background-color: #2a2a3c;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #3b82f6;
}
QMenu::separator {
    height: 1px;
    background-color: #45475a;
    margin: 4px 8px;
}

QProgressDialog {
    background-color: #1e1e2e;
}
QProgressDialog QLabel {
    color: #cdd6f4;
}

QMessageBox {
    background-color: #1e1e2e;
}
QMessageBox QLabel {
    color: #cdd6f4;
}
QMessageBox QPushButton {
    min-width: 80px;
}
"""
