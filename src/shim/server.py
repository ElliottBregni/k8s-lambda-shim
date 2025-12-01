"""FastAPI server for K8s Lambda Shim."""
from fastapi import FastAPI, HTTPException, Request
from typing import Any, Dict
import logging

from .events.dispatcher import EventDispatcher, Event, EventType
from .registry.service_registry import ServiceRegistry, ServiceEndpoint
from .middleware.base import MiddlewareChain
from .middleware.common import LoggingMiddleware, ValidationMiddleware
from .handlers import (
 APIGatewayHandler,
 EventBridgeHandler,
 SQSHandler,
 DirectInvokeHandler
)

logger = logging.getLogger(__name__)

def create_app(config: Dict[str, Any]) -> FastAPI:
 """Create and configure FastAPI application."""
 app = FastAPI(
 title="K8s Lambda Shim",
 description="Event dispatcher for routing AWS Lambda events to Kubernetes services",
 version="0.1.0"
 )

 # Setup service registry
 registry = ServiceRegistry()
 for svc in config.get('services', []):
 registry.register(
 svc['name'],
 ServiceEndpoint(
 namespace=svc['namespace'],
 service_name=svc['service_name'],
 port=svc['port'],
 path=svc.get('path', '/')
 )
 )
 logger.info(f"Registered service: {svc['name']}")

 # Setup event dispatcher
 dispatcher = EventDispatcher()
 dispatcher.register_handler(EventType.API_GATEWAY, APIGatewayHandler(registry))
 dispatcher.register_handler(EventType.EVENTBRIDGE, EventBridgeHandler(registry))
 dispatcher.register_handler(EventType.SQS, SQSHandler(registry))
 dispatcher.register_handler(EventType.DIRECT_INVOKE, DirectInvokeHandler(registry))

 # Setup middleware
 middleware = MiddlewareChain([
 LoggingMiddleware(),
 ValidationMiddleware(),
 ])

 @app.get("/health")
 async def health():
 """Health check endpoint."""
 return {"status": "healthy", "services": len(config.get('services', []))}

 @app.post("/invoke/{function_name}")
 async def invoke_function(function_name: str, request: Request):
 """Invoke a function by name."""
 try:
 body = await request.json()

 # Detect event type from payload structure
 event_type = _detect_event_type(body)

 event = Event(
 event_type=event_type,
 function_name=function_name,
 payload=body,
 context={}
 )

 async def final_handler(evt: Event):
 return await dispatcher.dispatch(evt)

 result = await middleware.execute(event, final_handler)
 return result

 except ValueError as e:
 raise HTTPException(status_code=404, detail=str(e))
 except Exception as e:
 logger.error(f"Error invoking {function_name}: {e}")
 raise HTTPException(status_code=500, detail=str(e))

 @app.post("/sqs/{function_name}")
 async def sqs_event(function_name: str, request: Request):
 """Handle SQS events."""
 return await _handle_event(function_name, EventType.SQS, request, dispatcher, middleware)

 @app.post("/eventbridge/{function_name}")
 async def eventbridge_event(function_name: str, request: Request):
 """Handle EventBridge events."""
 return await _handle_event(function_name, EventType.EVENTBRIDGE, request, dispatcher, middleware)

 @app.post("/api-gateway/{function_name}")
 async def api_gateway_event(function_name: str, request: Request):
 """Handle API Gateway events."""
 return await _handle_event(function_name, EventType.API_GATEWAY, request, dispatcher, middleware)

 @app.get("/services")
 async def list_services():
 """List all registered services."""
 services = []
 for name, endpoint in registry._mappings.items():
 services.append({
 "name": name,
 "namespace": endpoint.namespace,
 "service_name": endpoint.service_name,
 "port": endpoint.port,
 "path": endpoint.path,
 "url": endpoint.url
 })
 return {"services": services}

 return app

async def _handle_event(
 function_name: str,
 event_type: EventType,
 request: Request,
 dispatcher: EventDispatcher,
 middleware: MiddlewareChain
) -> Dict[str, Any]:
 """Handle an event of a specific type."""
 try:
 body = await request.json()

 event = Event(
 event_type=event_type,
 function_name=function_name,
 payload=body,
 context={}
 )

 async def final_handler(evt: Event):
 return await dispatcher.dispatch(evt)

 return await middleware.execute(event, final_handler)

 except ValueError as e:
 raise HTTPException(status_code=404, detail=str(e))
 except Exception as e:
 logger.error(f"Error handling {event_type.value} event: {e}")
 raise HTTPException(status_code=500, detail=str(e))

def _detect_event_type(payload: Dict[str, Any]) -> EventType:
 """Detect AWS event type from payload structure."""
 if "Records" in payload:
 if payload["Records"] and "eventSource" in payload["Records"][0]:
 source = payload["Records"][0]["eventSource"]
 if source == "aws:sqs":
 return EventType.SQS

 if "detail-type" in payload and "source" in payload:
 return EventType.EVENTBRIDGE

 if "httpMethod" in payload or "requestContext" in payload:
 return EventType.API_GATEWAY

 return EventType.DIRECT_INVOKE
