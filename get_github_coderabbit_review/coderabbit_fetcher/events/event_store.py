"""Event store implementation for CodeRabbit fetcher."""

import json
import logging
import threading
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import uuid

from ..patterns.observer import Event, EventType

logger = logging.getLogger(__name__)


@dataclass
class EventRecord:
    """Event record for storage."""
    id: str
    event: Event
    stored_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'event': self.event.to_dict(),
            'stored_at': self.stored_at.isoformat(),
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventRecord':
        """Create from dictionary."""
        event_data = data['event']
        event = Event(
            event_type=EventType(event_data['event_type']),
            timestamp=datetime.fromisoformat(event_data['timestamp']),
            source=event_data['source'],
            data=event_data['data'],
            severity=event_data['severity'],
            session_id=event_data.get('session_id')
        )

        return cls(
            id=data['id'],
            event=event,
            stored_at=datetime.fromisoformat(data['stored_at']),
            metadata=data.get('metadata', {})
        )


class EventStore(ABC):
    """Abstract event store."""

    @abstractmethod
    def store(self, event: Event, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store an event."""
        pass

    @abstractmethod
    def get(self, event_id: str) -> Optional[EventRecord]:
        """Get event by ID."""
        pass

    @abstractmethod
    def query(
        self,
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[EventRecord]:
        """Query events."""
        pass

    @abstractmethod
    def delete(self, event_id: str) -> bool:
        """Delete event by ID."""
        pass

    @abstractmethod
    def clear(self) -> int:
        """Clear all events."""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get event store statistics."""
        pass


class InMemoryEventStore(EventStore):
    """In-memory event store implementation."""

    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self._events: Dict[str, EventRecord] = {}
        self._event_order: List[str] = []
        self._lock = threading.RLock()

        self.stats = {
            'events_stored': 0,
            'events_evicted': 0,
            'queries_executed': 0
        }

    def store(self, event: Event, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store event in memory."""
        with self._lock:
            event_id = str(uuid.uuid4())

            record = EventRecord(
                id=event_id,
                event=event,
                metadata=metadata or {}
            )

            if len(self._events) >= self.max_events:
                self._evict_oldest()

            self._events[event_id] = record
            self._event_order.append(event_id)
            self.stats['events_stored'] += 1

            return event_id

    def get(self, event_id: str) -> Optional[EventRecord]:
        """Get event by ID."""
        with self._lock:
            return self._events.get(event_id)

    def query(
        self,
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[EventRecord]:
        """Query events with filters."""
        with self._lock:
            self.stats['queries_executed'] += 1
            results = []

            for record in self._events.values():
                if event_type and record.event.event_type != event_type:
                    continue
                if source and record.event.source != source:
                    continue
                if session_id and record.event.session_id != session_id:
                    continue
                if start_time and record.event.timestamp < start_time:
                    continue
                if end_time and record.event.timestamp > end_time:
                    continue

                results.append(record)

            results.sort(key=lambda r: r.event.timestamp, reverse=True)

            if limit:
                results = results[:limit]

            return results

    def delete(self, event_id: str) -> bool:
        """Delete event by ID."""
        with self._lock:
            if event_id in self._events:
                del self._events[event_id]
                if event_id in self._event_order:
                    self._event_order.remove(event_id)
                return True
            return False

    def clear(self) -> int:
        """Clear all events."""
        with self._lock:
            count = len(self._events)
            self._events.clear()
            self._event_order.clear()
            return count

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics."""
        with self._lock:
            stats = self.stats.copy()
            stats.update({
                'current_events': len(self._events),
                'max_events': self.max_events
            })
            return stats

    def _evict_oldest(self) -> None:
        """Evict oldest event."""
        if self._event_order:
            oldest_id = self._event_order.pop(0)
            if oldest_id in self._events:
                del self._events[oldest_id]
                self.stats['events_evicted'] += 1


class FileEventStore(EventStore):
    """File-based event store implementation."""

    def __init__(self, storage_dir: str = "event_store"):
        self.storage_dir = Path(storage_dir)
        self._lock = threading.RLock()

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._current_file_path = self.storage_dir / "events.jsonl"

        self.stats = {
            'events_stored': 0,
            'queries_executed': 0
        }

    def store(self, event: Event, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store event in file."""
        with self._lock:
            event_id = str(uuid.uuid4())

            record = EventRecord(
                id=event_id,
                event=event,
                metadata=metadata or {}
            )

            record_json = json.dumps(record.to_dict()) + '\n'

            try:
                with open(self._current_file_path, 'a', encoding='utf-8') as f:
                    f.write(record_json)
                    f.flush()

                self.stats['events_stored'] += 1
                return event_id

            except Exception as e:
                logger.error(f"Failed to store event: {e}")
                raise

    def get(self, event_id: str) -> Optional[EventRecord]:
        """Get event by ID."""
        with self._lock:
            try:
                with open(self._current_file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                record_data = json.loads(line)
                                if record_data['id'] == event_id:
                                    return EventRecord.from_dict(record_data)
                            except json.JSONDecodeError:
                                continue
            except FileNotFoundError:
                pass

            return None

    def query(
        self,
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[EventRecord]:
        """Query events from file."""
        with self._lock:
            self.stats['queries_executed'] += 1
            results = []

            try:
                with open(self._current_file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                record_data = json.loads(line)
                                record = EventRecord.from_dict(record_data)

                                if event_type and record.event.event_type != event_type:
                                    continue
                                if source and record.event.source != source:
                                    continue
                                if session_id and record.event.session_id != session_id:
                                    continue
                                if start_time and record.event.timestamp < start_time:
                                    continue
                                if end_time and record.event.timestamp > end_time:
                                    continue

                                results.append(record)

                                if limit and len(results) >= limit:
                                    break

                            except json.JSONDecodeError:
                                continue
            except FileNotFoundError:
                pass

            results.sort(key=lambda r: r.event.timestamp, reverse=True)
            return results

    def delete(self, event_id: str) -> bool:
        """Delete not supported for file store."""
        return False

    def clear(self) -> int:
        """Clear all event files."""
        with self._lock:
            count = 0

            try:
                with open(self._current_file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            count += 1

                self._current_file_path.unlink()

            except FileNotFoundError:
                pass

            return count

    def get_stats(self) -> Dict[str, Any]:
        """Get file store statistics."""
        with self._lock:
            stats = self.stats.copy()

            try:
                file_size = self._current_file_path.stat().st_size
                stats['file_size_bytes'] = file_size
            except FileNotFoundError:
                stats['file_size_bytes'] = 0

            return stats


# Global event store instance
_global_event_store: Optional[EventStore] = None


def get_event_store() -> Optional[EventStore]:
    """Get global event store."""
    return _global_event_store


def set_event_store(event_store: EventStore) -> None:
    """Set global event store."""
    global _global_event_store
    _global_event_store = event_store


def store_event(event: Event, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Store event in global event store."""
    event_store = get_event_store()
    if event_store:
        return event_store.store(event, metadata)
    return None
