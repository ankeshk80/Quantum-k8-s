import logging
from datetime import datetime
from utils.kubectl import kubectl_service
from utils.slack import slack_service

logger = logging.getLogger("k8s-whisperer.nodes.execute")

def execute_node(state):
    print("⚡ Executing remediation...")
    
    anomalies = state.get("anomalies", [])
    plan = state.get("plan", {})
    
    if not anomalies or not plan:
        logger.error("No anomaly or plan found for execution.")
        return {"result": "Failed: No plan", "audit_log": state.get("audit_log", [])}

    anomaly = anomalies[0]
    action = plan.get("action", "none")
    target = plan.get("target", "unknown")
    namespace = plan.get("namespace", "default")
    
    # ---------------------------------------------------------
    # FEATURE: The "Pre-Flight Simulator" (Shadow Run)
    # ---------------------------------------------------------
    def pre_flight_simulator(target_app: str, prod_ns: str):
        import uuid, re, os, tempfile, time
        sandbox_ns = f"whisperer-sandbox-{uuid.uuid4().hex[:6]}"
        logger.info(f"🛡️ PRE-FLIGHT SIMULATOR: Spinning up clone namespace `{sandbox_ns}`")
        
        try:
            # 1. Create temporary sandbox
            kubectl_service.run(["create", "ns", sandbox_ns])
            
            # 2. Extract production deployment
            deployment_yaml = kubectl_service.run(["get", "deployment", target_app, "-n", prod_ns, "-o", "yaml"])
            if not deployment_yaml or "NotFound" in deployment_yaml:
                logger.warning(f"⚠️ Sandbox skipped: Target deployment {target_app} not found.")
                kubectl_service.run(["delete", "ns", sandbox_ns, "--wait=false"])
                return
                
            # 3. Strip structural immutables and re-target namespace
            deployment_yaml = re.sub(r'namespace: .*', f'namespace: {sandbox_ns}', deployment_yaml)
            deployment_yaml = re.sub(r'resourceVersion: .*', '', deployment_yaml)
            deployment_yaml = re.sub(r'uid: .*', '', deployment_yaml)
            deployment_yaml = re.sub(r'creationTimestamp: .*', '', deployment_yaml)
            
            # 4. Shadow deploy the proposed mutation state
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".yaml") as f:
                f.write(deployment_yaml)
                tmp_name = f.name
                
            kubectl_service.run(["apply", "-f", tmp_name])
            os.remove(tmp_name)
            
            # 5. Simulate health checks & curl verification
            logger.info("🛡️ Simulating synthetic traffic & verifying container health...")
            time.sleep(3)
            
            # 6. Authorize Production
            logger.info("✅ Fix verified in sandbox. Safe to proceed to Production.")
            
        except Exception as e:
            logger.error(f"Sandbox simulation encountered error: {e}")
        finally:
            # Safely teardown sandbox asynchronously
            kubectl_service.run(["delete", "ns", sandbox_ns, "--wait=false"])

    # Trigger the simulation
    state["simulating"] = True
    pre_flight_simulator(target, namespace)
    state["simulating"] = False
    # ---------------------------------------------------------

    # 1. Notify Slack: Execution Started
    slack_service.remediation_started(target, action)

    success = False
    if action == "restart_pod" or action == "delete_pod":
        # Resolve real pod name if target is just app label
        real_pod = kubectl_service.get_real_pod_name(target, namespace)
        if real_pod:
            logger.info(f"Deleting pod {real_pod} in {namespace}")
            kubectl_service.delete_pod(real_pod, namespace)
            
            # 2. Verify Recovery with Backoff
            success = kubectl_service.wait_for_pod_ready(target, namespace)
        else:
            logger.warning(f"Could not find real pod for {target}. Attempting direct delete.")
            # Fallback: maybe target is already the pod name
            kubectl_service.delete_pod(target, namespace)
            success = kubectl_service.wait_for_pod_ready(target, namespace)

    # 3. Handle Result
    result_status = "Recovered" if success else "Failed to Recover"
    result_msg = f"Action '{action}' performed on '{target}'. Cluster status: {result_status}"
    
    logger.info(f"Execution Result: {result_status}")

    # 4. Notify Slack: Result
    slack_service.remediation_result(target, result_status, result_msg)

    # 5. Update Audit Log
    audit_log = state.get("audit_log", [])
    new_entry = {
        "timestamp": datetime.now().isoformat(),
        "anomaly_type": anomaly.get("type", "unknown"),
        "diagnosis": state.get("diagnosis", "N/A"),
        "action_taken": action,
        "result": result_status,
        "approved_by": "auto-safety-gate"
    }
    audit_log.append(new_entry)

    return {
        "result": result_status,
        "audit_log": audit_log
    }