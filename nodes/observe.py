import logging
from utils.kubectl import kubectl_service

logger = logging.getLogger("k8s-whisperer.nodes.observe")

def observe_node(state):
    print("👀 Observing cluster...")
    logger.info("Fetching real cluster events via kubectl")

    # Fetch real events
    all_events = kubectl_service.get_events()
    relevant_events = []
    
    # K8s events often mask OOMKilled as generic BackOffs. 
    # To reliably catch OOMKilled for the LLM, we must inspect actual pod statuses.
    try:
        pods_out = kubectl_service.run_command("kubectl get pods -A -o json")
        pods_data = __import__("json").loads(pods_out)
        for item in pods_data.get("items", []):
            pod_name = item.get("metadata", {}).get("name", "unknown")
            ns = item.get("metadata", {}).get("namespace", "default")
            statuses = item.get("status", {}).get("containerStatuses", [])
            
            for status in statuses:
                state = status.get("state", {})
                last_state = status.get("lastState", {})
                
                term = state.get("terminated", {})
                wait = state.get("waiting", {})
                last_term = last_state.get("terminated", {})
                
                # Check for OOMKilled aggressively across all states to guarantee extraction
                all_reasons = [last_term.get("reason"), term.get("reason"), wait.get("reason")]
                
                if "OOMKilled" in all_reasons:
                    reason = "OOMKilled"
                else:
                    reason = wait.get("reason") or term.get("reason") or last_term.get("reason")

                if reason in ["OOMKilled", "CrashLoopBackOff", "CreateContainerConfigError", "Error"]:
                    # We map "Error" generically back to "CrashLoopBackOff" for the LLM's understanding
                    if reason == "Error":
                        reason = "CrashLoopBackOff"
                        
                    relevant_events.append({
                        "pod": pod_name,
                        "namespace": ns,
                        "reason": reason,
                        "message": f"Container {status.get('name')} is in {reason} state.",
                        "lastTimestamp": term.get("finishedAt") or last_term.get("finishedAt") or ""
                    })
    except Exception as e:
        logger.error(f"Failed to inspect pod container statuses: {str(e)}")

    # Add any explicit Warning events from the cluster event stream
    for event in all_events:
        if event.get("type") == "Warning" and "FailedScheduling" in event.get("reason", ""):
            relevant_events.append({
                "pod": event.get("involvedObject", {}).get("name", "unknown"),
                "namespace": event.get("involvedObject", {}).get("namespace", "default"),
                "reason": event.get("reason", ""),
                "message": event.get("message", ""),
                "lastTimestamp": event.get("lastTimestamp", "")
            })
            
    return {"events": relevant_events}