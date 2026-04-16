"""
ChronoCore — ActiveStateMonitorWidget

Right-side card in the main content area displaying the real-time
state of every process currently in the scheduler.

Layout:
  - Header row with title, total-process count, and CPU-load badge
  - QTableWidget with columns:
      Process | Arrival | Burst | Remaining (progress bar) | Priority | Status
"""

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QProgressBar,
    QHeaderView,
    QSizePolicy,
    QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from src.UI.styles import (
    SURFACE_WHITE,
    CARD_BG,
    CARD_BORDER,
    TEXT_DARK,
    TEXT_SECONDARY,
    TEXT_LIGHT,
    PRIMARY_DARK,
    ACCENT_TEAL,
    STATUS_RUNNING,
    STATUS_WAITING,
    STATUS_FINISHED,
    BORDER_RADIUS,
)

COLUMNS = ["Process", "Arrival", "Burst", "Remaining", "Priority", "Status", "Wait", "Turnaround"]
_STATUS_COLORS = {
    "RUNNING": STATUS_RUNNING,
    "WAITING": STATUS_WAITING,
    "FINISHED": STATUS_FINISHED,
}


class ActiveStateMonitorWidget(QFrame):
    """
    Process-state table with live remaining-burst progress bars.

    No outgoing signals — this widget is a pure display driven by
    the backend controller through public methods.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._apply_styles()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(12)

        # --- Header row ---
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        title = QLabel("ACTIVE STATE MONITOR")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_DARK}; background: transparent;")
        header_row.addWidget(title)

        subtitle = QLabel("Real-time scheduling stack execution details")
        subtitle.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 11px; background: transparent;"
        )
        header_row.addWidget(subtitle)
        header_row.addStretch()

        # Badges
        self.lbl_total = QLabel("TOTAL PROCESSES: 0")
        self.lbl_total.setStyleSheet(self._badge_style(CARD_BG, TEXT_DARK))
        header_row.addWidget(self.lbl_total)

        self.lbl_cpu = QLabel("CPU LOAD: 0%")
        self.lbl_cpu.setStyleSheet(self._badge_style(PRIMARY_DARK, TEXT_LIGHT))
        header_row.addWidget(self.lbl_cpu)

        outer.addLayout(header_row)

        # --- Table ---
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        h = self.table.horizontalHeader()
        h.setStretchLastSection(False)
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setColumnWidth(5, 120)

        outer.addWidget(self.table, stretch=1)

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------
    def _apply_styles(self) -> None:
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            ActiveStateMonitorWidget {{
                background-color: {SURFACE_WHITE};
                border: 1px solid {CARD_BORDER};
                border-radius: 10px;
            }}
        """
        )
        self.table.setStyleSheet(
            self.table.styleSheet()
            + f"""
            QTableWidget {{
                alternate-background-color: {CARD_BG};
                background-color: {SURFACE_WHITE};
            }}
        """
        )

    @staticmethod
    def _badge_style(bg: str, fg: str) -> str:
        return (
            f"background-color: {bg}; color: {fg}; font-size: 10px; "
            f"font-weight: 700; padding: 4px 10px; border-radius: 4px; "
            f"letter-spacing: 0.5px;"
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _make_remaining_bar(self, remaining: float, burst: float) -> QProgressBar:
        bar = QProgressBar()
        bar.setRange(0, int(burst * 10))
        bar.setValue(int(remaining * 10))
        bar.setFixedHeight(14)
        bar.setTextVisible(False)
        bar.setStyleSheet(
            f"QProgressBar {{ background-color: {CARD_BG}; border: none; border-radius: 3px; }}"
            f"QProgressBar::chunk {{ background-color: {PRIMARY_DARK}; border-radius: 3px; }}"
        )
        return bar

    def _make_status_label(self, status: str) -> QLabel:
        color = _STATUS_COLORS.get(status.upper(), TEXT_SECONDARY)
        lbl = QLabel(status.upper())
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl.setStyleSheet(
            f"color: {color}; font-weight: 700; background: transparent; "
            f"letter-spacing: 0.5px;"
        )
        return lbl

    # ------------------------------------------------------------------
    # Public API (called by backend controllers)
    # ------------------------------------------------------------------
    def update_process_table(self, processes: list[dict]) -> None:
        """
        Replace the entire table with new process data.

        Each dict: {pid, arrival, burst, remaining, priority, status}
        """
        self.table.setRowCount(0)
        self.table.setRowCount(len(processes))

        for row, p in enumerate(processes):
            self.table.setItem(row, 0, QTableWidgetItem(str(p.get("pid", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(p.get("arrival", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(str(p.get("burst", ""))))

            burst = float(p.get("burst", 1))
            remaining = float(p.get("remaining", 0))

            remaining_container = QWidget()
            remaining_layout = QHBoxLayout(remaining_container)
            remaining_layout.setContentsMargins(4, 4, 4, 4)
            bar = self._make_remaining_bar(remaining, burst)
            remaining_layout.addWidget(bar)
            remaining_val = QLabel(f" {remaining:.0f}")
            remaining_val.setStyleSheet(f"color: {TEXT_DARK}; font-size: 11px; background: transparent;")
            remaining_layout.addWidget(remaining_val)
            self.table.setCellWidget(row, 3, remaining_container)

            priority_text = str(p.get("priority", "")) if p.get("priority") is not None else ""
            self.table.setItem(row, 4, QTableWidgetItem(priority_text))

            status_lbl = self._make_status_label(p.get("status", "WAITING"))
            self.table.setCellWidget(row, 5, status_lbl)

            wait_text = f"{p.get('waiting_time', 0.0):.2f}" if p.get("waiting_time") is not None else ""
            self.table.setItem(row, 6, QTableWidgetItem(wait_text))

            tat_text = f"{p.get('turnaround_time', 0.0):.2f}" if p.get("turnaround_time") is not None else ""
            self.table.setItem(row, 7, QTableWidgetItem(tat_text))

            self.table.setRowHeight(row, 44)

        for col in range(self.table.columnCount()):
            for row in range(self.table.rowCount()):
                item = self.table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_total_processes(self, count: int) -> None:
        """Update the 'TOTAL PROCESSES' badge."""
        self.lbl_total.setText(f"TOTAL PROCESSES: {count:02d}")

    def set_cpu_load(self, percent: int) -> None:
        """Update the 'CPU LOAD' badge."""
        clamped = max(0, min(100, percent))
        self.lbl_cpu.setText(f"CPU LOAD: {clamped}%")

    def highlight_running_process(self, pid: str) -> None:
        """Visually highlight the row whose PID matches."""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.text() == pid:
                self.table.selectRow(row)
                return
