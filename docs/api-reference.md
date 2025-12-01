# API Reference

## Events

### Event

Base event model for all event types.

```python
class Event(BaseModel):
 event_type: EventType
 payload: dict[str, Any]
 context: dict[str, Any] = Field(default_factory=dict)
 source_arn: str | None = None
 function_name: str
```

**Fields:**
- `event_type`: Type of event (API_GATEWAY, EVENTBRIDGE, SQS, DIRECT_INVOKE)
- `payload`: Event payload data
- `context`: Additional context information
- `source_arn`: ARN of the event source (optional)
- `function_name`: Target Lambda/K8s function name

### EventType

```python
class EventType(str, Enum):
 API_GATEWAY = "api_gateway"
 EVENTBRIDGE = "eventbridge"
 SQS = "sqs"
 DIRECT_INVOKE = "direct_invoke"
```

## Event Dispatcher

### EventDispatcher

```python
class EventDispatcher:
 def register_handler(self, event_type: EventType, handler: EventHandler)
 async def dispatch(self, event: Event) -> dict[str, Any]
 @staticmethod
 def identify_event_type(raw_event: dict[str, Any]) -> EventType
```

**Methods:**

#### register_handler
Register a handler for a specific event type.

```python
dispatcher.register_handler(EventType.SQS, SQSHandler(registry))
```

#### dispatch
Dispatch an event to the appropriate handler.

```python
result = await dispatcher.dispatch(event)
```

**Returns:** Handler response

**Raises:**
- `ValueError`: No handler registered for event type

#### identify_event_type
Automatically identify event type from raw AWS event.

```python
event_type = EventDispatcher.identify_event_type(raw_event)
```

## Service Registry

### ServiceEndpoint

```python
class ServiceEndpoint(BaseModel):
 namespace: str = "default"
 service_name: str
 port: int = 80
 path: str = "/"

 @property
 def url(self) -> str
```

**Properties:**
- `url`: Full K8s service URL (computed)

### ServiceRegistry

```python
class ServiceRegistry:
 def register(self, function_name: str, endpoint: ServiceEndpoint)
 def lookup(self, function_name: str) -> Optional[ServiceEndpoint]
 def load_from_config(self, config: dict[str, dict])
```

**Methods:**

#### register
Register a service endpoint for a function name.

```python
registry.register("my-function", ServiceEndpoint(
 service_name="my-service",
 namespace="prod",
 port=8080
))
```

#### lookup
Look up service endpoint by function name.

```python
endpoint = registry.lookup("my-function")
```

**Returns:** `ServiceEndpoint` or `None`

#### load_from_config
Load multiple service mappings from config dict.

```python
registry.load_from_config({
 "func1": {"service_name": "service1"},
 "func2": {"service_name": "service2", "port": 9000}
})
```

## Middleware

### Middleware

```python
class Middleware(ABC):
 @abstractmethod
 async def process(self, event: Event, next_handler: HandlerFunc) -> ResponseType
```

Base class for all middleware implementations.

### MiddlewareChain

```python
class MiddlewareChain:
 def __init__(self, middlewares: list[Middleware] | None = None)
 def add(self, middleware: Middleware)
 async def execute(self, event: Event, final_handler: HandlerFunc) -> ResponseType
```

**Methods:**

#### add
Add middleware to the chain.

```python
chain.add(LoggingMiddleware())
```

#### execute
Execute the middleware chain with a final handler.

```python
result = await chain.execute(event, final_handler)
```

### Built-in Middleware

#### LoggingMiddleware

```python
class LoggingMiddleware(Middleware)
```

Logs incoming events and responses.

#### ValidationMiddleware

```python
class ValidationMiddleware(Middleware)
```

Validates required event fields.

#### AuthMiddleware

```python
class AuthMiddleware(Middleware):
 def __init__(self, api_keys: set[str] | None = None)
```

Validates API keys from `event.context["api_key"]`.

#### ASNValidationMiddleware

```python
class ASNValidationMiddleware(Middleware)
```

Validates ASN structure and required fields.

**Required Fields:**
- `shipment_number`
- `carrier`
- `ship_to_address`
- `delivery_date`
- `items` (array with `part_number` and `quantity`)

#### ASNEnrichmentMiddleware

```python
class ASNEnrichmentMiddleware(Middleware)
```

Enriches ASN events with metadata and tracking numbers.

#### ASNBatchProcessingMiddleware

```python
class ASNBatchProcessingMiddleware(Middleware):
 def __init__(self, batch_size: int = 100)
```

Processes SQS batches in configurable sub-batches.

## Handlers

### K8sInvokeHandler

```python
class K8sInvokeHandler:
 def __init__(self, registry: ServiceRegistry)
 async def handle(self, event: Event) -> dict[str, Any]
```

Base handler for invoking K8s services via HTTP POST.

### APIGatewayHandler

```python
class APIGatewayHandler(K8sInvokeHandler)
```

Formats responses for API Gateway with `statusCode`, `body`, and `headers`.

### EventBridgeHandler

```python
class EventBridgeHandler(K8sInvokeHandler)
```

Handles EventBridge events.

### SQSHandler

```python
class SQSHandler(K8sInvokeHandler)
```

Processes SQS batches and returns `batchItemFailures` for partial failures.

### DirectInvokeHandler

```python
class DirectInvokeHandler(K8sInvokeHandler)
```

Basic handler for direct Lambda invocations.

## Type Aliases

```python
ResponseType = dict[str, Any]
HandlerFunc = Callable[[Event], Awaitable[ResponseType]]
```

## Error Handling

### Common Exceptions

- `ValueError`: Invalid event data or missing handler
- `PermissionError`: Authentication failure
- `httpx.HTTPStatusError`: K8s service returned error status

### Example Error Handling

```python
try:
 result = await dispatcher.dispatch(event)
except ValueError as e:
 logger.error(f"Invalid event: {e}")
 return {"statusCode": 400, "body": str(e)}
except PermissionError as e:
 logger.error(f"Auth failed: {e}")
 return {"statusCode": 403, "body": "Forbidden"}
except Exception as e:
 logger.error(f"Unexpected error: {e}")
 return {"statusCode": 500, "body": "Internal Server Error"}
```
