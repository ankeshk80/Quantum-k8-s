# nodes/hitl.py
from state import ClusterState

def hitl_node(state: ClusterState) -> dict:
    """
    Stage 5: Human-In-The-Loop.
    In LangGraph, we can use an interrupt to pause execution.
    This node acts as a placeholder for human intervention.
    """
    print("⚠️ [HITL] Waiting for human approval...")
    # Typically, you'd send a Slack message here with a button.
    # For now, we'll assume the approval will come from the graph state
    # when the user resumes with state['approved'] = True
    
    # We can add a simple instruction for the user in the CLI
    print(f"Proposed Plan: {state['plan'].get('action')} on {state['plan'].get('target')}")
    print(f"Diagnosis: {state['diagnosis']}")
    
    # After the human approves, the graph re-enters here and transitions to execute.
    return {"approved": True}
