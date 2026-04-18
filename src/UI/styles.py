"""
ChronoCore — Centralized QSS Stylesheet and Color Palette

All visual constants live here so that every widget module imports
from a single source of truth.  The palette is derived from the
neededUI.png mockup (navy / white / teal).
"""

# ---------------------------------------------------------------------------
# Color Palette
# ---------------------------------------------------------------------------
PRIMARY_DARK = "#1B2A4A"
PRIMARY_DARKER = "#142038"
ACCENT_TEAL = "#0D7C66"
ACCENT_TEAL_HOVER = "#0A6B58"
ACCENT_TEAL_PRESSED = "#085A4A"
SURFACE_WHITE = "#FFFFFF"
CARD_BG = "#F8F9FA"
CARD_BORDER = "#E2E8F0"
TEXT_DARK = "#1a1a2e"
TEXT_SECONDARY = "#64748B"
TEXT_LIGHT = "#FFFFFF"
DANGER_RED = "#DC2626"
DANGER_RED_HOVER = "#B91C1C"
WARNING_ORANGE = "#E67E22"
WARNING_ORANGE_HOVER = "#C86D1C"
STATUS_RUNNING = "#16A34A"
STATUS_WAITING = "#D97706"
STATUS_FINISHED = "#94A3B8"
PROGRESS_BG = "#E2E8F0"
BORDER_RADIUS = "6px"
SIDEBAR_WIDTH = 220

# ---------------------------------------------------------------------------
# Global Application Stylesheet (QSS)
# ---------------------------------------------------------------------------
APP_STYLESHEET = f"""

/* ---- Global ---- */
QMainWindow, QWidget#centralRoot {{
    background-color: {CARD_BG};
}}

/* ---- Labels ---- */
QLabel {{
    color: {TEXT_DARK};
    font-family: "Segoe UI", "Roboto", "Arial", sans-serif;
}}

/* ---- Buttons (default) ---- */
QPushButton {{
    font-family: "Segoe UI", "Roboto", "Arial", sans-serif;
    font-size: 13px;
    border: none;
    border-radius: {BORDER_RADIUS};
    padding: 8px 18px;
    color: {TEXT_LIGHT};
    background-color: {ACCENT_TEAL};
}}
QPushButton:hover {{
    background-color: {ACCENT_TEAL_HOVER};
}}
QPushButton:pressed {{
    background-color: {ACCENT_TEAL_PRESSED};
}}
QPushButton:disabled {{
    background-color: {PROGRESS_BG};
    color: {TEXT_SECONDARY};
}}

/* ---- Line Edits / Spin Boxes ---- */
QLineEdit, QDoubleSpinBox, QSpinBox {{
    font-family: "Segoe UI", "Roboto", "Arial", sans-serif;
    font-size: 13px;
    padding: 8px 10px;
    border: 1px solid {CARD_BORDER};
    border-radius: {BORDER_RADIUS};
    background-color: {SURFACE_WHITE};
    color: {TEXT_DARK};
}}
QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
    border: 1px solid {ACCENT_TEAL};
}}

/* ---- Table Widget ---- */
QTableWidget {{
    background-color: {SURFACE_WHITE};
    border: none;
    gridline-color: transparent;
    font-family: "Segoe UI", "Roboto", "Arial", sans-serif;
    font-size: 13px;
    color: {TEXT_DARK};
}}
QTableWidget::item {{
    padding: 6px 10px;
    border-bottom: 1px solid {CARD_BORDER};
}}
QTableWidget::item:selected {{
    background-color: {CARD_BG};
    color: {TEXT_DARK};
}}
QHeaderView::section {{
    background-color: {CARD_BG};
    color: {TEXT_SECONDARY};
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    padding: 8px 10px;
    border: none;
    border-bottom: 2px solid {CARD_BORDER};
}}

/* ---- Progress Bar ---- */
QProgressBar {{
    background-color: {PROGRESS_BG};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
    font-size: 1px;
}}
QProgressBar::chunk {{
    background-color: {ACCENT_TEAL};
    border-radius: 4px;
}}

/* ---- Scroll Bars ---- */
QScrollBar:horizontal {{
    height: 8px;
    background: {CARD_BG};
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {TEXT_SECONDARY};
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
QScrollBar:vertical {{
    width: 8px;
    background: {CARD_BG};
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {TEXT_SECONDARY};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* ---- Checkbox ---- */
QCheckBox {{
    font-family: "Segoe UI", "Roboto", "Arial", sans-serif;
    font-size: 13px;
    color: {TEXT_DARK};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 2px solid {CARD_BORDER};
    background-color: {SURFACE_WHITE};
}}
QCheckBox::indicator:checked {{
    background-color: {ACCENT_TEAL};
    border-color: {ACCENT_TEAL};
}}

/* ---- QSplitter ---- */
QSplitter::handle {{
    background-color: {CARD_BORDER};
    width: 1px;
}}

/* ---- Tooltip ---- */
QToolTip {{
    background-color: {PRIMARY_DARK};
    color: {TEXT_LIGHT};
    border: none;
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 12px;
}}
"""
