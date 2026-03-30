import subprocess
import json
import logging
import time

logger = logging.getLogger("k8s-whisperer.kubectl")

class KubectlUtil:
    def __init__(self, timeout=30):
        self.timeout = timeout

    def run(self, cmd_args: list) -> str:
        """Run a kubectl command with timeout, error handling and status code checking"""
        full_cmd = ["kubectl"] + cmd_args
        try:
            logger.info(f"Running command: {' '.join(full_cmd)}")
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False
            )
            
            if result.returncode != 0:
                logger.warning(f"Kubectl Command Failed: {' '.join(full_cmd)} \nError: {result.stderr}")
                return ""
            
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.error(f"Kubectl Command Timeout: {' '.join(full_cmd)}")
            return ""
        except Exception as e:
            logger.error(f"Kubectl Command Exception: {e}")
            return ""

    def run_command(self, cmd_string: str) -> str:
        """Run a raw command string. Trims leading 'kubectl ' if present."""
        if cmd_string.startswith("kubectl "):
            cmd_string = cmd_string[8:]
        import shlex
        return self.run(shlex.split(cmd_string))

    def get_events(self) -> list:
        """Fetch cluster events in JSON format"""
        raw = self.run(["get", "events", "-o", "json"])
        if raw:
            try:
                data = json.loads(raw)
                return data.get("items", [])
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse events JSON: {raw[:100]}...")
        return []

    def get_logs(self, pod: str, namespace="default", previous=True) -> str:
        """Fetch pod logs"""
        args = ["logs", pod, "-n", namespace]
        if previous:
            args.append("--previous")
        
        logs = self.run(args)
        if not logs:
            # Try without previous if previous failed
            args = ["logs", pod, "-n", namespace]
            logs = self.run(args)
            
        return logs or "No logs available"

    def get_real_pod_name(self, target: str, namespace="default") -> str:
        """Lookup full pod name using label OR return name if it already exists"""
        # 1. Try if target exists as a pod directly
        status = self.run(["get", "pod", target, "-n", namespace, "-o", "name"])
        if status:
            return target
            
        # 2. Try as a label
        raw = self.run([
            "get", "pods", "-n", namespace, 
            "-l", f"app={target}", 
            "-o", "jsonpath={.items[0].metadata.name}"
        ])
        if raw:
            return raw.strip()
            
        # 3. Try partial match/stripping suffix (for hackathon robustness)
        # If target is "app-name-suffix1-suffix2", try "app-name"
        if "-" in target:
            base = "-".join(target.split("-")[:-2])
            if base:
                raw = self.run([
                    "get", "pods", "-n", namespace, 
                    "-l", f"app={base}", 
                    "-o", "jsonpath={.items[0].metadata.name}"
                ])
                return raw.strip() if raw else ""
                
        return ""

    def get_pod_status(self, pod_name: str, namespace="default") -> str:
        """Get pod status phase"""
        status = self.run([
            "get", "pod", pod_name, "-n", namespace,
            "-o", "jsonpath={.status.phase}"
        ])
        return status.strip() if status else "Unknown"

    def delete_pod(self, pod_name: str, namespace="default") -> bool:
        """Delete a pod"""
        result = self.run(["delete", "pod", pod_name, "-n", namespace])
        return bool(result)

    def wait_for_pod_ready(self, target: str, namespace="default", attempts=8, backoff=5) -> bool:
        """Wait for pod to be running with exponential backoff"""
        # Extract base app name if it's a full pod name
        app_label = target
        if "-" in target and len(target.split("-")) > 2:
             app_label = "-".join(target.split("-")[:-2])

        for i in range(attempts):
            # Try finding ANY pod for this app label
            real_pod = self.get_real_pod_name(app_label, namespace)
            if real_pod:
                status = self.get_pod_status(real_pod, namespace)
                logger.info(f"Verification attempt {i+1} for {app_label}: {status}")
                if status == "Running":
                    return True
            
            wait_time = backoff + (i * 2)
            time.sleep(wait_time)
            
        return False

kubectl_service = KubectlUtil()
