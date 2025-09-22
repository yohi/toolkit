"""Real-time dashboard module for CodeRabbit fetcher."""

from .web_server import (
    DashboardServer,
    DashboardConfig,
    create_dashboard_app
)

from .data_aggregator import (
    DataAggregator,
    MetricsCollector,
    RealtimeStats,
    HistoricalData
)

from .visualizations import (
    ChartGenerator,
    MetricsVisualizer,
    ReportGenerator
)

from .websocket_handler import (
    WebSocketHandler,
    ClientConnection,
    BroadcastManager
)

__all__ = [
    # Web Server
    "DashboardServer",
    "DashboardConfig",
    "create_dashboard_app",

    # Data Aggregation
    "DataAggregator",
    "MetricsCollector",
    "RealtimeStats",
    "HistoricalData",

    # Visualizations
    "ChartGenerator",
    "MetricsVisualizer",
    "ReportGenerator",

    # WebSocket
    "WebSocketHandler",
    "ClientConnection",
    "BroadcastManager"
]
