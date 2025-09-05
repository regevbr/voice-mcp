"""
Mock MCP implementation for development and testing purposes.
This will be replaced with the actual MCP package when available.
"""

from typing import Dict, Any, List, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class MockFastMCP:
    """Mock FastMCP server for development."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._tools = []
        self._prompts = []
        
    def tool(self):
        """Decorator for registering tools."""
        def decorator(func: Callable) -> Callable:
            self._tools.append(func)
            logger.debug(f"Registered tool: {func.__name__}")
            return func
        return decorator
    
    def prompt(self):
        """Decorator for registering prompts."""
        def decorator(func: Callable) -> Callable:
            self._prompts.append(func)
            logger.debug(f"Registered prompt: {func.__name__}")
            return func
        return decorator
    
    def run(self, transport: str = "stdio", host: str = "localhost", port: int = 8000, debug: bool = False):
        """Mock run method."""
        logger.info(f"Mock MCP server '{self.name}' would run on {transport}://{host}:{port}")
        logger.info(f"Registered {len(self._tools)} tools and {len(self._prompts)} prompts")
        
        if transport == "stdio":
            logger.info("Would run with stdio transport (suitable for Claude Desktop)")
        elif transport == "sse":
            logger.info(f"Would run with SSE transport on http://{host}:{port}")
        else:
            raise ValueError(f"Unsupported transport: {transport}")


# Mock the mcp.server.fastmcp module
class MockFastMCPModule:
    FastMCP = MockFastMCP