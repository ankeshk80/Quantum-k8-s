import requests
import os
import logging
from typing import Optional, Dict

logger = logging.getLogger("k8s-whisperer.mcp_tools.prometheus")

class PrometheusMCP:
    def __init__(self, url: Optional[str] = None):
        self.url = url or os.getenv("PROMETHEUS_URL", "http://localhost:9090")
        
    def query(self, promql: str) -> Dict:
        """Execute a raw PromQL query."""
        try:
            response = requests.get(f"{self.url}/api/v1/query", params={"query": promql}, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Prometheus query failed: {e}")
            return {"status": "error", "data": {"result": []}}

    def get_pod_memory_util(self, pod_name: str, namespace: str = "default") -> float:
        """Fetch memory usage bytes for a specific pod."""
        query = f'sum(container_memory_usage_bytes{{pod="{pod_name}",namespace="{namespace}"}})'
        result = self.query(query)
        try:
            val = result['data']['result'][0]['value'][1]
            return float(val) / (1024 * 1024) # Return in MB
        except (IndexError, KeyError):
            return 0.0

    def get_pod_cpu_util(self, pod_name: str, namespace: str = "default") -> float:
        """Fetch CPU usage for a specific pod."""
        query = f'sum(rate(container_cpu_usage_seconds_total{{pod="{pod_name}",namespace="{namespace}"}}[5m]))'
        result = self.query(query)
        try:
            val = result['data']['result'][0]['value'][1]
            return float(val) * 100 # Return as percentage equivalent
        except (IndexError, KeyError):
            return 0.0

prometheus_mcp = PrometheusMCP()
