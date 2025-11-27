"""Event dispatcher for routing Lambda events to K8s services."""
from enum import Enum
from typing import Any, Protocol
from pydantic import BaseModel, Field


class EventType(str, Enum):
    API_GATEWAY = "api_gateway"
    EVENTBRIDGE = "eventbridge"
    SQS = "sqs"
    DIRECT_INVOKE = "direct_invoke"


class Event(BaseModel):
    event_type: EventType
    payload: dict[str, Any]
    context: dict[str, Any] = Field(default_factory=dict)
    source_arn: str | None = None
    function_name: str


class EventHandler(Protocol):
    async def handle(self, event: Event) -> dict[str, Any]: ...


class EventDispatcher:
    def __init__(self):
        self._handlers: dict[EventType, EventHandler] = {}
    
    def register_handler(self, event_type: EventType, handler: EventHandler):
        self._handlers[event_type] = handler
    
    async def dispatch(self, event: Event) -> dict[str, Any]:
        handler = self._handlers.get(event.event_type)
        if not handler:
            raise ValueError(f"No handler registered for {event.event_type}")
        return await handler.handle(event)
    
    @staticmethod
    def identify_event_type(raw_event: dict[str, Any]) -> EventType:
        if "httpMethod" in raw_event or "requestContext" in raw_event:
            return EventType.API_GATEWAY
        elif "detail-type" in raw_event or "source" in raw_event:
            return EventType.EVENTBRIDGE
        elif "Records" in raw_event and raw_event["Records"][0].get("eventSource") == "aws:sqs":
            return EventType.SQS
        else:
            return EventType.DIRECT_INVOKE
