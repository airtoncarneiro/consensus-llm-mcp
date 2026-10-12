from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp_types import ToolAnnotations
from pydantic import Field

from consensus import DeliberationResult, run_consensus, run_consensus_deliberate


MAX_PROMPT_LENGTH = 8_000
Prompt = Annotated[
    str,
    Field(
        min_length=1,
        max_length=MAX_PROMPT_LENGTH,
        description=(
            "Question or task to evaluate. Do not include secrets or unnecessary "
            "personal data because the prompt is sent to configured external models."
        ),
    ),
]
EXTERNAL_MODEL_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=True,
)


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


@mcp.tool(
    title="Generate a multi-model consensus answer",
    description=(
        "Use when the user wants one consolidated answer from configured external "
        "models. Sends the supplied prompt to OpenRouter-backed models, performs "
        "peer review and synthesis, and may incur provider usage charges. Does not "
        "modify project or user data."
    ),
    annotations=EXTERNAL_MODEL_ANNOTATIONS,
)
def consensus(prompt: Prompt) -> str:
    return run_consensus(prompt)


@mcp.tool(
    title="Deliberate across multiple external models",
    description=(
        "Use when the user wants to inspect a multi-model deliberation before a "
        "client produces its own final answer. Sends the supplied prompt to "
        "OpenRouter-backed models, performs generation, peer review, and revision, "
        "and may incur provider usage charges. Returns initial_responses, "
        "peer_reviews, revised_responses, and revision_summary; it does not return "
        "a final synthesis or modify project or user data."
    ),
    annotations=EXTERNAL_MODEL_ANNOTATIONS,
    structured_output=True,
)
def consensus_deliberate(prompt: Prompt) -> DeliberationResult:
    return run_consensus_deliberate(prompt)


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=3000,
    )
