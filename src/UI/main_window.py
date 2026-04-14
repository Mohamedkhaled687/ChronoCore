"""
ChronoCore — MainWindow

QMainWindow subclass that assembles every child widget into the
final layout hierarchy:

    QVBoxLayout (root)
    +-- TopBarWidget
    +-- QSplitter (horizontal)
    |   +-- SidebarWidget
    |   +-- Central QWidget
    |       +-- QHBoxLayout (upper row)
    |       |   +-- InputPanelWidget
    |       |   +-- ActiveStateMonitorWidget
    |       +-- GanttChartWidget
    +-- StatusBarWidget

Intra-UI signals are wired here.  Backend integration hooks are
documented with clearly marked comments so that a controller can
be plugged in without touching any widget internals.
"""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
)
from PySide6.QtCore import Qt

from src.UI.styles import APP_STYLESHEET, SIDEBAR_WIDTH
from src.UI.top_bar import TopBarWidget
from src.UI.sidebar import SidebarWidget
from src.UI.input_panel import InputPanelWidget
from src.UI.active_state_monitor import ActiveStateMonitorWidget
from src.UI.gantt_chart import GanttChartWidget
from src.UI.status_bar import StatusBarWidget

_ALGO_DISPLAY_NAMES = {
    "fcfs": "FCFS",
    "sjf": "SJF",
    "priority": "Priority",
    "round_robin": "Round Robin",
}


class MainWindow(QMainWindow):
    """Root application window for ChronoCore."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ChronoCore — CPU Scheduling Simulator")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        self.setStyleSheet(APP_STYLESHEET)

        self._build_ui()
        self._connect_intra_ui_signals()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        central = QWidget(objectName="centralRoot")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- Top Bar ----
        self.top_bar = TopBarWidget()
        root.addWidget(self.top_bar)

        # ---- Horizontal splitter: Sidebar | Content ----
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)

        self.sidebar = SidebarWidget()

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 12)
        content_layout.setSpacing(14)

        # Upper row: Input Panel + Active Monitor
        upper_row = QHBoxLayout()
        upper_row.setSpacing(14)

        self.input_panel = InputPanelWidget()
        self.input_panel.setMinimumWidth(320)
        self.input_panel.setMaximumWidth(420)
        upper_row.addWidget(self.input_panel)

        self.active_monitor = ActiveStateMonitorWidget()
        upper_row.addWidget(self.active_monitor, stretch=1)

        content_layout.addLayout(upper_row, stretch=4)

        # Lower row: Gantt Chart
        self.gantt_chart = GanttChartWidget()
        content_layout.addWidget(self.gantt_chart, stretch=3)

        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(content)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([SIDEBAR_WIDTH, 1060])

        root.addWidget(self.splitter, stretch=1)

        # ---- Status Bar ----
        self.status_bar = StatusBarWidget()
        root.addWidget(self.status_bar)

    # ------------------------------------------------------------------
    # Intra-UI Signal Wiring
    # ------------------------------------------------------------------
    def _connect_intra_ui_signals(self) -> None:
        """
        Wire widget-to-widget signals that are purely UI concerns
        (e.g. sidebar selection updating the input panel fields).
        """
        # Algorithm selection -> input panel field visibility
        self.sidebar.algorithm_selected.connect(self._on_algorithm_changed)
        self.sidebar.preemptive_toggled.connect(self._on_preemptive_toggled)

        # New scenario -> reset everything
        self.sidebar.new_scenario_clicked.connect(self._on_new_scenario)

    # ------------------------------------------------------------------
    # Internal Slots (UI-only reactions)
    # ------------------------------------------------------------------
    def _on_algorithm_changed(self, algo_key: str) -> None:
        preemptive = self.sidebar.is_preemptive()
        self.input_panel.set_algorithm_mode(algo_key, preemptive)
        display = _ALGO_DISPLAY_NAMES.get(algo_key, algo_key.upper())
        self.status_bar.set_active_algorithm(display)

    def _on_preemptive_toggled(self, checked: bool) -> None:
        algo = self.sidebar.get_current_algorithm()
        self.input_panel.set_algorithm_mode(algo, checked)

    def _on_new_scenario(self) -> None:
        self.input_panel.clear_form()
        self.input_panel.set_status_badge("READY")
        self.input_panel.set_quantum_locked(False)
        self.input_panel.update_results(0.0, 0.0, 0.0, 0.0)
        self.active_monitor.update_process_table([])
        self.active_monitor.set_total_processes(0)
        self.active_monitor.set_cpu_load(0)
        self.gantt_chart.clear_chart()
        self.top_bar.set_progress(0)
        self.status_bar.reset_uptime()

    # ------------------------------------------------------------------
    # BACKEND INTEGRATION HOOKS
    #
    # The following connections should be made by the Controller layer
    # when it is instantiated.  Example wiring (in controller.__init__):
    #
    #   # UI -> Controller  (user actions)
    #   window.top_bar.run_simulation_clicked.connect(self.start_simulation)
    #   window.top_bar.stop_simulation_clicked.connect(self.stop_simulation)
    #   window.top_bar.simulation_mode_changed.connect(self.set_mode)
    #   window.sidebar.algorithm_selected.connect(self.set_algorithm)
    #   window.sidebar.preemptive_toggled.connect(self.set_preemptive)
    #   window.input_panel.process_added.connect(self.add_process)
    #
    #   # Controller -> UI  (data updates)
    #   self.progress_updated.connect(window.top_bar.set_progress)
    #   self.process_table_updated.connect(window.active_monitor.update_process_table)
    #   self.total_processes_changed.connect(window.active_monitor.set_total_processes)
    #   self.cpu_load_changed.connect(window.active_monitor.set_cpu_load)
    #   self.gantt_block_added.connect(window.gantt_chart.add_gantt_block)
    #   self.results_updated.connect(window.input_panel.update_results)
    #   self.status_changed.connect(window.input_panel.set_status_badge)
    #   self.system_health_changed.connect(window.status_bar.set_system_status)
    # ------------------------------------------------------------------
