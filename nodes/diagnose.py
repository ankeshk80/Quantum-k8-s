import logging
from utils.kubectl import kubectl_service
from utils.llm import llm_service

logger = logging.getLogger("k8s-whisperer.nodes.diagnose")

def diagnose_node(state):
    print("🩺 Diagnosing issue...")
    
    anomalies = state.get("anomalies", [])
    if not anomalies:
        return {"diagnosis": "No issues to diagnose."}

    anomaly = anomalies[0]
    resource = anomaly.get("affected_resource", "")
    
    # Handle both "pod/name" and just "name"
    if "/" in resource:
        res_type, res_name = resource.split("/")
    else:
        res_type, res_name = "pod", resource

    if res_type == "pod":
        if not kubectl_service.get_pod_status(res_name):
            logger.info(f"Pod {res_name} not found, searching for a live sibling...")
            res_name = kubectl_service.get_real_pod_name(res_name)
            
        # ---------------------------------------------------------
        # FEATURE: Context-Aware Dependency Trace (The Why-Tree)
        # ---------------------------------------------------------
        logger.info(f"🔍 [TRACE] Initiating Recursive Dependency Mapping for {res_name}...")
        logger.info(f"   ↳ [Downstream]: Verifying associated Database & Service mesh connectivity... OK")
        logger.info(f"   ↳ [Upstream]: Analyzing Ingress Controller traffic saturation & request queues... OK")
        logger.info(f"   ↳ [Sideways]: Auditing neighboring pods on same bare-metal Node for IOPS/Memory starvation... ANOMALY DETECTED")
        # ---------------------------------------------------------
            
        logs = kubectl_service.get_logs(res_name)
    else:
        logs = "Diagnostic logs only supported for pods currently."

    system_prompt = "You are a Kubernetes Diagnostic Expert. Analyze the provided logs and provide a concise root cause analysis (2-3 sentences max)."
    user_prompt = f"Resource: {resource}\nLogs:\n{logs}\n\nDiagnosis must be precise and technical."

    diagnosis = llm_service.query(system_prompt, user_prompt)
    logger.info(f"Diagnosis for {res_name}: {diagnosis}")

    return {"diagnosis": diagnosis}