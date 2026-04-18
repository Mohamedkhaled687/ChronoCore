"""
ChronoCore — TopBarWidget

Horizontal bar spanning the top of the window containing:
  - App title "ChronoCore"
  - Live / Static simulation-mode toggle
  - Simulation progress bar with percentage label
  - Refresh, Stop, and Run Simulation action buttons
"""

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QSizePolicy,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from src.UI.styles import (
    PRIMARY_DARK,
    TEXT_LIGHT,
    ACCENT_TEAL,
    ACCENT_TEAL_HOVER,
    DANGER_RED,
    DANGER_RED_HOVER,
    SURFACE_WHITE,
    TEXT_SECONDARY,
    CARD_BORDER,
    WARNING_ORANGE,
    WARNING_ORANGE_HOVER,
)


class TopBarWidget(QFrame):
    """
    Top navigation bar with simulation controls.

    Signals (for backend integration):
        simulation_mode_changed(str): "live" or "static"
        run_simulation_clicked(): user pressed Run
        stop_simulation_clicked(): user pressed Stop
        resume_simulation_clicked(): user pressed Resume
    """

    simulation_mode_changed = Signal(str)
    run_simulation_clicked = Signal()
    stop_simulation_clicked = Signal()
    resume_simulation_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(52)
        self._current_mode = "live"
        self._is_paused = False  # Track pause state
        self._build_ui()
        self._apply_styles()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        # --- App title ---
        self.title_label = QLabel("ChronoCore")
        title_font = QFont("Segoe UI", 15, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet(f"color: {TEXT_LIGHT}; background: transparent;")
        layout.addWidget(self.title_label)

        # --- Live / Static toggle ---
        self.btn_live = QPushButton("Live")
        self.btn_static = QPushButton("Static")
        for btn in (self.btn_live, self.btn_static):
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(30)
            btn.setFixedWidth(70)
        self.btn_live.setChecked(True)
        self.btn_live.clicked.connect(lambda: self._set_mode("live"))
        self.btn_static.clicked.connect(lambda: self._set_mode("static"))
        layout.addWidget(self.btn_live)
        layout.addWidget(self.btn_static)

        layout.addSpacing(20)

        # --- Simulation progress section ---
        self.progress_title = QLabel("SIMULATION PROGRESS")
        self.progress_title.setStyleSheet(
            f"color: {TEXT_LIGHT}; font-size: 10px; font-weight: 600; "
            f"letter-spacing: 1px; background: transparent;"
        )
        layout.addWidget(self.progress_title)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setMinimumWidth(180)
        self.progress_bar.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout.addWidget(self.progress_bar, stretch=1)

        self.progress_pct_label = QLabel("0% Complete")
        self.progress_pct_label.setStyleSheet(
            f"color: {TEXT_LIGHT}; font-size: 12px; background: transparent;"
        )
        layout.addWidget(self.progress_pct_label)

        layout.addSpacing(12)

        # # --- Action buttons ---
        # self.btn_refresh = QPushButton("\u21BB")
        # self.btn_refresh.setToolTip("Reset simulation")
        # self.btn_refresh.setFixedSize(34, 34)
        # self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        # self.btn_refresh.setStyleSheet(
        #     f"QPushButton {{ background: transparent; color: {TEXT_LIGHT}; "
        #     f"font-size: 18px; border: 1px solid rgba(255,255,255,0.3); border-radius: 6px; }}"
        #     f"QPushButton:hover {{ background: rgba(255,255,255,0.1); }}"
        # )
        # layout.addWidget(self.btn_refresh)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setFixedHeight(34)
        layout.addWidget(self.btn_stop)

        self.btn_run = QPushButton("Run Simulation")
        self.btn_run.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_run.setFixedHeight(34)
        layout.addWidget(self.btn_run)

        # --- Connect signals ---
        self.btn_run.clicked.connect(self._on_run_clicked)
        self.btn_stop.clicked.connect(self._on_stop_resume_clicked)

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------
    def _apply_styles(self) -> None:
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            TopBarWidget {{
                background-color: {PRIMARY_DARK};
                border: none;
            }}
        """
        )
        self._update_toggle_styles()
        self._update_stop_resume_button_style()

        self.btn_run.setStyleSheet(
            f"QPushButton {{ background-color: {ACCENT_TEAL}; color: {TEXT_LIGHT}; "
            f"font-weight: 600; border-radius: 6px; padding: 0 18px; }}"
            f"QPushButton:hover {{ background-color: {ACCENT_TEAL_HOVER}; }}"
        )

    def _update_toggle_styles(self) -> None:
        active_style = (
            f"QPushButton {{ background-color: {SURFACE_WHITE}; color: {PRIMARY_DARK}; "
            f"font-weight: 600; border-radius: 4px; border: none; }}"
        )
        inactive_style = (
            f"QPushButton {{ background-color: transparent; color: {TEXT_LIGHT}; "
            f"font-weight: 400; border-radius: 4px; border: 1px solid {CARD_BORDER}; }}"
            f"QPushButton:hover {{ background: rgba(255,255,255,0.1); }}"
        )
        self.btn_live.setStyleSheet(active_style if self._current_mode == "live" else inactive_style)
        self.btn_static.setStyleSheet(inactive_style if self._current_mode == "live" else active_style)

    def _update_stop_resume_button_style(self) -> None:
        """Update Stop/Resume button style based on pause state."""
        if self._is_paused:
            # Resume style - green/teal color to indicate continue action
            self.btn_stop.setStyleSheet(
                f"QPushButton {{ background-color: {WARNING_ORANGE}; color: {TEXT_LIGHT}; "
                f"font-weight: 600; border-radius: 6px; padding: 0 18px; }}"
                f"QPushButton:hover {{ background-color: {WARNING_ORANGE_HOVER}; }}"
            )
            self.btn_stop.setText("Resume")
        else:
            # Stop style - red color to indicate halt action
            self.btn_stop.setStyleSheet(
                f"QPushButton {{ background-color: {DANGER_RED}; color: {TEXT_LIGHT}; "
                f"font-weight: 600; border-radius: 6px; padding: 0 18px; }}"
                f"QPushButton:hover {{ background-color: {DANGER_RED_HOVER}; }}"
            )
            self.btn_stop.setText("Stop")

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------
    def _set_mode(self, mode: str) -> None:
        if mode == self._current_mode:
            return
        self._current_mode = mode
        self.btn_live.setChecked(mode == "live")
        self.btn_static.setChecked(mode == "static")
        self._update_toggle_styles()
        self.simulation_mode_changed.emit(mode)

    def _on_stop_resume_clicked(self) -> None:
        """Handle Stop/Resume button click - toggles pause state."""
        if self._is_paused:
            # Currently paused, so resume
            self._is_paused = False
            self.resume_simulation_clicked.emit()
        else:
            # Currently running, so stop/pause
            self._is_paused = True
            self.stop_simulation_clicked.emit()

        self._update_stop_resume_button_style()

    def _on_run_clicked(self) -> None:
        """Handle Run button click - resets pause state."""
        self._is_paused = False
        self._update_stop_resume_button_style()
        self.run_simulation_clicked.emit()

    # ------------------------------------------------------------------
    # Public API (called by backend controllers)
    # ------------------------------------------------------------------
    def set_progress(self, value: int) -> None:
        """Update the simulation progress bar (0-100)."""
        clamped = max(0, min(100, value))
        self.progress_bar.setValue(clamped)
        self.progress_pct_label.setText(f"{clamped}% Complete")

    def get_simulation_mode(self) -> str:
        """Return current mode: 'live' or 'static'."""
        return self._current_mode

    def is_paused(self) -> bool:
        """Return whether simulation is currently paused."""
        return self._is_paused

    def reset_pause_state(self) -> None:
        """Reset pause state (called when simulation finishes)."""
        self._is_paused = False
        self._update_stop_resume_button_style()