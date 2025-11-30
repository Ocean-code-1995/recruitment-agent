"""
Google Calendar MCP Server - Pure MCP Implementation

This server provides MCP (Model Context Protocol) tools for interacting with Google Calendar.
"""

import sys
import os
import logging
import asyncio

# Configure logging first to capture any startup errors
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path to ensure imports work in all environments
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    logger.info(f"Added {parent_dir} to Python path")

from .mcp_bridge import create_mcp_server

# MCP server is created in mcp_bridge.py and instantiated in main() below


async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Google Calendar MCP Server...")
    
    # Create the MCP server with all tools
    mcp = create_mcp_server()
    
    # Run the server
    logger.info("MCP server initialized and starting...")
    async with mcp.run() as resources:
        logger.info("MCP server is running")
        await mcp.wait_for_shutdown()


if __name__ == "__main__":
    asyncio.run(main())