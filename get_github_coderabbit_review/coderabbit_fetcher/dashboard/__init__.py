"""Real-time dashboard module for CodeRabbit fetcher."""

from .data_aggregator import DataAggregator, HistoricalData, MetricsCollector, RealtimeStats
from .visualizations import ChartGenerator, MetricsVisualizer, ReportGenerator
from .web_server import DashboardConfig, DashboardServer, create_dashboard_app
from .websocket_handler import BroadcastManager, ClientConnection, WebSocketHandler

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
    "BroadcastManager",
]
