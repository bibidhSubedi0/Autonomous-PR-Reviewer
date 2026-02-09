from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.nodes import clone_node, linter_node, ai_review_node, cleanup_node

def should_continue(state: AgentState):
    """Decides if we proceed to AI or abort."""
    # For now, we always go to AI now, even if Linter fails.
    return "ai_review"



workflow = StateGraph(AgentState)

# 1. Add Nodes
workflow.add_node("clone", clone_node)
workflow.add_node("linter", linter_node)
workflow.add_node("ai_review", ai_review_node)
workflow.add_node("cleanup", cleanup_node)

# 2. Add Edges (The Flow)
workflow.set_entry_point("clone")
workflow.add_edge("clone", "linter")

# 3. Conditional Edge (The Decision)
workflow.add_conditional_edges(
    "linter",
    should_continue,
    {
        "cleanup": "cleanup",      # If lint failed, go to cleanup
        "ai_review": "ai_review"   # If lint passed, go to AI
    }
)

workflow.add_edge("ai_review", "cleanup")
workflow.add_edge("cleanup", END)

# 4. Compile
app = workflow.compile()