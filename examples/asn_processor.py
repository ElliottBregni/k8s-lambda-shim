"""Example: ASN processing with K8s Lambda shim."""
import asyncio
import logging
from datetime import datetime

from shim.events.dispatcher import EventDispatcher, Event, EventType
from shim.registry.service_registry import ServiceRegistry, ServiceEndpoint
from shim.middleware.base import MiddlewareChain
from shim.middleware.common import LoggingMiddleware, ValidationMiddleware
from shim.middleware.asn import (
    ASNValidationMiddleware,
    ASNEnrichmentMiddleware,
    ASNBatchProcessingMiddleware
)
from shim.handlers import (
    APIGatewayHandler,
    EventBridgeHandler,
    SQSHandler,
    DirectInvokeHandler
)

logging.basicConfig(level=logging.INFO)


async def main():
    # Setup service registry
    registry = ServiceRegistry()
    registry.register("asn-processor", ServiceEndpoint(
        namespace="freightverify",
        service_name="asn-processor-service",
        port=8080,
        path="/process"
    ))
    registry.register("parts-validator", ServiceEndpoint(
        namespace="freightverify",
        service_name="parts-validator-service",
        port=8080,
        path="/validate"
    ))
    
    # Setup event dispatcher with handlers
    dispatcher = EventDispatcher()
    dispatcher.register_handler(EventType.API_GATEWAY, APIGatewayHandler(registry))
    dispatcher.register_handler(EventType.EVENTBRIDGE, EventBridgeHandler(registry))
    dispatcher.register_handler(EventType.SQS, SQSHandler(registry))
    dispatcher.register_handler(EventType.DIRECT_INVOKE, DirectInvokeHandler(registry))
    
    # Setup middleware chain
    middleware = MiddlewareChain([
        LoggingMiddleware(),
        ValidationMiddleware(),
        ASNValidationMiddleware(),
        ASNEnrichmentMiddleware(),
        ASNBatchProcessingMiddleware(batch_size=50),
    ])
    
    # Example 1: SQS event with batch of ASNs
    sqs_event = Event(
        event_type=EventType.SQS,
        function_name="asn-processor",
        payload={
            "Records": [
                {
                    "messageId": "msg-001",
                    "body": {
                        "shipment_number": "SH-2025-001",
                        "carrier": "FEDEX",
                        "ship_to_address": "123 Factory St, Detroit, MI",
                        "delivery_date": "2025-11-28",
                        "items": [
                            {
                                "part_number": "BRK-1234-A",
                                "quantity": 100,
                                "description": "Brake Pad Assembly"
                            },
                            {
                                "part_number": "ENG-5678-B",
                                "quantity": 50,
                                "description": "Engine Gasket"
                            }
                        ]
                    }
                },
                {
                    "messageId": "msg-002",
                    "body": {
                        "shipment_number": "SH-2025-002",
                        "carrier": "UPS",
                        "ship_to_address": "456 Plant Rd, Chicago, IL",
                        "delivery_date": "2025-11-29",
                        "items": [
                            {
                                "part_number": "TIRE-9012-C",
                                "quantity": 200,
                                "description": "All-Season Tire"
                            }
                        ]
                    }
                }
            ]
        },
        context={
            "timestamp": datetime.now().isoformat(),
            "request_id": "req-123"
        }
    )
    
    # Example 2: API Gateway event (webhook from PartView)
    api_gateway_event = Event(
        event_type=EventType.API_GATEWAY,
        function_name="parts-validator",
        payload={
            "httpMethod": "POST",
            "body": {
                "shipment_number": "SH-2025-003",
                "carrier": "DHL",
                "ship_to_address": "789 Assembly Blvd, Austin, TX",
                "delivery_date": "2025-11-30",
                "items": [
                    {
                        "part_number": "TRANS-3456-D",
                        "quantity": 25,
                        "description": "Transmission Housing"
                    }
                ]
            }
        },
        context={"api_key": "partview-webhook-key"}
    )
    
    # Example 3: EventBridge event (scheduled ASN processing)
    eventbridge_event = Event(
        event_type=EventType.EVENTBRIDGE,
        function_name="asn-processor",
        payload={
            "detail-type": "Scheduled ASN Processing",
            "source": "aws.scheduler",
            "detail": {
                "shipment_number": "SH-2025-004",
                "carrier": "USPS",
                "ship_to_address": "321 Logistics Way, Phoenix, AZ",
                "delivery_date": "2025-12-01",
                "items": [
                    {
                        "part_number": "SEAT-7890-E",
                        "quantity": 75,
                        "description": "Leather Seat Cover"
                    }
                ]
            }
        }
    )
    
    # Process events through middleware chain
    async def process_with_middleware(event: Event):
        async def final_handler(evt: Event):
            return await dispatcher.dispatch(evt)
        
        return await middleware.execute(event, final_handler)
    
    print("\n=== Processing SQS Batch ===")
    try:
        result = await process_with_middleware(sqs_event)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n=== Processing API Gateway Event ===")
    try:
        result = await process_with_middleware(api_gateway_event)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n=== Processing EventBridge Event ===")
    try:
        result = await process_with_middleware(eventbridge_event)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
