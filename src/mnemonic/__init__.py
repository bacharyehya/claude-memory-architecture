"""
Mnemonic - AI Memory MCP Server

Persistent memory management for Claude and other AI assistants.
"""

__version__ = "0.1.0"

from mnemonic.server import mcp, main

__all__ = ["mcp", "main", "__version__"]
