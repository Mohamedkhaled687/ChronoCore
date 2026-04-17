"""ChronoCore application entry point."""

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from src.Controllers import SchedulerController
from src.UI.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)

    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    window = MainWindow()
    controller = SchedulerController(window)
    controller.bind_window(window)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
