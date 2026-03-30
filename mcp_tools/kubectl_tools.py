# mcp_tools/kubectl_tools.py
import subprocess
import json
import time

# A helper so we don't repeat subprocess code everywhere
def run_kubectl(args: list[str]) -> str:
    result = subprocess.run(
        ["kubectl"] + args,
        capture_output=True,
        text=True
    )
    # Return stderr too — it often contains the useful error message
    return result.stdout or result.stderr

def get_all_pods() -> list[dict]:
    """
    Fetches all pods across all namespaces as structured data.
    This is what observe_node calls every 30 seconds.
    """
    try:
        output = run_kubectl([
            "get", "pods",
            "--all-namespaces",
            "-o", "json"          # ask kubectl for machine-readable JSON
        ])
        data = json.loads(output)
        
        # We only extract the fields our agent actually needs
        # This keeps ClusterState lean and avoids flooding the LLM
        pods = []
        for item in data.get("items", []):
            pods.append({
                "name": item["metadata"]["name"],
                "namespace": item["metadata"]["namespace"],
                "phase": item["status"].get("phase", "Unknown"),
                "conditions": item["status"].get("conditions", []),
                "containerStatuses": item["status"].get("containerStatuses", []),
                "events": []   # filled in separately by get_pod_events
            })
        return pods
    except Exception as e:
        print(f"Error getting pods: {e}")
        return []

def get_pod_logs(pod_name: str, namespace: str = "default") -> str:
    """Last 100 lines only — avoids context window overflow."""
    return run_kubectl([
        "logs", pod_name,
        "-n", namespace,
        "--tail=100",
        "--previous"   # gets logs from the PREVIOUS crashed container
                       # which is exactly what you want for CrashLoopBackOff
    ])

def get_pod_description(pod_name: str, namespace: str = "default") -> str:
    return run_kubectl(["describe", "pod", pod_name, "-n", namespace])

def restart_pod(pod_name: str, namespace: str = "default") -> str:
    """Restarts a pod by deleting it. Kubernetes will recreate it from the Deployment."""
    return run_kubectl(["delete", "pod", pod_name, "-n", namespace])

def patch_memory_limit(pod_name: str, namespace: str, new_limit: str) -> str:
    """
    Increases the memory limit for a deployment.
    Note: we patch the Deployment, not the Pod directly —
    patching a Pod directly doesn't persist after restart.
    """
    # Get the deployment name from the pod name
    # Pods are named deployment-name-<random-suffix>
    # Safety: check if it matches the pattern or just take the components
    parts = pod_name.split("-")
    if len(parts) > 2:
        deployment = "-".join(parts[:-2])
    else:
        deployment = pod_name
    
    patch = json.dumps({
        "spec": {
            "template": {
                "spec": {
                    "containers": [{
                        "name": deployment,
                        "resources": {
                            "limits": {"memory": new_limit}
                        }
                    }]
                }
            }
        }
    })
    return run_kubectl([
        "patch", "deployment", deployment,
        "-n", namespace,
        "--type=merge",
        "-p", patch
    ])

def verify_pod_health(pod_name: str, namespace: str = "default") -> bool:
    """
    Polls pod status every 10 seconds up to 6 times (60 seconds total).
    Returns True only when pod status becomes Running.
    This is the verify loop the problem statement requires.
    """
    for attempt in range(6):
        output = run_kubectl([
            "get", "pod", pod_name,
            "-n", namespace,
            "-o", "jsonpath={.status.phase}"
        ])
        if output.strip() == "Running":
            return True
        # Exponential backoff — wait longer each time
        time.sleep(10 * (attempt + 1))
    return False
