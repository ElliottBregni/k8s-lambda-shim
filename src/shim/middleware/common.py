"""Common middleware implementations."""
import logging
from typing import Any

from .base import Middleware, HandlerFunc, ResponseType
from ..events.dispatcher import Event

logger = logging.getLogger(__name__)

class LoggingMiddleware(Middleware):
 async def process(self, event: Event, next_handler: HandlerFunc) -> ResponseType:
 logger.info(f"Processing {event.event_type} for {event.function_name}")
 try:
 response = await next_handler(event)
 logger.info(f"Successfully processed {event.function_name}")
 return response
 except Exception as e:
 logger.error(f"Error processing {event.function_name}: {e}")
 raise

class ValidationMiddleware(Middleware):
 async def process(self, event: Event, next_handler: HandlerFunc) -> ResponseType:
 if not event.function_name:
 raise ValueError("function_name is required")

 if not event.payload:
 logger.warning(f"Empty payload for {event.function_name}")

 return await next_handler(event)

class AuthMiddleware(Middleware):
 def __init__(self, api_keys: set[str] | None = None):
 self.api_keys = api_keys or set()

 async def process(self, event: Event, next_handler: HandlerFunc) -> ResponseType:
 if not self.api_keys:
 return await next_handler(event)

 api_key = event.context.get("api_key")
 if api_key not in self.api_keys:
 raise PermissionError("Invalid API key")

 return await next_handler(event)
