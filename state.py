from typing import TypedDict

class Anomaly(TypedDict):
    type: str
    severity: str
    affected_resource: str
    confidence: float
    reason: str

class RemediationPlan(TypedDict):
    action: str
    target: str
    namespace: str
    parameters: dict
    confidence: float
    blast_radius: str

class LogEntry(TypedDict):
    timestamp: str
    anomaly_type: str
    diagnosis: str
    action_taken: str
    result: str
    approved_by: str

class ClusterState(TypedDict):
    events: list[dict]
    anomalies: list[Anomaly]
    diagnosis: str
    plan: RemediationPlan
    approved: bool
    result: str
    audit_log: list[LogEntry]