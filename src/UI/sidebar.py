"""
ChronoCore — SidebarWidget

Left-hand panel listing available scheduling algorithms.

Layout:
  - Header ("ALGORITHMS" / "TECHNICAL SIMULATION")
  - Algorithm button list (FCFS, SJF, Priority, Round Robin)
  - Preemptive checkbox (visible only for SJF / Priority)
  - Spacer
  - "+ New Scenario" button
"""

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QSizePolicy,
    QSpacerItem,
    QButtonGroup,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from src.UI.styles import (
    PRIMARY_DARK,
    PRIMARY_DARKER,
    ACCENT_TEAL,
    TEXT_LIGHT,
    TEXT_SECONDARY,
    CARD_BORDER,
    SIDEBAR_WIDTH,
)

ALGORITHMS = [
    ("fcfs", "First-Come First-Served", "1"),
    ("sjf", "Shortest Job First", "2"),
    ("priority", "Priority Scheduling", "3"),
    ("round_robin", "Round Robin", "4"),
]

_ALGO_ICON_MAP = {
    "fcfs": "\u23F1",
    "sjf": "\u26A1",
    "priority": "\u2B50",
    "round_robin": "\u21BB",
}


class SidebarWidget(QFrame):
    """
    Algorithm-selection sidebar.

    Signals (for backend integration):
        algorithm_selected(str):  algorithm key, e.g. "fcfs"
        preemptive_toggled(bool): True when preemptive is checked
        new_scenario_clicked():   user wants to reset everything
    """

    algorithm_selected = Signal(str)
    preemptive_toggled = Signal(bool)
    new_scenario_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedWidth(SIDEBAR_WIDTH)
        self._current_algo = "fcfs"
        self._algo_buttons: dict[str, QPushButton] = {}
        self._build_ui()
        self._apply_styles()
        self._select_algorithm("fcfs")

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 16)
        layout.setSpacing(4)

        # --- Header ---
        header = QLabel("  ALGORITHMS")
        header_font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        header.setFont(header_font)
        header.setStyleSheet(f"color: {TEXT_LIGHT}; background: transparent; padding-left: 16px;")
        layout.addWidget(header)

        subtitle = QLabel("  TECHNICAL SIMULATION")
        subtitle.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 10px; letter-spacing: 1px; "
            f"background: transparent; padding-left: 16px; margin-bottom: 12px;"
        )
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # --- Algorithm buttons ---
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        for key, label, number in ALGORITHMS:
            btn = QPushButton(f"  {_ALGO_ICON_MAP.get(key, '')}   {label}")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(42)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            self.button_group.addButton(btn)
            self._algo_buttons[key] = btn
            layout.addWidget(btn)

            btn.clicked.connect(lambda checked, k=key: self._select_algorithm(k))

        # --- Preemptive checkbox ---
        layout.addSpacing(6)
        self.preemptive_cb = QCheckBox("  Preemptive")
        self.preemptive_cb.setStyleSheet(
            f"QCheckBox {{ color: {TEXT_LIGHT}; padding-left: 20px; background: transparent; }}"
            f"QCheckBox::indicator {{ border-color: {TEXT_SECONDARY}; }}"
            f"QCheckBox::indicator:checked {{ background-color: {ACCENT_TEAL}; border-color: {ACCENT_TEAL}; }}"
        )
        self.preemptive_cb.setVisible(False)
        self.preemptive_cb.toggled.connect(self.preemptive_toggled.emit)
        layout.addWidget(self.preemptive_cb)

        # --- Spacer ---
        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # --- New Scenario button ---
        self.btn_new_scenario = QPushButton("+ New Scenario")
        self.btn_new_scenario.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_new_scenario.setFixedHeight(38)
        self.btn_new_scenario.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: {TEXT_LIGHT}; "
            f"border: 1px solid {CARD_BORDER}; border-radius: 6px; font-weight: 600; "
            f"margin: 0 16px; }}"
            f"QPushButton:hover {{ background-color: rgba(255,255,255,0.08); }}"
        )
        self.btn_new_scenario.clicked.connect(self.new_scenario_clicked.emit)
        layout.addWidget(self.btn_new_scenario)

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------
    def _apply_styles(self) -> None:
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            SidebarWidget {{
                background-color: {PRIMARY_DARK};
                border: none;
            }}
        """
        )
        self._refresh_button_styles()

    def _refresh_button_styles(self) -> None:
        for key, btn in self._algo_buttons.items():
            if key == self._current_algo:
                btn.setStyleSheet(
                    f"QPushButton {{ text-align: left; padding-left: 16px; "
                    f"background-color: {PRIMARY_DARKER}; color: {TEXT_LIGHT}; "
                    f"font-weight: 600; border: none; "
                    f"border-left: 3px solid {ACCENT_TEAL}; border-radius: 0px; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ text-align: left; padding-left: 19px; "
                    f"background-color: transparent; color: rgba(255,255,255,0.7); "
                    f"font-weight: 400; border: none; border-radius: 0px; }}"
                    f"QPushButton:hover {{ background-color: rgba(255,255,255,0.05); "
                    f"color: {TEXT_LIGHT}; }}"
                )

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------
    def _select_algorithm(self, key: str) -> None:
        self._current_algo = key
        self._algo_buttons[key].setChecked(True)
        self._refresh_button_styles()

        has_preemptive = key in ("sjf", "priority")
        self.preemptive_cb.setVisible(has_preemptive)
        if not has_preemptive:
            self.preemptive_cb.setChecked(False)

        self.algorithm_selected.emit(key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_current_algorithm(self) -> str:
        return self._current_algo

    def is_preemptive(self) -> bool:
        return self.preemptive_cb.isChecked()
