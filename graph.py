from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from state import ClusterState

from nodes.observe import observe_node
from nodes.detect import detect_node
from nodes.diagnose import diagnose_node
from nodes.plan import plan_node
from nodes.safety import safety_router
from nodes.execute import execute_node
from nodes.explain import explain_node
from nodes.hitl import hitl_node

def build_graph():
    g = StateGraph(ClusterState)

    # Define Nodes
    g.add_node("observe", observe_node)
    g.add_node("detect", detect_node)
    g.add_node("diagnose", diagnose_node)
    g.add_node("plan", plan_node)
    g.add_node("hitl", hitl_node)
    g.add_node("execute", execute_node)
    g.add_node("explain", explain_node)

    # Define Workflows
    g.add_edge("observe", "detect")
    g.add_edge("detect", "diagnose")
    g.add_edge("diagnose", "plan")

    # Safety Gate Logic
    g.add_conditional_edges("plan", safety_router, {
        "execute": "execute",
        "hitl": "hitl",
        "explain": "explain"
    })
    
    g.add_edge("hitl", "execute")
    g.add_edge("execute", "explain")

    g.set_entry_point("observe")

    return g.compile(checkpointer=MemorySaver(), interrupt_before=["hitl"])