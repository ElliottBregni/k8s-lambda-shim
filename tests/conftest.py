"""Pytest fixtures for K8s Lambda shim tests."""
import pytest
from datetime import datetime

from shim.events.dispatcher import Event, EventType, EventDispatcher
from shim.registry.service_registry import ServiceRegistry, ServiceEndpoint
from shim.middleware.base import MiddlewareChain
from shim.handlers import (
    APIGatewayHandler,
    EventBridgeHandler,
    SQSHandler,
    DirectInvokeHandler
)


@pytest.fixture
def service_registry():
    """Create a test service registry."""
    registry = ServiceRegistry()
    registry.register("test-function", ServiceEndpoint(
        namespace="test",
        service_name="test-service",
        port=8080,
        path="/test"
    ))
    return registry


@pytest.fixture
def event_dispatcher(service_registry):
    """Create a test event dispatcher."""
    dispatcher = EventDispatcher()
    dispatcher.register_handler(EventType.API_GATEWAY, APIGatewayHandler(service_registry))
    dispatcher.register_handler(EventType.EVENTBRIDGE, EventBridgeHandler(service_registry))
    dispatcher.register_handler(EventType.SQS, SQSHandler(service_registry))
    dispatcher.register_handler(EventType.DIRECT_INVOKE, DirectInvokeHandler(service_registry))
    return dispatcher


@pytest.fixture
def middleware_chain():
    """Create a test middleware chain."""
    return MiddlewareChain()


@pytest.fixture
def sample_asn_payload():
    """Sample ASN payload for testing."""
    return {
        "shipment_number": "SH-2025-001",
        "carrier": "FEDEX",
        "ship_to_address": "123 Factory St, Detroit, MI",
        "delivery_date": "2025-11-28",
        "items": [
            {
                "part_number": "BRK-1234-A",
                "quantity": 100,
                "description": "Brake Pad Assembly"
            }
        ]
    }


@pytest.fixture
def sqs_event(sample_asn_payload):
    """Sample SQS event."""
    return Event(
        event_type=EventType.SQS,
        function_name="test-function",
        payload={
            "Records": [
                {
                    "messageId": "msg-001",
                    "body": sample_asn_payload
                }
            ]
        },
        context={"timestamp": datetime.now().isoformat()}
    )


@pytest.fixture
def api_gateway_event(sample_asn_payload):
    """Sample API Gateway event."""
    return Event(
        event_type=EventType.API_GATEWAY,
        function_name="test-function",
        payload={
            "httpMethod": "POST",
            "body": sample_asn_payload
        },
        context={"api_key": "test-key"}
    )


@pytest.fixture
def eventbridge_event(sample_asn_payload):
    """Sample EventBridge event."""
    return Event(
        event_type=EventType.EVENTBRIDGE,
        function_name="test-function",
        payload={
            "detail-type": "Test Event",
            "source": "test.source",
            "detail": sample_asn_payload
        }
    )
