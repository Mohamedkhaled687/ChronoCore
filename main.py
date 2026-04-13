"""
ChronoCore — Application Entry Point

Launches the PySide6 QApplication and shows the main window.
"""

import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from src.UI.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)

    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
