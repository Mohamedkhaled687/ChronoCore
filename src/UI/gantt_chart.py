"""
ChronoCore — GanttChartWidget

Bottom card in the main content area showing a horizontal Gantt
timeline of CPU allocation painted via QPainter.

Features:
  - Colored blocks per process (auto-assigned palette)
  - Lighter blocks for context switches
  - Time axis with tick marks
  - "QUEUE PENDING" zone for unallocated future time
  - Legend (Active / Context Switch)
  - Horizontal scroll for long timelines
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
    QScrollArea,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush

from src.UI.styles import (
    SURFACE_WHITE,
    CARD_BG,
    CARD_BORDER,
    TEXT_DARK,
    TEXT_SECONDARY,
    TEXT_LIGHT,
    PRIMARY_DARK,
    ACCENT_TEAL,
    BORDER_RADIUS,
)

_PROCESS_PALETTE = [
    "#1B4F72", "#0D7C66", "#2E86C1", "#1A5276",
    "#148F77", "#2874A6", "#117A65", "#1F618D",
    "#0E6655", "#21618C", "#17A589", "#2980B9",
]

_CONTEXT_SWITCH_COLOR = "#CBD5E1"


class _TimelineCanvas(QWidget):
    """
    Internal widget that does the actual QPainter drawing.
    Embedded inside a QScrollArea so long timelines can scroll.
    """

    BLOCK_HEIGHT = 40
    AXIS_HEIGHT = 30
    TOP_PADDING = 10
    PIXELS_PER_UNIT = 14

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._blocks: list[dict] = []
        self._total_time: float = 80.0
        self._pid_colors: dict[str, QColor] = {}
        self._color_idx = 0
        self.setMinimumHeight(self.BLOCK_HEIGHT + self.AXIS_HEIGHT + self.TOP_PADDING + 20)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _color_for_pid(self, pid: str) -> QColor:
        if pid not in self._pid_colors:
            color = _PROCESS_PALETTE[self._color_idx % len(_PROCESS_PALETTE)]
            self._pid_colors[pid] = QColor(color)
            self._color_idx += 1
        return self._pid_colors[pid]

    def _recalc_width(self) -> None:
        needed = int(self._total_time * self.PIXELS_PER_UNIT) + 60
        self.setMinimumWidth(max(needed, self.parent().width() if self.parent() else 600))

    def set_blocks(self, blocks: list[dict]) -> None:
        self._blocks = blocks
        self._recalc_width()
        self.update()

    def set_total_time(self, t: float) -> None:
        self._total_time = max(t, 10.0)
        self._recalc_width()
        self.update()

    def clear(self) -> None:
        self._blocks.clear()
        self._pid_colors.clear()
        self._color_idx = 0
        self._total_time = 80.0
        self._recalc_width()
        self.update()

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        left_margin = 30.0
        right_margin = 30.0
        usable = w - left_margin - right_margin
        scale = usable / self._total_time if self._total_time else 1.0

        block_y = self.TOP_PADDING
        axis_y = block_y + self.BLOCK_HEIGHT + 8

        # --- Draw blocks ---
        last_end = 0.0
        for b in self._blocks:
            x = left_margin + b["start"] * scale
            bw = (b["end"] - b["start"]) * scale
            rect = QRectF(x, block_y, bw, self.BLOCK_HEIGHT)

            if b.get("is_context_switch"):
                painter.setBrush(QBrush(QColor(_CONTEXT_SWITCH_COLOR)))
            else:
                painter.setBrush(QBrush(self._color_for_pid(b["pid"])))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 4, 4)

            if bw > 30:
                painter.setPen(QPen(QColor(TEXT_LIGHT)))
                painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, b["pid"])

            last_end = max(last_end, b["end"])

        # --- Queue-pending zone ---
        if last_end < self._total_time:
            pending_x = left_margin + last_end * scale
            pending_w = (self._total_time - last_end) * scale
            pending_rect = QRectF(pending_x, block_y, pending_w, self.BLOCK_HEIGHT)
            painter.setBrush(QBrush(QColor(CARD_BG)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(pending_rect, 4, 4)
            painter.setPen(QPen(QColor(TEXT_SECONDARY)))
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
            painter.drawText(pending_rect, Qt.AlignmentFlag.AlignCenter, "QUEUE PENDING")

        # --- Time axis ---
        painter.setPen(QPen(QColor(TEXT_SECONDARY), 1))
        painter.drawLine(int(left_margin), int(axis_y), int(w - right_margin), int(axis_y))

        tick_interval = self._calc_tick_interval()
        painter.setFont(QFont("Segoe UI", 8))
        t = 0.0
        while t <= self._total_time:
            tx = left_margin + t * scale
            painter.drawLine(int(tx), int(axis_y), int(tx), int(axis_y + 5))
            painter.drawText(int(tx) - 10, int(axis_y + 18), f"{t:.0f}")
            t += tick_interval

        painter.end()

    def _calc_tick_interval(self) -> float:
        if self._total_time <= 20:
            return 2
        if self._total_time <= 50:
            return 5
        if self._total_time <= 200:
            return 10
        return 20


class GanttChartWidget(QFrame):
    """
    Gantt chart card with scrollable QPainter timeline.

    No outgoing signals — driven by the backend through public methods.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._blocks: list[dict] = []
        self._build_ui()
        self._apply_styles()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 14, 20, 14)
        outer.setSpacing(8)

        # --- Header row ---
        header_row = QHBoxLayout()

        title_col = QVBoxLayout()
        title = QLabel("GANTT CHART VISUALIZATION")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_DARK}; background: transparent;")
        title_col.addWidget(title)

        subtitle = QLabel("Timeline representation of CPU allocation over time")
        subtitle.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 11px; background: transparent;"
        )
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)

        header_row.addStretch()

        # Legend
        legend_row = QHBoxLayout()
        legend_row.setSpacing(16)
        legend_row.addWidget(self._legend_item(PRIMARY_DARK, "ACTIVE"))
        legend_row.addWidget(self._legend_item(_CONTEXT_SWITCH_COLOR, "CONTEXT SWITCH"))
        header_row.addLayout(legend_row)

        outer.addLayout(header_row)

        # --- Scrollable canvas ---
        self._canvas = _TimelineCanvas()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._canvas)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setFixedHeight(
            _TimelineCanvas.BLOCK_HEIGHT
            + _TimelineCanvas.AXIS_HEIGHT
            + _TimelineCanvas.TOP_PADDING
            + 20
        )

        outer.addWidget(scroll, stretch=1)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _legend_item(color: str, text: str) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)

        dot = QLabel()
        dot.setFixedSize(12, 12)
        dot.setStyleSheet(
            f"background-color: {color}; border-radius: 2px; border: none;"
        )
        h.addWidget(dot)

        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 10px; font-weight: 600; "
            f"letter-spacing: 0.5px; background: transparent;"
        )
        h.addWidget(lbl)
        return w

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------
    def _apply_styles(self) -> None:
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            GanttChartWidget {{
                background-color: {SURFACE_WHITE};
                border: 1px solid {CARD_BORDER};
                border-radius: 10px;
            }}
        """
        )

    # ------------------------------------------------------------------
    # Public API (called by backend controllers)
    # ------------------------------------------------------------------
    def add_gantt_block(
        self,
        pid: str,
        start: float,
        end: float,
        is_context_switch: bool = False,
    ) -> None:
        """Append a block and repaint."""
        self._blocks.append(
            {"pid": pid, "start": start, "end": end, "is_context_switch": is_context_switch}
        )
        self._canvas.set_blocks(self._blocks)

    def clear_chart(self) -> None:
        """Remove all blocks (new simulation)."""
        self._blocks.clear()
        self._canvas.clear()

    def set_time_range(self, total_time: float) -> None:
        """Set the total timeline length in time units."""
        self._canvas.set_total_time(total_time)
