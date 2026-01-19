from app.websocket.events import EventBus, EventProcessor

event_bus = EventBus()


def get_event_processor(db_session, connection_manager):
    """Factory function to create EventProcessor instances."""
    return EventProcessor(db_session, connection_manager)
