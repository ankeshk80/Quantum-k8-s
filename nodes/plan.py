import json
import logging
from utils.llm import llm_service

logger = logging.getLogger("k8s-whisperer.nodes.plan")

def plan_node(state):
    print("🧠 Planning fix...")
    
    diagnosis = state.get("diagnosis", "")
    anomalies = state.get("anomalies", [])
    if not anomalies:
        return {"plan": {}}
        
    anomaly = anomalies[0]

    system_prompt = """
    You are a Kubernetes SRE. Given a diagnosis, propose a remediation plan.
    Return JSON with fields:
    - action: string (e.g., restart_pod, rollout_undo, scale_up)
    - target: string (the resource name. IMPORTANT: if affected resource is a pod with random suffix like 'app-123-abc', return the base app name 'app')
    - namespace: string
    - parameters: dict (extra params)
    - confidence: float (0.0 to 1.0)
    - blast_radius: string (IMPORTANT: CrashLoopBackOff MUST be 'low', OOMKilled MUST be 'medium', and unfixable Pending issues MUST be 'high')
    """

    user_prompt = f"Diagnosis: {diagnosis}\nAffected Resource: {anomaly.get('affected_resource', 'unknown')}\n\nReturn EXACT JSON response."

    raw_response = llm_service.query(system_prompt, user_prompt)
    plan = llm_service.safe_parse_json(raw_response)
    
    logger.info(f"Generated remediation plan: {plan.get('action', 'none')}")
    
    return {"plan": plan}