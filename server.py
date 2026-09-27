from mcp.server.mcpserver import MCPServer

from consensus import DeliberationResult, run_consensus, run_consensus_deliberate


mcp = MCPServer(
    "consensus-llm",
    instructions=(
        "This MCP server provides a multi-model consensus response. "
        "When the user asks to use consensus-llm, call the consensus tool with "
        "the user's original prompt. The consensus tool performs model generation, "
        "peer review, and final synthesis internally. "
        "Return the final answer produced by the consensus tool without performing "
        "additional model comparison or synthesis yourself. The "
        "consensus_deliberate tool instead returns the complete deliberation record "
        "for client-side synthesis; it never returns a final synthesized answer."
    ),
)


@mcp.tool()
def consensus(prompt: str) -> str:
    """
    Run a multi-model consensus process and return one consolidated final answer.

    Three configured models independently answer the prompt, independently
    peer-review the available initial responses, and a configured synthesizer
    model produces the final consolidated answer.
    """
    return run_consensus(prompt)


@mcp.tool()
def consensus_deliberate(prompt: str) -> DeliberationResult:
    """Return an ordered three-round record without final synthesis.

    The result always contains initial_responses, peer_reviews,
    revised_responses, and revision_summary. A model is omitted only from the
    round it failed; revised_responses and revision_summary have identical keys.
    """
    return run_consensus_deliberate(prompt)


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=3000,
    )
