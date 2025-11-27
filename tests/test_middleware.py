"""Tests for middleware."""
import pytest
from unittest.mock import AsyncMock

from shim.events.dispatcher import Event, EventType
from shim.middleware.base import Middleware, MiddlewareChain
from shim.middleware.common import LoggingMiddleware, ValidationMiddleware, AuthMiddleware


class RecordingMiddleware(Middleware):
    """Test middleware that records calls."""
    
    def __init__(self, name):
        self.name = name
        self.called = False
    
    async def process(self, event, next_handler):
        self.called = True
        return await next_handler(event)


class TestMiddlewareChain:
    @pytest.mark.asyncio
    async def test_executes_middleware_in_order(self):
        mw1 = RecordingMiddleware("first")
        mw2 = RecordingMiddleware("second")
        chain = MiddlewareChain([mw1, mw2])
        
        final_handler = AsyncMock(return_value={"success": True})
        event = Event(
            event_type=EventType.DIRECT_INVOKE,
            function_name="test",
            payload={}
        )
        
        result = await chain.execute(event, final_handler)
        
        assert mw1.called
        assert mw2.called
        assert result == {"success": True}
        final_handler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_can_add_middleware(self):
        chain = MiddlewareChain()
        mw = RecordingMiddleware("test")
        
        chain.add(mw)
        
        assert len(chain.middlewares) == 1
        assert chain.middlewares[0] == mw


class TestValidationMiddleware:
    @pytest.mark.asyncio
    async def test_raises_error_for_missing_function_name(self):
        middleware = ValidationMiddleware()
        event = Event(
            event_type=EventType.DIRECT_INVOKE,
            function_name="",
            payload={}
        )
        next_handler = AsyncMock()
        
        with pytest.raises(ValueError, match="function_name is required"):
            await middleware.process(event, next_handler)
    
    @pytest.mark.asyncio
    async def test_allows_valid_event(self):
        middleware = ValidationMiddleware()
        event = Event(
            event_type=EventType.DIRECT_INVOKE,
            function_name="test",
            payload={"data": "value"}
        )
        next_handler = AsyncMock(return_value={})
        
        result = await middleware.process(event, next_handler)
        
        next_handler.assert_called_once()
        assert result == {}


class TestAuthMiddleware:
    @pytest.mark.asyncio
    async def test_allows_request_with_valid_api_key(self):
        middleware = AuthMiddleware(api_keys={"valid-key"})
        event = Event(
            event_type=EventType.DIRECT_INVOKE,
            function_name="test",
            payload={},
            context={"api_key": "valid-key"}
        )
        next_handler = AsyncMock(return_value={"authorized": True})
        
        result = await middleware.process(event, next_handler)
        
        assert result == {"authorized": True}
    
    @pytest.mark.asyncio
    async def test_rejects_request_with_invalid_api_key(self):
        middleware = AuthMiddleware(api_keys={"valid-key"})
        event = Event(
            event_type=EventType.DIRECT_INVOKE,
            function_name="test",
            payload={},
            context={"api_key": "invalid-key"}
        )
        next_handler = AsyncMock()
        
        with pytest.raises(PermissionError, match="Invalid API key"):
            await middleware.process(event, next_handler)
    
    @pytest.mark.asyncio
    async def test_bypasses_auth_when_no_keys_configured(self):
        middleware = AuthMiddleware()
        event = Event(
            event_type=EventType.DIRECT_INVOKE,
            function_name="test",
            payload={},
            context={}
        )
        next_handler = AsyncMock(return_value={})
        
        result = await middleware.process(event, next_handler)
        
        next_handler.assert_called_once()
