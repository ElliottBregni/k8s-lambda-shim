"""Tests for ASN-specific middleware."""
import pytest
from unittest.mock import AsyncMock

from shim.events.dispatcher import Event, EventType
from shim.middleware.asn import (
    ASNValidationMiddleware,
    ASNEnrichmentMiddleware,
    ASNBatchProcessingMiddleware
)


class TestASNValidationMiddleware:
    @pytest.mark.asyncio
    async def test_validates_required_fields(self, sample_asn_payload):
        middleware = ASNValidationMiddleware()
        event = Event(
            event_type=EventType.DIRECT_INVOKE,
            function_name="test",
            payload=sample_asn_payload
        )
        next_handler = AsyncMock(return_value={})
        
        result = await middleware.process(event, next_handler)
        
        next_handler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rejects_missing_required_fields(self):
        middleware = ASNValidationMiddleware()
        event = Event(
            event_type=EventType.DIRECT_INVOKE,
            function_name="test",
            payload={"shipment_number": "123"}
        )
        next_handler = AsyncMock()
        
        with pytest.raises(ValueError, match="Missing required ASN fields"):
            await middleware.process(event, next_handler)
    
    @pytest.mark.asyncio
    async def test_rejects_asn_without_items(self):
        middleware = ASNValidationMiddleware()
        event = Event(
            event_type=EventType.DIRECT_INVOKE,
            function_name="test",
            payload={
                "shipment_number": "SH-001",
                "carrier": "FEDEX",
                "ship_to_address": "123 Main St",
                "delivery_date": "2025-11-28",
                "items": []
            }
        )
        next_handler = AsyncMock()
        
        with pytest.raises(ValueError, match="ASN must contain at least one item"):
            await middleware.process(event, next_handler)
    
    @pytest.mark.asyncio
    async def test_validates_items_have_part_number(self):
        middleware = ASNValidationMiddleware()
        event = Event(
            event_type=EventType.DIRECT_INVOKE,
            function_name="test",
            payload={
                "shipment_number": "SH-001",
                "carrier": "FEDEX",
                "ship_to_address": "123 Main St",
                "delivery_date": "2025-11-28",
                "items": [{"quantity": 100}]
            }
        )
        next_handler = AsyncMock()
        
        with pytest.raises(ValueError, match="Item 0 missing part_number"):
            await middleware.process(event, next_handler)


class TestASNEnrichmentMiddleware:
    @pytest.mark.asyncio
    async def test_adds_metadata(self, sample_asn_payload):
        middleware = ASNEnrichmentMiddleware()
        event = Event(
            event_type=EventType.DIRECT_INVOKE,
            function_name="test",
            payload=sample_asn_payload,
            context={"timestamp": "2025-11-27T00:00:00Z"}
        )
        
        enriched_event = None
        async def capture_handler(evt):
            nonlocal enriched_event
            enriched_event = evt
            return {}
        
        await middleware.process(event, capture_handler)
        
        assert "metadata" in enriched_event.payload
        assert enriched_event.payload["metadata"]["source"] == "direct_invoke"
        assert enriched_event.payload["metadata"]["function_name"] == "test"
    
    @pytest.mark.asyncio
    async def test_generates_tracking_number_if_missing(self, sample_asn_payload):
        middleware = ASNEnrichmentMiddleware()
        event = Event(
            event_type=EventType.DIRECT_INVOKE,
            function_name="test",
            payload=sample_asn_payload,
            context={}
        )
        
        enriched_event = None
        async def capture_handler(evt):
            nonlocal enriched_event
            enriched_event = evt
            return {}
        
        await middleware.process(event, capture_handler)
        
        assert "tracking_number" in enriched_event.payload
        assert enriched_event.payload["tracking_number"] == "TRK-SH-2025-001"


class TestASNBatchProcessingMiddleware:
    @pytest.mark.asyncio
    async def test_processes_sqs_batches(self, sample_asn_payload):
        middleware = ASNBatchProcessingMiddleware(batch_size=2)
        event = Event(
            event_type=EventType.SQS,
            function_name="test",
            payload={
                "Records": [
                    {"messageId": "msg-1", "body": sample_asn_payload},
                    {"messageId": "msg-2", "body": sample_asn_payload},
                    {"messageId": "msg-3", "body": sample_asn_payload}
                ]
            }
        )
        next_handler = AsyncMock(return_value={})
        
        result = await middleware.process(event, next_handler)
        
        assert next_handler.call_count == 2
        assert result == {"batchItemFailures": []}
    
    @pytest.mark.asyncio
    async def test_skips_batching_for_non_sqs_events(self, sample_asn_payload):
        middleware = ASNBatchProcessingMiddleware()
        event = Event(
            event_type=EventType.DIRECT_INVOKE,
            function_name="test",
            payload=sample_asn_payload
        )
        next_handler = AsyncMock(return_value={"result": "ok"})
        
        result = await middleware.process(event, next_handler)
        
        assert result == {"result": "ok"}
        next_handler.assert_called_once()
