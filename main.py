"""
InterSpeed — Internet Speed Monitor & Billing System
Main application entry point.
"""
import sys
import os
import logging
from datetime import datetime

# Setup logging before anything else
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "interspeed.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("interspeed.main")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QLabel, QPushButton, QStackedWidget,
    QFrame, QSizePolicy, QSplitter
)
from PySide6.QtCore import Qt, QTimer, QSettings
from PySide6.QtGui import QFont, QIcon, QFontDatabase

from ui.styles import MAIN_STYLESHEET, C_SIDEBAR, C_SIDEBAR_ACTIVE, C_NAVY, C_MUTED, C_PRIMARY, C_BORDER
from database.database import get_db
from core.monitor import NetworkMonitor
from core.usage_tracker import UsageTracker

# Import all pages
from ui.dashboard import DashboardPage
from ui.monitoring import MonitoringPage
from ui.speedtest import SpeedTestPage
from ui.analytics import AnalyticsPage
from ui.usage import UsagePage
from ui.billing import BillingPage
from ui.history import HistoryPage
from ui.settings import SettingsPage


class SidebarButton(QPushButton):
    """Navigation button for the sidebar."""
    def __init__(self, icon_text: str, label: str, parent=None):
        super().__init__(parent)
        self.setText(f"  {icon_text}   {label}")
        self.setObjectName("navBtn")
        self.setMinimumHeight(44)
        self.setCheckable(False)
        self.setCursor(Qt.PointingHandCursor)
        self._active = False

    def set_active(self, active: bool):
        self._active = active
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("InterSpeed — Internet Speed Monitor & Billing")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        self.db = get_db()
        self._monitor: NetworkMonitor = None
        self._usage_tracker: UsageTracker = None
        self._current_page = 0
        self._nav_buttons: list = []

        self._setup_ui()
        self._setup_monitor()

        # Show dashboard by default
        self._navigate_to(0)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ─── Sidebar ────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(4)

        # Logo area
        logo_lbl = QLabel("⚡ InterSpeed")
        logo_lbl.setObjectName("sidebarTitle")
        sub_lbl = QLabel("Speed Monitor & Billing")
        sub_lbl.setObjectName("sidebarSubtitle")
        sidebar_layout.addWidget(logo_lbl)
        sidebar_layout.addWidget(sub_lbl)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {C_BORDER}; background: {C_BORDER}; margin: 8px 0;")
        line.setFixedHeight(1)
        sidebar_layout.addWidget(line)

        # Navigation buttons
        nav_items = [
            ("📊", "Dashboard"),
            ("📡", "Live Monitoring"),
            ("⚡", "Speed Test"),
            ("📈", "Analytics"),
            ("💾", "Data Usage"),
            ("🧾", "Billing"),
            ("🕐", "History"),
            ("⚙", "Settings"),
        ]
        for idx, (icon, label) in enumerate(nav_items):
            btn = SidebarButton(icon, label)
            btn.clicked.connect(lambda checked, i=idx: self._navigate_to(i))
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # Status at bottom
        self._sidebar_status = QLabel("● Initializing…")
        self._sidebar_status.setObjectName("cardTitle")
        self._sidebar_status.setStyleSheet(f"color: {C_MUTED}; padding: 4px;")
        sidebar_layout.addWidget(self._sidebar_status)

        self._sidebar_speed = QLabel("↓ 0.00  ↑ 0.00 Mbps")
        self._sidebar_speed.setObjectName("cardTitle")
        self._sidebar_speed.setStyleSheet(f"color: {C_PRIMARY}; padding: 4px;")
        sidebar_layout.addWidget(self._sidebar_speed)

        root_layout.addWidget(sidebar)

        # ─── Page stack ──────────────────────────────────────────
        self._stack = QStackedWidget()

        self._page_dashboard = DashboardPage()
        self._page_monitoring = MonitoringPage()
        self._page_speedtest = SpeedTestPage()
        self._page_analytics = AnalyticsPage()
        self._page_usage = UsagePage()
        self._page_billing = BillingPage()
        self._page_history = HistoryPage()
        self._page_settings = SettingsPage()

        pages = [
            self._page_dashboard,
            self._page_monitoring,
            self._page_speedtest,
            self._page_analytics,
            self._page_usage,
            self._page_billing,
            self._page_history,
            self._page_settings,
        ]
        for page in pages:
            self._stack.addWidget(page)

        root_layout.addWidget(self._stack)

        # Connect monitoring page callbacks
        self._page_monitoring.set_interface_callback(self._on_interface_change)
        self._page_monitoring.set_interval_callback(self._on_interval_change)

    def _setup_monitor(self):
        """Initialize the background network monitor."""
        settings = self.db.get_all_settings()
        iface = settings.get("selected_interface", "auto")
        interval = float(settings.get("monitor_interval_sec", "2"))
        auto_start = settings.get("start_monitoring_on_launch", "true") == "true"

        if auto_start:
            self._start_monitor(iface, interval)
        else:
            self._sidebar_status.setText("● Monitoring paused")

    def _start_monitor(self, interface: str = "auto", interval: float = 2.0):
        if self._monitor and self._monitor.isRunning():
            self._monitor.stop()

        self._monitor = NetworkMonitor(interface=interface, interval=interval)
        self._monitor.speed_updated.connect(self._on_speed_update)
        self._monitor.status_changed.connect(self._on_status_change)
        self._monitor.error_occurred.connect(self._on_monitor_error)
        self._monitor.start()

        # Usage tracker
        if self._usage_tracker and self._usage_tracker.isRunning():
            self._usage_tracker.stop()

        self._usage_tracker = UsageTracker()
        self._usage_tracker.usage_updated.connect(self._on_usage_update)
        self._usage_tracker.start()

        logger.info("Monitor started (interface=%s, interval=%.1fs)", interface, interval)

    def _navigate_to(self, index: int):
        self._current_page = index
        self._stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_buttons):
            btn.set_active(i == index)

        # Refresh the page on navigation
        page = self._stack.currentWidget()
        if hasattr(page, "refresh"):
            try:
                page.refresh()
            except Exception as e:
                logger.error("Page refresh error: %s", e)

    def _on_speed_update(self, down: float, up: float, recv: float, sent: float, iface: str):
        try:
            # Update sidebar
            self._sidebar_speed.setText(f"↓ {down:.2f}  ↑ {up:.2f} Mbps")

            # Forward to active pages
            self._page_dashboard.on_speed_update(down, up, recv, sent, iface)
            self._page_monitoring.on_speed_update(down, up, recv, sent, iface)

            # Record usage
            if self._usage_tracker:
                self._usage_tracker.record_sample(down, up, recv, sent, iface)
        except Exception as e:
            logger.error("Error in _on_speed_update: %s", e)

    def _on_status_change(self, connected: bool):
        if connected:
            self._sidebar_status.setText("● Online")
            self._sidebar_status.setStyleSheet("color: #4CAF9A; padding: 4px;")
        else:
            self._sidebar_status.setText("● Offline")
            self._sidebar_status.setStyleSheet("color: #E05C5C; padding: 4px;")

        self._page_dashboard.on_status_change(connected)
        self._page_monitoring.on_status_change(connected)

    def _on_monitor_error(self, msg: str):
        logger.warning("Monitor error: %s", msg)
        self._sidebar_status.setText("● Error")
        self._sidebar_status.setStyleSheet(f"color: #E05C5C; padding: 4px;")

    def _on_usage_update(self, recv_gb: float, sent_gb: float):
        self._page_usage.update_session(recv_gb, sent_gb)

    def _on_interface_change(self, iface: str):
        if self._monitor:
            self._monitor.set_interface(iface)
            logger.info("Interface changed to: %s", iface)

    def _on_interval_change(self, seconds: int):
        if self._monitor:
            self._monitor.set_interval(float(seconds))
            logger.info("Monitor interval changed to: %ds", seconds)

    def closeEvent(self, event):
        """Gracefully stop background threads on close."""
        logger.info("Application closing — stopping background threads.")
        if self._monitor:
            self._monitor.stop()
        if self._usage_tracker:
            self._usage_tracker.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("InterSpeed")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("InterSpeed")

    # Load Google-style font from system (Segoe UI is Windows default)
    app.setFont(QFont("Segoe UI", 10))

    # Apply stylesheet
    app.setStyleSheet(MAIN_STYLESHEET)

    # Initialize database first
    try:
        db = get_db()
        logger.info("Database ready at: %s", db.db_path)
    except Exception as e:
        logger.critical("Database initialization failed: %s", e)
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Database Error",
                             f"Failed to initialize database:\n{e}\n\n"
                             "The application will exit.")
        sys.exit(1)

    window = MainWindow()
    window.show()

    logger.info("InterSpeed started successfully.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
