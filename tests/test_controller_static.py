"""Controller static-mode integration smoke test."""

import os
import sys

from PySide6.QtWidgets import QApplication

from src.Controllers import SchedulerController
from src.UI.main_window import MainWindow


def test_controller_static_flow():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication(sys.argv)

    window = MainWindow()
    controller = SchedulerController(window)
    controller.bind_window(window)

    captured = {
        "progress": None,
        "rows": None,
        "results": None,
    }

    controller.progress_updated.connect(lambda value: captured.__setitem__("progress", value))
    controller.process_table_updated.connect(lambda rows: captured.__setitem__("rows", rows))
    controller.results_updated.connect(
        lambda a, b, c, d: captured.__setitem__("results", (a, b, c, d))
    )

    controller.set_mode("static")
    controller.set_algorithm("fcfs")
    controller.add_process({"pid": "P1", "arrival": 0, "burst": 4, "priority": None, "quantum": None})
    controller.add_process({"pid": "P2", "arrival": 1, "burst": 3, "priority": None, "quantum": None})

    controller.start_simulation()

    assert captured["progress"] == 100
    assert captured["rows"] is not None and len(captured["rows"]) == 2
    assert captured["results"] is not None
