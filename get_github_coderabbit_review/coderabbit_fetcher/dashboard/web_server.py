"""Web server for real-time dashboard."""

import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

# Optional dependencies for web server
try:
    from flask import Flask, jsonify, render_template, request, send_from_directory
    from flask_socketio import SocketIO, emit, join_room, leave_room

    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None
    SocketIO = None

from ..patterns.observer import Event, EventObserver, EventType, subscribe_observer

logger = logging.getLogger(__name__)


def _generate_secure_key() -> str:
    """Generate a secure random key for Flask sessions.

    Returns:
        Base64-encoded 32-byte random key

    Raises:
        RuntimeError: If secure key generation fails
    """
    try:
        import secrets
        import base64

        # Generate 32 random bytes and encode as base64
        random_bytes = secrets.token_bytes(32)
        return base64.b64encode(random_bytes).decode("utf-8")
    except ImportError:
        # Fallback for older Python versions
        import os
        import base64

        random_bytes = os.urandom(32)
        return base64.b64encode(random_bytes).decode("utf-8")


@dataclass
class DashboardConfig:
    """Dashboard configuration."""

    host: str = "localhost"
    port: int = 8080
    debug: bool = False
    auto_refresh_interval: int = 5  # seconds
    max_history_points: int = 100
    enable_authentication: bool = False
    secret_key: str = field(
        default_factory=lambda: os.environ.get("DASHBOARD_SECRET_KEY") or _generate_secure_key()
    )
    static_folder: str = "dashboard/static"
    template_folder: str = "dashboard/templates"
    cors_enabled: bool = True
    websocket_enabled: bool = True


@dataclass
class RealtimeMetrics:
    """Real-time metrics data."""

    timestamp: str
    processing_count: int = 0
    ai_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    errors: int = 0
    average_response_time: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    active_connections: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "processing_count": self.processing_count,
            "ai_requests": self.ai_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "errors": self.errors,
            "average_response_time": self.average_response_time,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "active_connections": self.active_connections,
        }


class DashboardServer:
    """Real-time dashboard server."""

    def __init__(self, config: DashboardConfig):
        """Initialize dashboard server.

        Args:
            config: Dashboard configuration
        """
        if not FLASK_AVAILABLE:
            raise ImportError(
                "Flask and Flask-SocketIO are required for dashboard. Install with: pip install flask flask-socketio"
            )

        self.config = config

        # Security warning for default secret key
        if config.secret_key == "dev-secret-key":
            logger.warning(
                "Using default development secret key for dashboard. "
                "Set DASHBOARD_SECRET_KEY environment variable for production!"
            )

        self.app = None
        self.socketio = None
        self.running = False
        self.metrics_history: List[RealtimeMetrics] = []
        self.current_metrics = RealtimeMetrics(timestamp=self._get_timestamp())

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}

        # Statistics
        self.stats = {
            "server_start_time": None,
            "total_requests": 0,
            "connected_clients": 0,
            "total_events_processed": 0,
        }

        # Initialize Flask app
        self._init_flask_app()

        # Subscribe to events
        self._subscribe_to_events()

    def _init_flask_app(self) -> None:
        """Initialize Flask application."""
        self.app = Flask(
            __name__,
            static_folder=self.config.static_folder,
            template_folder=self.config.template_folder,
        )

        self.app.config["SECRET_KEY"] = self.config.secret_key

        # Initialize SocketIO
        if self.config.websocket_enabled:
            self.socketio = SocketIO(
                self.app,
                cors_allowed_origins="*" if self.config.cors_enabled else None,
                logger=logger,
                engineio_logger=logger,
            )
            self._setup_socketio_handlers()

        # Setup routes
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup Flask routes."""

        @self.app.route("/")
        def dashboard_home():
            """Dashboard home page."""
            return render_template("dashboard.html", config=self.config)

        @self.app.route("/api/metrics")
        def get_metrics():
            """Get current metrics."""
            self.stats["total_requests"] += 1

            response_data = {
                "current": self.current_metrics.to_dict(),
                "history": [m.to_dict() for m in self.metrics_history[-50:]],  # Last 50 points
                "stats": self.stats.copy(),
            }

            return jsonify(response_data)

        @self.app.route("/api/health")
        def health_check():
            """Health check endpoint."""
            return jsonify(
                {
                    "status": "healthy",
                    "uptime": self._get_uptime(),
                    "version": "1.0.0",
                    "timestamp": self._get_timestamp(),
                }
            )

        @self.app.route("/api/export/<format>")
        def export_data(format):
            """Export data in various formats."""
            if format not in ["json", "csv"]:
                return jsonify({"error": "Unsupported format"}), 400

            if format == "json":
                return jsonify(
                    {
                        "metrics_history": [m.to_dict() for m in self.metrics_history],
                        "export_timestamp": self._get_timestamp(),
                    }
                )
            elif format == "csv":
                # Simple CSV export (in production, use proper CSV library)
                csv_data = "timestamp,processing_count,ai_requests,cache_hits,errors\\n"
                for metric in self.metrics_history:
                    csv_data += f"{metric.timestamp},{metric.processing_count},{metric.ai_requests},{metric.cache_hits},{metric.errors}\\n"

                return csv_data, 200, {"Content-Type": "text/csv"}

        @self.app.route("/static/<path:filename>")
        def static_files(filename):
            """Serve static files."""
            return send_from_directory(self.config.static_folder, filename)

    def _setup_socketio_handlers(self) -> None:
        """Setup SocketIO event handlers."""
        if not self.socketio:
            return

        @self.socketio.on("connect")
        def handle_connect():
            """Handle client connection."""
            self.stats["connected_clients"] += 1
            logger.info(f"Client connected. Total clients: {self.stats['connected_clients']}")

            # Send initial data to client
            emit(
                "metrics_update",
                {
                    "current": self.current_metrics.to_dict(),
                    "history": [m.to_dict() for m in self.metrics_history[-10:]],
                },
            )

        @self.socketio.on("disconnect")
        def handle_disconnect():
            """Handle client disconnection."""
            self.stats["connected_clients"] = max(0, self.stats["connected_clients"] - 1)
            logger.info(f"Client disconnected. Total clients: {self.stats['connected_clients']}")

        @self.socketio.on("subscribe_to_events")
        def handle_subscribe(data):
            """Handle event subscription."""
            event_types = data.get("event_types", [])
            for event_type in event_types:
                join_room(f"events_{event_type}")

            emit("subscription_confirmed", {"event_types": event_types})

        @self.socketio.on("request_metrics")
        def handle_metrics_request():
            """Handle metrics request."""
            emit(
                "metrics_update",
                {
                    "current": self.current_metrics.to_dict(),
                    "history": [m.to_dict() for m in self.metrics_history[-50:]],
                },
            )

    def _subscribe_to_events(self) -> None:
        """Subscribe to system events."""
        # Create event observer
        observer = DashboardEventObserver(self)

        # Subscribe to relevant events
        subscribe_observer(
            observer,
            [
                EventType.PROCESSING_STARTED,
                EventType.PROCESSING_COMPLETED,
                EventType.PROCESSING_FAILED,
                EventType.CACHE_HIT,
                EventType.CACHE_MISS,
            ],
        )

    def start_server(self, threaded: bool = True) -> None:
        """Start the dashboard server.

        Args:
            threaded: Whether to run in a separate thread
        """
        if self.running:
            logger.warning("Dashboard server is already running")
            return

        self.stats["server_start_time"] = datetime.now()
        self.running = True

        logger.info(f"Starting dashboard server on {self.config.host}:{self.config.port}")

        if threaded:
            # Start in background thread
            server_thread = threading.Thread(target=self._run_server, daemon=True)
            server_thread.start()

            # Start metrics update loop
            metrics_thread = threading.Thread(target=self._metrics_update_loop, daemon=True)
            metrics_thread.start()

        else:
            # Run in current thread
            self._run_server()

    def _run_server(self) -> None:
        """Run the Flask server."""
        try:
            if self.socketio:
                self.socketio.run(
                    self.app,
                    host=self.config.host,
                    port=self.config.port,
                    debug=self.config.debug,
                    use_reloader=False,  # Disable reloader in threaded mode
                )
            else:
                self.app.run(
                    host=self.config.host,
                    port=self.config.port,
                    debug=self.config.debug,
                    threaded=True,
                )
        except Exception as e:
            logger.error(f"Dashboard server error: {e}")
            self.running = False

    def _metrics_update_loop(self) -> None:
        """Background loop to update metrics."""
        while self.running:
            try:
                # Update current metrics
                self._update_current_metrics()

                # Add to history
                self.metrics_history.append(self.current_metrics)

                # Limit history size
                if len(self.metrics_history) > self.config.max_history_points:
                    self.metrics_history = self.metrics_history[-self.config.max_history_points :]

                # Broadcast to clients
                self._broadcast_metrics_update()

                # Wait for next update
                time.sleep(self.config.auto_refresh_interval)

            except Exception as e:
                logger.error(f"Metrics update error: {e}")
                time.sleep(self.config.auto_refresh_interval)

    def _update_current_metrics(self) -> None:
        """Update current metrics from system state."""
        # Get system metrics (simplified - in production, use psutil)
        import psutil

        # Update metrics
        self.current_metrics = RealtimeMetrics(
            timestamp=self._get_timestamp(),
            memory_usage=psutil.virtual_memory().percent,
            cpu_usage=psutil.cpu_percent(),
            active_connections=self.stats["connected_clients"],
            # Other metrics would be updated from event handlers
            processing_count=self.current_metrics.processing_count,
            ai_requests=self.current_metrics.ai_requests,
            cache_hits=self.current_metrics.cache_hits,
            cache_misses=self.current_metrics.cache_misses,
            errors=self.current_metrics.errors,
            average_response_time=self.current_metrics.average_response_time,
        )

    def _broadcast_metrics_update(self) -> None:
        """Broadcast metrics update to all connected clients."""
        if not self.socketio or not self.running:
            return

        try:
            self.socketio.emit(
                "metrics_update",
                {"current": self.current_metrics.to_dict(), "timestamp": self._get_timestamp()},
            )
        except Exception as e:
            logger.error(f"Broadcast error: {e}")

    def handle_event(self, event: Event) -> None:
        """Handle system event for metrics update.

        Args:
            event: System event
        """
        self.stats["total_events_processed"] += 1

        # Update metrics based on event type
        if event.event_type == EventType.PROCESSING_STARTED:
            self.current_metrics.processing_count += 1

        elif event.event_type == EventType.PROCESSING_COMPLETED:
            # Extract response time if available
            if "response_time_ms" in event.data:
                response_time = event.data["response_time_ms"]
                self._update_average_response_time(response_time)

            # Count AI requests
            if event.source in ["OpenAIClient", "AnthropicClient", "AICommentClassifier"]:
                self.current_metrics.ai_requests += 1

        elif event.event_type == EventType.PROCESSING_FAILED:
            self.current_metrics.errors += 1

        elif event.event_type == EventType.CACHE_HIT:
            self.current_metrics.cache_hits += 1

        elif event.event_type == EventType.CACHE_MISS:
            self.current_metrics.cache_misses += 1

        # Broadcast event to interested clients
        self._broadcast_event(event)

    def _update_average_response_time(self, response_time: float) -> None:
        """Update average response time."""
        if self.current_metrics.average_response_time == 0.0:
            self.current_metrics.average_response_time = response_time
        else:
            # Simple moving average
            self.current_metrics.average_response_time = (
                self.current_metrics.average_response_time * 0.9 + response_time * 0.1
            )

    def _broadcast_event(self, event: Event) -> None:
        """Broadcast event to subscribed clients."""
        if not self.socketio:
            return

        try:
            room = f"events_{event.event_type.value}"
            self.socketio.emit(
                "system_event",
                {
                    "event_type": event.event_type.value,
                    "source": event.source,
                    "data": event.data,
                    "timestamp": event.timestamp.isoformat(),
                    "severity": event.severity,
                },
                room=room,
            )
        except Exception as e:
            logger.error(f"Event broadcast error: {e}")

    def stop_server(self) -> None:
        """Stop the dashboard server."""
        logger.info("Stopping dashboard server")
        self.running = False

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        return datetime.now().isoformat()

    def _get_uptime(self) -> str:
        """Get server uptime."""
        if not self.stats["server_start_time"]:
            return "0:00:00"

        uptime = datetime.now() - self.stats["server_start_time"]
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def get_dashboard_url(self) -> str:
        """Get dashboard URL."""
        return f"http://{self.config.host}:{self.config.port}"


class DashboardEventObserver(EventObserver):
    """Event observer for dashboard updates."""

    def __init__(self, dashboard: DashboardServer):
        """Initialize observer.

        Args:
            dashboard: Dashboard server instance
        """
        self.dashboard = dashboard

    def update(self, event: Event) -> None:
        """Handle event.

        Args:
            event: System event
        """
        self.dashboard.handle_event(event)

    def get_name(self) -> str:
        """Get observer name."""
        return "DashboardEventObserver"


def create_dashboard_app(config: Optional[DashboardConfig] = None) -> DashboardServer:
    """Create dashboard application.

    Args:
        config: Optional dashboard configuration

    Returns:
        Dashboard server instance
    """
    if config is None:
        config = DashboardConfig()

    return DashboardServer(config)


# Global dashboard instance
_global_dashboard: Optional[DashboardServer] = None


def get_dashboard() -> Optional[DashboardServer]:
    """Get global dashboard instance."""
    return _global_dashboard


def set_dashboard(dashboard: DashboardServer) -> None:
    """Set global dashboard instance."""
    global _global_dashboard
    _global_dashboard = dashboard
    logger.info("Set global dashboard server")


def start_dashboard(
    config: Optional[DashboardConfig] = None, threaded: bool = True
) -> DashboardServer:
    """Start dashboard server.

    Args:
        config: Optional dashboard configuration
        threaded: Whether to run in background thread

    Returns:
        Dashboard server instance
    """
    dashboard = create_dashboard_app(config)
    set_dashboard(dashboard)
    dashboard.start_server(threaded=threaded)

    logger.info(f"Dashboard available at: {dashboard.get_dashboard_url()}")
    return dashboard


# Example usage
if __name__ == "__main__":
    # Create and start dashboard
    config = DashboardConfig(host="0.0.0.0", port=8080, debug=True)

    dashboard = start_dashboard(config, threaded=False)
