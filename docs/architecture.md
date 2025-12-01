# Architecture

## Overview

The K8s Lambda Shim provides a unified event dispatcher that routes AWS Lambda events to Kubernetes services, eliminating the need for Lambda-to-Lambda invocations.

## Components

### Event Dispatcher

The core component that identifies event types and routes them to appropriate handlers.

```
AWS Event → Event Dispatcher → Middleware Chain → Handler → K8s Service
```

**Supported Event Types:**
- API Gateway (REST/HTTP)
- EventBridge
- SQS
- Direct Invoke

### Service Registry

Maps Lambda function names to Kubernetes service endpoints.

**Example:**
```python
registry.register("asn-processor", ServiceEndpoint(
 namespace="freightverify",
 service_name="asn-processor-service",
 port=8080,
 path="/process"
))
```

Service endpoints are resolved using Kubernetes DNS:
```
http://{service_name}.{namespace}.svc.cluster.local:{port}{path}
```

### Middleware Chain

Provides cross-cutting concerns like authentication, validation, logging, and enrichment.

**Execution Order:**
1. LoggingMiddleware - Request/response logging
2. ValidationMiddleware - Basic payload validation
3. AuthMiddleware - API key verification
4. ASNValidationMiddleware - Domain-specific validation
5. ASNEnrichmentMiddleware - Data enrichment
6. ASNBatchProcessingMiddleware - Batch processing logic

Each middleware can:
- Modify the event
- Short-circuit the chain (error handling)
- Add context
- Transform responses

### Handlers

Event-type-specific handlers that invoke K8s services via HTTP.

**Handler Types:**
- `APIGatewayHandler` - Formats response for API Gateway
- `EventBridgeHandler` - Processes EventBridge events
- `SQSHandler` - Handles SQS batch processing with partial batch failures
- `DirectInvokeHandler` - Basic HTTP invocation

## Data Flow

### Example: SQS ASN Processing

```
SQS Queue → Lambda Runtime
 ↓
Event Dispatcher (identifies SQS event)
 ↓
Middleware Chain
 ├─ LoggingMiddleware (log incoming batch)
 ├─ ValidationMiddleware (check required fields)
 ├─ ASNValidationMiddleware (validate ASN structure)
 ├─ ASNEnrichmentMiddleware (add tracking metadata)
 └─ ASNBatchProcessingMiddleware (split into batches)
 ↓
SQSHandler
 ↓
HTTP POST to K8s Service
 ↓
K8s Service processes ASN
 ↓
Response with batchItemFailures
```

## Event Type Detection

The dispatcher automatically identifies event types:

```python
if "httpMethod" in event or "requestContext" in event:
 return EventType.API_GATEWAY
elif "detail-type" in event or "source" in event:
 return EventType.EVENTBRIDGE
elif "Records" in event and event["Records"][0].get("eventSource") == "aws:sqs":
 return EventType.SQS
else:
 return EventType.DIRECT_INVOKE
```

## Error Handling

### SQS Partial Batch Failures

The `SQSHandler` returns `batchItemFailures` to support partial batch failure processing:

```python
{
 "batchItemFailures": [
 {"itemIdentifier": "messageId-1"},
 {"itemIdentifier": "messageId-5"}
 ]
}
```

### Middleware Error Propagation

Exceptions in middleware propagate up the chain and can be caught by outer middleware (e.g., LoggingMiddleware).

## Extensibility

### Custom Middleware

```python
class CustomMiddleware(Middleware):
 async def process(self, event: Event, next_handler: HandlerFunc) -> ResponseType:
 # Pre-processing
 event.context["custom_field"] = "value"

 # Call next middleware/handler
 response = await next_handler(event)

 # Post-processing
 response["custom_header"] = "value"
 return response
```

### Custom Handlers

```python
class CustomHandler(K8sInvokeHandler):
 async def handle(self, event: Event) -> dict[str, Any]:
 # Custom pre-processing
 result = await super().handle(event)
 # Custom post-processing
 return result
```

## Deployment

### As Lambda Layer

Package the shim as a Lambda layer and use it in your existing Lambda functions:

```python
from shim import create_dispatcher

dispatcher = create_dispatcher(config)

def lambda_handler(event, context):
 return dispatcher.dispatch(event)
```

### As Standalone Service

Deploy as a service in K8s that receives webhooks or SQS messages and routes them to other K8s services.

## Configuration

Configuration can be loaded from YAML:

```yaml
services:
 function-name:
 namespace: prod
 service_name: my-service
 port: 8080
 path: /invoke

middleware:
 auth:
 enabled: true
 api_keys:
 - "key-1"
 - "key-2"
```
