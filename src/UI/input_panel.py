"""
ChronoCore — InputPanelWidget

Left-side card in the main content area containing:
  - Process parameter form (PID, Arrival, Burst, Priority*, Quantum*)
  - "ADD PROCESS" button
  - Results sub-panel (AVG Wait Time, AVG Turnaround Time)

Fields marked * are conditionally shown based on the active algorithm.
"""

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QDoubleSpinBox,
    QSpinBox,
    QPushButton,
    QSizePolicy,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from src.UI.styles import (
    SURFACE_WHITE,
    CARD_BG,
    CARD_BORDER,
    TEXT_DARK,
    TEXT_SECONDARY,
    TEXT_LIGHT,
    ACCENT_TEAL,
    ACCENT_TEAL_HOVER,
    STATUS_RUNNING,
    STATUS_WAITING,
    STATUS_FINISHED,
    BORDER_RADIUS,
)


class InputPanelWidget(QFrame):
    """
    Process parameter entry form with embedded results display.

    Signals (for backend integration):
        process_added(dict): emitted with process data dict containing
            pid, arrival, burst, and optionally priority / quantum
        input_fields_cleared(): emitted after form auto-clears on add
    """

    process_added = Signal(dict)
    input_fields_cleared = Signal()

    _BADGE_STYLES = {
        "READY": f"background-color: {ACCENT_TEAL}; color: {TEXT_LIGHT};",
        "RUNNING": f"background-color: {STATUS_RUNNING}; color: {TEXT_LIGHT};",
        "FINISHED": f"background-color: {TEXT_SECONDARY}; color: {TEXT_LIGHT};",
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current_algo = "fcfs"
        self._preemptive = False
        self._quantum_locked = False
        self._build_ui()
        self._apply_styles()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(14)

        # --- Header row ---
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        header_label = QLabel("PROCESS PARAMETERS")
        header_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        header_label.setStyleSheet(f"color: {TEXT_DARK}; background: transparent;")
        header_row.addWidget(header_label)

        header_row.addStretch()

        self.status_badge = QLabel("READY")
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setFixedSize(70, 26)
        self.status_badge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._set_badge_style("READY")
        header_row.addWidget(self.status_badge)

        outer.addLayout(header_row)

        # --- Form fields ---
        form_grid = QGridLayout()
        form_grid.setHorizontalSpacing(12)
        form_grid.setVerticalSpacing(10)

        # Process ID (row 0, spans full width)
        lbl_pid = QLabel("PROCESS ID")
        lbl_pid.setStyleSheet(self._field_label_style())
        form_grid.addWidget(lbl_pid, 0, 0, 1, 2)

        self.input_pid = QLineEdit()
        self.input_pid.setPlaceholderText("P-0001")
        form_grid.addWidget(self.input_pid, 1, 0, 1, 2)

        # Arrival Time  |  Burst Time (row 2-3)
        lbl_arrival = QLabel("ARRIVAL TIME")
        lbl_arrival.setStyleSheet(self._field_label_style())
        form_grid.addWidget(lbl_arrival, 2, 0)

        lbl_burst = QLabel("BURST TIME")
        lbl_burst.setStyleSheet(self._field_label_style())
        form_grid.addWidget(lbl_burst, 2, 1)

        self.input_arrival = QDoubleSpinBox()
        self.input_arrival.setRange(0.0, 99999.0)
        self.input_arrival.setDecimals(1)
        self.input_arrival.setSuffix("  MS")
        self.input_arrival.setFixedHeight(36)
        form_grid.addWidget(self.input_arrival, 3, 0)

        self.input_burst = QDoubleSpinBox()
        self.input_burst.setRange(0.1, 99999.0)
        self.input_burst.setDecimals(1)
        self.input_burst.setSuffix("  MS")
        self.input_burst.setFixedHeight(36)
        form_grid.addWidget(self.input_burst, 3, 1)

        # Priority (row 4-5, conditional)
        self.lbl_priority = QLabel("PRIORITY")
        self.lbl_priority.setStyleSheet(self._field_label_style())
        form_grid.addWidget(self.lbl_priority, 4, 0)

        self.input_priority = QSpinBox()
        self.input_priority.setRange(0, 9999)
        self.input_priority.setFixedHeight(36)
        self.input_priority.setToolTip("Lower number = higher priority")
        form_grid.addWidget(self.input_priority, 5, 0)

        # Quantum Time (row 4-5 col 1, conditional)
        self.lbl_quantum = QLabel("QUANTUM TIME")
        self.lbl_quantum.setStyleSheet(self._field_label_style())
        form_grid.addWidget(self.lbl_quantum, 4, 1)

        self.input_quantum = QDoubleSpinBox()
        self.input_quantum.setRange(0.1, 99999.0)
        self.input_quantum.setDecimals(1)
        self.input_quantum.setSuffix("  MS")
        self.input_quantum.setFixedHeight(36)
        self.input_quantum.setToolTip("Set once per simulation run")
        form_grid.addWidget(self.input_quantum, 5, 1)

        outer.addLayout(form_grid)

        # hide conditional fields by default
        self._set_field_visibility()

        # --- Add Process button ---
        self.btn_add = QPushButton("ADD PROCESS")
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.setFixedHeight(42)
        self.btn_add.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.btn_add.setStyleSheet(
            f"QPushButton {{ background-color: {ACCENT_TEAL}; color: {TEXT_LIGHT}; "
            f"border-radius: {BORDER_RADIUS}; }}"
            f"QPushButton:hover {{ background-color: {ACCENT_TEAL_HOVER}; }}"
        )
        self.btn_add.clicked.connect(self._on_add_process)
        outer.addWidget(self.btn_add)

        # --- Separator ---
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {CARD_BORDER}; background: {CARD_BORDER};")
        sep.setFixedHeight(1)
        outer.addWidget(sep)

        # --- Results sub-panel ---
        self._build_results_panel(outer)

        outer.addStretch()

    def _build_results_panel(self, parent_layout: QVBoxLayout) -> None:
        results_row = QHBoxLayout()
        results_row.setSpacing(16)

        self.avg_wait_card = self._make_metric_card("AVG WAIT", "0.00", "ms")
        results_row.addWidget(self.avg_wait_card["frame"])

        self.avg_tat_card = self._make_metric_card("AVG TAT", "0.00", "ms")
        results_row.addWidget(self.avg_tat_card["frame"])

        parent_layout.addLayout(results_row)

    def _make_metric_card(self, title: str, value: str, unit: str) -> dict:
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background-color: {CARD_BG}; border: 1px solid {CARD_BORDER}; "
            f"border-radius: 8px; }}"
        )
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        frame.setFixedHeight(72)

        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(14, 10, 14, 10)
        vbox.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 10px; font-weight: 600; "
            f"letter-spacing: 1px; background: transparent; border: none;"
        )
        vbox.addWidget(lbl_title)

        value_row = QHBoxLayout()
        value_row.setSpacing(4)
        lbl_value = QLabel(value)
        lbl_value.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        lbl_value.setStyleSheet(f"color: {TEXT_DARK}; background: transparent; border: none;")
        value_row.addWidget(lbl_value)

        lbl_unit = QLabel(unit)
        lbl_unit.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 12px; background: transparent; border: none;"
        )
        lbl_unit.setAlignment(Qt.AlignmentFlag.AlignBottom)
        value_row.addWidget(lbl_unit)
        value_row.addStretch()
        vbox.addLayout(value_row)

        return {"frame": frame, "value": lbl_value}

    # ------------------------------------------------------------------
    # Styling helpers
    # ------------------------------------------------------------------
    def _apply_styles(self) -> None:
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            InputPanelWidget {{
                background-color: {SURFACE_WHITE};
                border: 1px solid {CARD_BORDER};
                border-radius: 10px;
            }}
        """
        )

    @staticmethod
    def _field_label_style() -> str:
        return (
            f"color: {TEXT_SECONDARY}; font-size: 10px; font-weight: 600; "
            f"letter-spacing: 1px; background: transparent;"
        )

    def _set_badge_style(self, status: str) -> None:
        base = (
            f"border-radius: 4px; padding: 2px 8px; font-size: 10px; "
            f"font-weight: 700; letter-spacing: 0.5px;"
        )
        self.status_badge.setStyleSheet(base + self._BADGE_STYLES.get(status, ""))

    # ------------------------------------------------------------------
    # Field visibility logic
    # ------------------------------------------------------------------
    def _set_field_visibility(self) -> None:
        show_priority = self._current_algo == "priority"
        show_quantum = self._current_algo == "round_robin"

        self.lbl_priority.setVisible(show_priority)
        self.input_priority.setVisible(show_priority)

        self.lbl_quantum.setVisible(show_quantum)
        self.input_quantum.setVisible(show_quantum)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------
    def _on_add_process(self) -> None:
        data = {
            "pid": self.input_pid.text().strip(),
            "arrival": self.input_arrival.value(),
            "burst": self.input_burst.value(),
            "priority": self.input_priority.value() if self._current_algo == "priority" else None,
            "quantum": self.input_quantum.value() if self._current_algo == "round_robin" else None,
        }
        self.process_added.emit(data)
        self.clear_form()

    # ------------------------------------------------------------------
    # Public API (stubs for backend integration)
    # ------------------------------------------------------------------
    def set_algorithm_mode(self, algo: str, preemptive: bool = False) -> None:
        """
        Reconfigure which input fields are visible.

        Called when the user picks a new algorithm in the sidebar.
        """
        self._current_algo = algo
        self._preemptive = preemptive
        self._set_field_visibility()

    def update_results(
        self,
        avg_wait: float,
        avg_tat: float,
        delta_wait: float = 0.0,
        delta_tat: float = 0.0,
    ) -> None:
        """Update the results sub-panel with computed metrics."""
        self.avg_wait_card["value"].setText(f"{avg_wait:.2f}")
        self.avg_tat_card["value"].setText(f"{avg_tat:.2f}")

    def set_status_badge(self, status: str) -> None:
        """Set the header badge text/color: 'READY', 'RUNNING', 'FINISHED'."""
        self.status_badge.setText(status.upper())
        self._set_badge_style(status.upper())

    def set_quantum_locked(self, locked: bool) -> None:
        """Disable quantum input once a simulation has started (Round Robin rule)."""
        self._quantum_locked = locked
        self.input_quantum.setEnabled(not locked)

    def clear_form(self) -> None:
        """Reset all input fields to defaults."""
        self.input_pid.clear()
        self.input_arrival.setValue(0.0)
        self.input_burst.setValue(0.1)
        self.input_priority.setValue(0)
        if not self._quantum_locked:
            self.input_quantum.setValue(0.1)
        self.input_fields_cleared.emit()
