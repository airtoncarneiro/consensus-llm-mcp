from mcp.server.mcpserver import MCPServer

from arena import run_arena


mcp = MCPServer(
    "consensus-llm",
    instructions=(
        "This MCP server provides a multi-model response arena. "
        "When the user asks to use the Arena, call the arena tool with the "
        "user's original prompt. The arena tool performs model generation, "
        "peer review, and final synthesis internally. "
        "Return the final answer produced by the arena tool without performing "
        "additional model comparison or synthesis yourself."
    ),
)


@mcp.tool()
def arena(prompt: str) -> str:
    """
    Run a multi-model response arena and return one consolidated final answer.

    Three configured models independently answer the prompt, independently
    peer-review the available initial responses, and a configured synthesizer
    model produces the final consolidated answer.
    """
    return run_arena(prompt)


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=3000,
    )
