"""
ChronoCore — StatusBarWidget

Thin bar at the very bottom of the window showing system indicators:
  - System health status (dot + label)
  - Active algorithm name
  - Uptime counter (auto-incremented via QTimer)
  - Kernel version label
"""

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
)
from PySide6.QtCore import QTimer, QTime
from PySide6.QtGui import QFont

from src.UI.styles import (
    PRIMARY_DARK,
    TEXT_LIGHT,
    TEXT_SECONDARY,
    STATUS_RUNNING,
    DANGER_RED,
    CARD_BORDER,
)


class StatusBarWidget(QFrame):
    """
    Bottom status strip — no outgoing signals; driven by public setters.
    """

    KERNEL_VERSION = "KERNEL 3.15.0-V2"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(28)
        self._healthy = True
        self._elapsed = QTime(0, 0, 0)
        self._build_ui()
        self._apply_styles()
        self._start_uptime_timer()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(20)

        # System health
        self.dot_health = QLabel("\u25CF")
        self.dot_health.setFixedWidth(12)
        self.dot_health.setStyleSheet(f"color: {STATUS_RUNNING}; font-size: 10px; background: transparent;")
        layout.addWidget(self.dot_health)

        self.lbl_health = QLabel("SYSTEM HEALTHY")
        self.lbl_health.setStyleSheet(self._indicator_style())
        layout.addWidget(self.lbl_health)

        layout.addSpacing(8)

        # Active algorithm
        self.dot_algo = QLabel("\u25CF")
        self.dot_algo.setFixedWidth(12)
        self.dot_algo.setStyleSheet(f"color: {STATUS_RUNNING}; font-size: 10px; background: transparent;")
        layout.addWidget(self.dot_algo)

        self.lbl_algo = QLabel("FCFS ACTIVE")
        self.lbl_algo.setStyleSheet(self._indicator_style())
        layout.addWidget(self.lbl_algo)

        layout.addStretch()

        # Uptime
        self.lbl_uptime = QLabel("UPTIME: 00:00:00")
        self.lbl_uptime.setStyleSheet(self._indicator_style())
        layout.addWidget(self.lbl_uptime)

        layout.addSpacing(16)

        # Kernel
        self.lbl_kernel = QLabel(self.KERNEL_VERSION)
        self.lbl_kernel.setStyleSheet(self._indicator_style())
        layout.addWidget(self.lbl_kernel)

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------
    def _apply_styles(self) -> None:
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            StatusBarWidget {{
                background-color: {PRIMARY_DARK};
                border: none;
                border-top: 1px solid {CARD_BORDER};
            }}
        """
        )

    @staticmethod
    def _indicator_style() -> str:
        return (
            f"color: {TEXT_LIGHT}; font-size: 10px; font-weight: 600; "
            f"letter-spacing: 0.8px; background: transparent;"
        )

    # ------------------------------------------------------------------
    # Uptime timer
    # ------------------------------------------------------------------
    def _start_uptime_timer(self) -> None:
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick_uptime)
        self._timer.start()

    def _tick_uptime(self) -> None:
        self._elapsed = self._elapsed.addSecs(1)
        self.lbl_uptime.setText(f"UPTIME: {self._elapsed.toString('HH:mm:ss')}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_system_status(self, healthy: bool) -> None:
        """Toggle between SYSTEM HEALTHY (green) and SYSTEM ERROR (red)."""
        self._healthy = healthy
        color = STATUS_RUNNING if healthy else DANGER_RED
        text = "SYSTEM HEALTHY" if healthy else "SYSTEM ERROR"
        self.dot_health.setStyleSheet(f"color: {color}; font-size: 10px; background: transparent;")
        self.lbl_health.setText(text)

    def set_active_algorithm(self, name: str) -> None:
        """Update the active-algorithm indicator text."""
        self.lbl_algo.setText(f"{name.upper()} ACTIVE")

    def reset_uptime(self) -> None:
        """Reset the uptime counter back to 00:00:00."""
        self._elapsed = QTime(0, 0, 0)
        self.lbl_uptime.setText("UPTIME: 00:00:00")
