"""Base middleware framework."""
from typing import Any, Callable, Awaitable
from abc import ABC, abstractmethod

from ..events.dispatcher import Event


ResponseType = dict[str, Any]
HandlerFunc = Callable[[Event], Awaitable[ResponseType]]


class Middleware(ABC):
    @abstractmethod
    async def process(self, event: Event, next_handler: HandlerFunc) -> ResponseType:
        pass


class MiddlewareChain:
    def __init__(self, middlewares: list[Middleware] | None = None):
        self.middlewares = middlewares or []
    
    def add(self, middleware: Middleware):
        self.middlewares.append(middleware)
    
    async def execute(self, event: Event, final_handler: HandlerFunc) -> ResponseType:
        async def create_chain(index: int) -> HandlerFunc:
            if index >= len(self.middlewares):
                return final_handler
            
            middleware = self.middlewares[index]
            next_handler = await create_chain(index + 1)
            
            async def handler(evt: Event) -> ResponseType:
                return await middleware.process(evt, next_handler)
            
            return handler
        
        chain = await create_chain(0)
        return await chain(event)
