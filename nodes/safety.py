import logging

logger = logging.getLogger("k8s-whisperer.safety")

def safety_router(state):
    plan = state.get("plan", {})
    
    confidence = float(plan.get("confidence", 0))
    blast_radius = plan.get("blast_radius", "high").lower()

    # Safety limits: High confidence AND Low blast radius
    if confidence >= 0.8 and blast_radius == "low":
        logger.info(f"✅ Safe confidence ({confidence}) & radius ({blast_radius}). Proceeding to execute.")
        return "execute"
        
    if blast_radius == "medium":
        logger.warning(f"⚠️ Medium Blast Radius. Routing to Human-In-The-Loop.")
        from utils.slack import slack_service
        slack_service.hitl_request(
            pod=plan.get("target", "unknown"),
            diagnosis=state.get("diagnosis", "N/A"),
            action=plan.get("action", "unknown")
        )
        return "hitl"

    logger.warning(f"⚠️ Safety check failed: Confidence={confidence}, BlastRadius={blast_radius}. Needs manual intervention.")
    # In a real production system, this would go to a human node (hitl)
    # For hackathon, we could route to "explain" or a dedicated "failed_safety" node
    return "explain"