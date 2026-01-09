from typing import Callable, Any, Dict, List

class EventBus:
    def __init__(self):
        # Dictionnaire associant un nom d'événement à une liste de fonctions
        self._listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, listener: Callable):
        """Un plugin s'abonne à un type d'événement."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    def publish(self, event_type: str, data: Any = None):
        """Un plugin diffuse une information à tout le monde."""
        if event_type in self._listeners:
            for listener in self._listeners[event_type]:
                listener(data)

# Instance unique (Singleton) pour tout le projet
bus = EventBus()