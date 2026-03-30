import logging

logger = logging.getLogger("k8s-whisperer.nodes.explain")

def explain_node(state):
    print("📝 Finalizing explanation...")
    
    anomalies = state.get("anomalies", [])
    result = state.get("result", "Unknown")
    
    if not anomalies:
        summary = "No anomalies were detected. The cluster appears healthy."
    else:
        summary = f"The agent detected {len(anomalies)} anomalies and attempted remediation. Final result: {result}."
        
    logger.info(f"Agent Run Summary: {summary}")
    
    # Fulfill Deliverable 3: Persistent JSON Audit Trail
    if anomalies:
        try:
            import json, os
            from datetime import datetime
            
            audit_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "anomalies": anomalies,
                "diagnosis": state.get("diagnosis", ""),
                "action_taken": state.get("plan", {}).get("action", "None"),
                "blast_radius": state.get("plan", {}).get("blast_radius", "None"),
                "explanation": summary,
                "final_status": result
            }
            
            log_path = "audit_log.json"
            logs = []
            if os.path.exists(log_path):
                with open(log_path, "r") as f:
                    logs = json.load(f)
            
            logs.append(audit_entry)
            
            with open(log_path, "w") as f:
                json.dump(logs, f, indent=4)
                
            logger.info("✅ Appended incident record to persistent audit_log.json")
        except Exception as e:
            logger.error(f"Failed to write to audit JSON: {e}")
    
    return {
        "explanation": summary,
        "result": result
    }