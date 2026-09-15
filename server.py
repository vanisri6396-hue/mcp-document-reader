from mcp.server import MCPServer

from mcp_interface.tools import register_tools
from mcp_interface.resources import register_resources
from mcp_interface.prompts import register_prompts
from security.logging_config import configure_logging


logger = configure_logging()


mcp = MCPServer("DocumentMCP")


register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)


if __name__ == "__main__":
    logger.info("Starting DocumentMCP server...")
    mcp.run()