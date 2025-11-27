# ASN Processing Guide

## Overview

The K8s Lambda Shim provides specialized middleware for processing Advanced Shipping Notices (ASNs) in automotive supply chains.

## ASN Data Structure

### Required Fields

```python
{
    "shipment_number": str,      # Unique shipment identifier
    "carrier": str,               # Carrier name (FEDEX, UPS, etc.)
    "ship_to_address": str,       # Destination address
    "delivery_date": str,         # Expected delivery (ISO 8601)
    "items": [                    # List of parts/items
        {
            "part_number": str,   # Part identifier
            "quantity": int,      # Quantity shipped
            "description": str    # Optional description
        }
    ]
}
```

### Optional Fields

- `tracking_number` - Carrier tracking number
- `container_id` - SSCC or container identifier
- `gross_weight` - Total weight
- `notes` - Additional shipping notes

## Middleware Stack

### ASNValidationMiddleware

Validates ASN structure and required fields.

**Configuration:**
```python
middleware = ASNValidationMiddleware()
```

**Validates:**
- Required fields present
- Items array not empty
- Each item has `part_number` and `quantity`

**Error Response:**
```python
ValueError: "Missing required ASN fields: {'carrier', 'delivery_date'}"
ValueError: "ASN must contain at least one item"
ValueError: "Item 0 missing part_number"
```

### ASNEnrichmentMiddleware

Adds metadata and tracking information.

**Adds:**
- `metadata.processed_at` - Processing timestamp
- `metadata.source` - Event source type
- `metadata.function_name` - Processing function
- `tracking_number` - Auto-generated if missing

**Example Enriched Payload:**
```json
{
    "shipment_number": "SH-2025-001",
    "carrier": "FEDEX",
    "tracking_number": "TRK-SH-2025-001",
    "metadata": {
        "processed_at": "2025-11-27T00:00:00Z",
        "source": "sqs",
        "function_name": "asn-processor"
    },
    "items": [...]
}
```

### ASNBatchProcessingMiddleware

Handles large SQS batches with configurable batch size.

**Configuration:**
```python
middleware = ASNBatchProcessingMiddleware(batch_size=50)
```

**Features:**
- Splits large SQS batches into sub-batches
- Error isolation (one failed batch doesn't fail all)
- Returns `batchItemFailures` for retry

**Example:**
```
100 SQS messages → 2 batches of 50
- Batch 1: Success
- Batch 2: Failure → Returns failed message IDs
```

## Event Sources

### SQS Queue

**Configuration:**
```json
{
    "FunctionResponseTypes": ["ReportBatchItemFailures"],
    "BatchSize": 10,
    "MaximumBatchingWindowInSeconds": 5
}
```

**Event Structure:**
```python
{
    "Records": [
        {
            "messageId": "msg-001",
            "body": {
                "shipment_number": "SH-2025-001",
                "carrier": "FEDEX",
                ...
            }
        }
    ]
}
```

### API Gateway (PartView Webhook)

**Headers:**
```
Content-Type: application/json
X-API-Key: your-api-key
```

**Payload:**
```json
{
    "shipment_number": "SH-2025-001",
    "carrier": "FEDEX",
    "ship_to_address": "123 Factory St",
    "delivery_date": "2025-11-28",
    "items": [...]
}
```

### EventBridge (Scheduled)

**Event Pattern:**
```json
{
    "detail-type": ["Scheduled ASN Processing"],
    "source": ["aws.scheduler"],
    "detail": {
        "shipment_number": "SH-2025-001",
        ...
    }
}
```

## K8s Service Integration

### Service Endpoints

Map Lambda functions to K8s services:

```yaml
services:
  asn-processor:
    namespace: freightverify
    service_name: asn-processor-service
    port: 8080
    path: /process
  
  parts-validator:
    namespace: freightverify
    service_name: parts-validator-service
    port: 8080
    path: /validate
```

### Expected Service Interface

K8s services should accept POST requests with:

```json
{
    "event": {
        "shipment_number": "...",
        "carrier": "...",
        ...
    },
    "context": {
        "timestamp": "...",
        "request_id": "..."
    }
}
```

And return:

```json
{
    "status": "success",
    "asn_id": "...",
    "processed_items": 5
}
```

## Example Usage

```python
from shim.events.dispatcher import EventDispatcher, Event, EventType
from shim.registry.service_registry import ServiceRegistry, ServiceEndpoint
from shim.middleware.base import MiddlewareChain
from shim.middleware.asn import (
    ASNValidationMiddleware,
    ASNEnrichmentMiddleware,
    ASNBatchProcessingMiddleware
)

# Setup
registry = ServiceRegistry()
registry.register("asn-processor", ServiceEndpoint(
    namespace="freightverify",
    service_name="asn-processor-service",
    port=8080,
    path="/process"
))

dispatcher = EventDispatcher()
dispatcher.register_handler(EventType.SQS, SQSHandler(registry))

middleware = MiddlewareChain([
    ASNValidationMiddleware(),
    ASNEnrichmentMiddleware(),
    ASNBatchProcessingMiddleware(batch_size=50),
])

# Process event
async def process_asn(event):
    async def final_handler(evt):
        return await dispatcher.dispatch(evt)
    
    return await middleware.execute(event, final_handler)
```

## Error Handling

### Validation Errors

Return HTTP 400 with error details:
```json
{
    "error": "ValidationError",
    "message": "Missing required ASN fields: {'carrier'}"
}
```

### Service Errors

Return HTTP 500 and retry via SQS:
```json
{
    "batchItemFailures": [
        {"itemIdentifier": "msg-001"}
    ]
}
```

## Best Practices

1. **Batch Size**: Set to 50-100 for optimal throughput
2. **Timeouts**: Configure 30s timeout for K8s service calls
3. **Retries**: Enable SQS DLQ for failed messages after 3 retries
4. **Validation**: Validate early to fail fast
5. **Monitoring**: Log processing metrics at each stage
6. **Idempotency**: K8s services should handle duplicate ASNs

## Monitoring

Key metrics to track:
- ASN processing latency
- Batch failure rate
- Validation error rate
- K8s service response time
- Queue depth
