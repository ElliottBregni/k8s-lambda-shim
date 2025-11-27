"""Tests for event dispatcher."""
import pytest

from shim.events.dispatcher import EventDispatcher, Event, EventType


class TestEventTypeIdentification:
    def test_identifies_api_gateway_with_http_method(self):
        raw_event = {"httpMethod": "POST", "body": "{}"}
        event_type = EventDispatcher.identify_event_type(raw_event)
        assert event_type == EventType.API_GATEWAY
    
    def test_identifies_api_gateway_with_request_context(self):
        raw_event = {"requestContext": {"accountId": "123"}}
        event_type = EventDispatcher.identify_event_type(raw_event)
        assert event_type == EventType.API_GATEWAY
    
    def test_identifies_eventbridge_with_detail_type(self):
        raw_event = {"detail-type": "Some Event", "detail": {}}
        event_type = EventDispatcher.identify_event_type(raw_event)
        assert event_type == EventType.EVENTBRIDGE
    
    def test_identifies_eventbridge_with_source(self):
        raw_event = {"source": "aws.events", "detail": {}}
        event_type = EventDispatcher.identify_event_type(raw_event)
        assert event_type == EventType.EVENTBRIDGE
    
    def test_identifies_sqs(self):
        raw_event = {
            "Records": [
                {"eventSource": "aws:sqs", "body": "{}"}
            ]
        }
        event_type = EventDispatcher.identify_event_type(raw_event)
        assert event_type == EventType.SQS
    
    def test_identifies_direct_invoke_as_fallback(self):
        raw_event = {"custom": "data"}
        event_type = EventDispatcher.identify_event_type(raw_event)
        assert event_type == EventType.DIRECT_INVOKE


class TestEventDispatcher:
    def test_registers_handler(self):
        dispatcher = EventDispatcher()
        handler = object()
        dispatcher.register_handler(EventType.SQS, handler)
        assert dispatcher._handlers[EventType.SQS] == handler
    
    @pytest.mark.asyncio
    async def test_raises_error_for_unregistered_event_type(self):
        dispatcher = EventDispatcher()
        event = Event(
            event_type=EventType.SQS,
            function_name="test",
            payload={}
        )
        
        with pytest.raises(ValueError, match="No handler registered"):
            await dispatcher.dispatch(event)
