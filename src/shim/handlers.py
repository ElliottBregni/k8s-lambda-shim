"""Event handlers for different AWS event types."""
import httpx
from typing import Any

from .events.dispatcher import Event, EventHandler
from .registry.service_registry import ServiceRegistry


class K8sInvokeHandler:
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def handle(self, event: Event) -> dict[str, Any]:
        endpoint = self.registry.lookup(event.function_name)
        if not endpoint:
            raise ValueError(f"No service registered for {event.function_name}")
        
        response = await self.client.post(
            endpoint.url,
            json={
                "event": event.payload,
                "context": event.context,
            }
        )
        response.raise_for_status()
        return response.json()


class APIGatewayHandler(K8sInvokeHandler):
    async def handle(self, event: Event) -> dict[str, Any]:
        result = await super().handle(event)
        return {
            "statusCode": 200,
            "body": result,
            "headers": {"Content-Type": "application/json"}
        }


class EventBridgeHandler(K8sInvokeHandler):
    async def handle(self, event: Event) -> dict[str, Any]:
        return await super().handle(event)


class SQSHandler(K8sInvokeHandler):
    async def handle(self, event: Event) -> dict[str, Any]:
        results = []
        for record in event.payload.get("Records", []):
            individual_event = Event(
                event_type=event.event_type,
                payload=record,
                context=event.context,
                function_name=event.function_name
            )
            result = await super().handle(individual_event)
            results.append(result)
        return {"batchItemFailures": []}


class DirectInvokeHandler(K8sInvokeHandler):
    pass
