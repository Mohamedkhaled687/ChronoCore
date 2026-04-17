"""
ChronoCore — GanttChartWidget

Bottom card in the main content area showing a horizontal Gantt
timeline of CPU allocation painted via QPainter.

Blocks are drawn as adjacent rectangles with the process name
centered inside each block, and time labels rendered at every
block boundary along the bottom axis.
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
    "#E67E22", "#2E86C1", "#1B4F72", "#0D7C66",
    "#8E44AD", "#C0392B", "#27AE60", "#2874A6",
    "#D4AC0D", "#148F77", "#1F618D", "#17A589",
]


class _TimelineCanvas(QWidget):
    """
    Internal widget that does the actual QPainter drawing.
    Embedded inside a QScrollArea so long timelines can scroll.
    """

    BLOCK_HEIGHT = 40
    AXIS_HEIGHT = 30
    TOP_PADDING = 10
    PIXELS_PER_UNIT = 50

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._blocks: list[dict] = []
        self._total_time: float = 20.0
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
        needed = int(self._total_time * self.PIXELS_PER_UNIT) + 80
        self.setMinimumWidth(max(needed, self.parent().width() if self.parent() else 600))

    def set_blocks(self, blocks: list[dict]) -> None:
        self._blocks = blocks
        if blocks:
            max_end = max(b["end"] for b in blocks)
            self._total_time = max(max_end + 2, 10.0)
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
        self._total_time = 20.0
        self._recalc_width()
        self.update()

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        left_margin = 30.0
        right_margin = 30.0
        w = self.width()
        usable = w - left_margin - right_margin
        scale = usable / self._total_time if self._total_time else 1.0

        block_y = self.TOP_PADDING
        axis_y = block_y + self.BLOCK_HEIGHT

        boundary_times: set[float] = set()

        for b in self._blocks:
            x = left_margin + b["start"] * scale
            bw = (b["end"] - b["start"]) * scale
            rect = QRectF(x, block_y, bw, self.BLOCK_HEIGHT)

            fill_color = self._color_for_pid(b["pid"])
            painter.setBrush(QBrush(fill_color))
            border_color = fill_color.darker(130)
            painter.setPen(QPen(border_color, 1.5))
            painter.drawRect(rect)

            painter.setPen(QPen(QColor(TEXT_LIGHT)))
            font_size = 10 if bw > 25 else 8
            painter.setFont(QFont("Segoe UI", font_size, QFont.Weight.Bold))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, b["pid"])

            boundary_times.add(b["start"])
            boundary_times.add(b["end"])

        # Axis line
        painter.setPen(QPen(QColor(TEXT_SECONDARY), 1))
        painter.drawLine(int(left_margin), int(axis_y), int(w - right_margin), int(axis_y))

        # Time labels at block boundaries
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QPen(QColor(TEXT_DARK)))
        for t in sorted(boundary_times):
            tx = left_margin + t * scale
            painter.drawLine(int(tx), int(axis_y), int(tx), int(axis_y + 5))
            label = f"{t:.0f}" if t == int(t) else f"{t:.1f}"
            painter.drawText(int(tx) - 8, int(axis_y + 18), label)

        painter.end()


class GanttChartWidget(QFrame):
    """
    Gantt chart card with scrollable QPainter timeline.

    No outgoing signals -- driven by the backend through public methods.
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

        # Header row
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
        outer.addLayout(header_row)

        # Scrollable canvas
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
        """Append a block and repaint. Context-switch flag is accepted but ignored."""
        self._blocks.append({"pid": pid, "start": start, "end": end})
        self._canvas.set_blocks(self._blocks)

    def clear_chart(self) -> None:
        """Remove all blocks (new simulation)."""
        self._blocks.clear()
        self._canvas.clear()

    def set_time_range(self, total_time: float) -> None:
        """Set the total timeline length in time units."""
        self._canvas.set_total_time(total_time)
