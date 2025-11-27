"""ASN-specific middleware for automotive parts processing."""
import logging
from typing import Any

from .base import Middleware, HandlerFunc, ResponseType
from ..events.dispatcher import Event

logger = logging.getLogger(__name__)


class ASNValidationMiddleware(Middleware):
    """Validates ASN structure and required fields."""
    
    REQUIRED_FIELDS = {
        "shipment_number",
        "carrier",
        "ship_to_address",
        "delivery_date",
        "items"
    }
    
    async def process(self, event: Event, next_handler: HandlerFunc) -> ResponseType:
        payload = event.payload
        
        if event.event_type.value == "sqs":
            records = payload.get("Records", [])
            for record in records:
                body = record.get("body", {})
                self._validate_asn(body)
        else:
            self._validate_asn(payload)
        
        return await next_handler(event)
    
    def _validate_asn(self, asn_data: dict[str, Any]):
        missing_fields = self.REQUIRED_FIELDS - set(asn_data.keys())
        if missing_fields:
            raise ValueError(f"Missing required ASN fields: {missing_fields}")
        
        items = asn_data.get("items", [])
        if not items:
            raise ValueError("ASN must contain at least one item")
        
        for idx, item in enumerate(items):
            if "part_number" not in item:
                raise ValueError(f"Item {idx} missing part_number")
            if "quantity" not in item:
                raise ValueError(f"Item {idx} missing quantity")


class ASNEnrichmentMiddleware(Middleware):
    """Enriches ASN data with metadata and tracking info."""
    
    async def process(self, event: Event, next_handler: HandlerFunc) -> ResponseType:
        payload = event.payload.copy()
        
        payload["metadata"] = {
            "processed_at": event.context.get("timestamp"),
            "source": event.event_type.value,
            "function_name": event.function_name,
        }
        
        if "tracking_number" not in payload:
            payload["tracking_number"] = f"TRK-{payload.get('shipment_number', 'UNKNOWN')}"
        
        enriched_event = Event(
            event_type=event.event_type,
            payload=payload,
            context=event.context,
            function_name=event.function_name,
            source_arn=event.source_arn
        )
        
        return await next_handler(enriched_event)


class ASNBatchProcessingMiddleware(Middleware):
    """Handles large ASN batch processing with error isolation."""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
    
    async def process(self, event: Event, next_handler: HandlerFunc) -> ResponseType:
        if event.event_type.value != "sqs":
            return await next_handler(event)
        
        records = event.payload.get("Records", [])
        total = len(records)
        
        logger.info(f"Processing batch of {total} ASN records")
        
        failures = []
        for i in range(0, total, self.batch_size):
            batch = records[i:i + self.batch_size]
            batch_event = Event(
                event_type=event.event_type,
                payload={"Records": batch},
                context=event.context,
                function_name=event.function_name
            )
            
            try:
                await next_handler(batch_event)
                logger.info(f"Successfully processed batch {i//self.batch_size + 1}")
            except Exception as e:
                logger.error(f"Batch {i//self.batch_size + 1} failed: {e}")
                failures.extend([{"itemIdentifier": r.get("messageId")} for r in batch])
        
        return {"batchItemFailures": failures}
