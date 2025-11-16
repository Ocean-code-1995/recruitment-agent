import logging
from src.mcp_bridge import create_mcp_server

# Optional: keep logging simple and clean
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

def main():
    """Start the MCP server over stdio."""
    server = create_mcp_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
