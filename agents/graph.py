from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.nodes import clone_node, linter_node, ai_review_node, cleanup_node


def should_continue(state: AgentState) -> str:
    """
    Routes after the linter node.

    FIX: The old version was hardcoded to always return "ai_review", making
    the "cleanup" (abort) branch permanently dead code. Now it actually reads
    review_status and skips AI review when the clone itself failed.
    """
    status = state.get("review_status", "")

    # If cloning failed there is no local_path or diff — nothing for AI to do.
    if status == "failed":
        return "cleanup"

    # lint_failed is intentionally routed to AI: let Gemini review the diff
    # even when the linter complains (lint errors are already stored in state).
    return "ai_review"


workflow = StateGraph(AgentState)

# 1. Add Nodes
workflow.add_node("clone", clone_node)
workflow.add_node("linter", linter_node)
workflow.add_node("ai_review", ai_review_node)
workflow.add_node("cleanup", cleanup_node)

# 2. Linear edges
workflow.set_entry_point("clone")
workflow.add_edge("clone", "linter")

# 3. Conditional edge after linter
workflow.add_conditional_edges(
    "linter",
    should_continue,
    {
        "cleanup": "cleanup",       # Clone failed -> skip AI, just clean up
        "ai_review": "ai_review",   # lint_passed or lint_failed -> run AI
    },
)

workflow.add_edge("ai_review", "cleanup")
workflow.add_edge("cleanup", END)

# 4. Compile
app = workflow.compile()