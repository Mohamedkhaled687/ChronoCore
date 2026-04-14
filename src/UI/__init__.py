"""
ChronoCore UI package — re-exports every public widget for convenient imports.

Usage:
    from src.UI import MainWindow, TopBarWidget, SidebarWidget, ...
"""

from src.UI.main_window import MainWindow
from src.UI.top_bar import TopBarWidget
from src.UI.sidebar import SidebarWidget
from src.UI.input_panel import InputPanelWidget
from src.UI.active_state_monitor import ActiveStateMonitorWidget
from src.UI.gantt_chart import GanttChartWidget
from src.UI.status_bar import StatusBarWidget

__all__ = [
    "MainWindow",
    "TopBarWidget",
    "SidebarWidget",
    "InputPanelWidget",
    "ActiveStateMonitorWidget",
    "GanttChartWidget",
    "StatusBarWidget",
]
