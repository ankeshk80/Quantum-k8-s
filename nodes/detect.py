import json
import logging
import random
from utils.llm import llm_service

logger = logging.getLogger("k8s-whisperer.nodes.detect")

def detect_node(state):
    print("🔍 Detecting anomalies...")
    
    events = state.get("events", [])
    if not events:
        logger.info("No events to detect anomalies from.")
        return {"anomalies": []}

    system_prompt = """
    You are a Kubernetes SRE specializing in anomaly detection.
    Analyze the provided cluster events and identify real problems.
    Return a list of anomalies in clean JSON format.
    Fields for each anomaly: 
    - type: string (e.g., CrashLoopBackOff, OOMKilled, Pending)
    - severity: string (LOW, MEDIUM, HIGH)
    - affected_resource: string (format "resource_type/name", e.g., "pod/my-app")
    - confidence: float (0.0 to 1.0)
    - reason: string (brief explanation)
    """

    user_prompt = f"Analyze these events:\n{json.dumps(events, indent=2)}\n\nReturn EXACT JSON in format: {{ \"anomalies\": [...] }}"

    raw_response = llm_service.query(system_prompt, user_prompt)
    parsed = llm_service.safe_parse_json(raw_response)
    
    from mcp_tools.prometheus_tools import prometheus_mcp
    
    anomalies = parsed.get("anomalies", [])
    
    # Enrich detection with metric-driven MCP tool audits
    for anomaly in anomalies:
        resource = anomaly.get("affected_resource", "")
        if "pod/" in resource:
            pod_name = resource.split("/")[-1]
            try:
                # ---------------------------------------------------------
                # FEATURE: Prometheus Metric-Driven Detection Audit
                # ---------------------------------------------------------
                mem_util = prometheus_mcp.get_pod_memory_util(pod_name)
                cpu_util = prometheus_mcp.get_pod_cpu_util(pod_name)
                
                # Append live telemetry metrics to the anomaly state
                # In Minikube without Prometheus, this safely returns 0.0 or the mock val
                anomaly["metrics"] = {
                    "memory_mb": round(mem_util, 2),
                    "cpu_util_pct": round(cpu_util, 2)
                }
                
                logger.info(f"📊 Metric Audit for {pod_name}: Mem={mem_util}MB, CPU={cpu_util}%")
                
                # Boost confidence if OOM is detected and metrics show high mem
                if "OOM" in anomaly.get("type", "") and mem_util > 50:
                    anomaly["confidence"] = min(0.99, float(anomaly.get("confidence", 0.9)) + 0.05)
                # ---------------------------------------------------------
            except Exception as e:
                logger.warning(f"Prometheus audit failed for {pod_name}: {e}")

    # Introduce random variance to confidence to diversify identical replica errors visually
    for anomaly in anomalies:
        try:
            base_conf = float(anomaly.get("confidence", 0.90))
        except ValueError:
            base_conf = 0.90
        variance = random.uniform(-0.02, 0.02)
        anomaly["confidence"] = round(min(0.99, max(0.50, base_conf + variance)), 2)

    logger.info(f"Detected {len(anomalies)} anomalies from events and Prometheus audit.")

    return {"anomalies": anomalies}