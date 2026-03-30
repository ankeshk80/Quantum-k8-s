import requests
import os
import logging
from datetime import datetime

logger = logging.getLogger("k8s-whisperer.slack")

class SlackUtil:
    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    def send_message(self, text: str, blocks: list = None) -> bool:
        """Send message to Slack (non-blocking in error cases)"""
        if not self.webhook_url:
            logger.warning("SLACK_WEBHOOK_URL not set. Skipping notification.")
            return False
            
        payload = {"text": text}
        if blocks:
            payload["blocks"] = blocks
            
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            logger.info("Successfully sent Slack notification")
            return True
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

    def alert_issue(self, pod: str, anomaly_type: str, severity: str):
        """Standard issue alert message"""
        emoji = "🔴" if severity == "HIGH" else "🟡"
        msg = f"{emoji} *Kubernetes Issue Detected*\n\n*Pod:* `{pod}`\n*Type:* `{anomaly_type}`\n*Severity:* `{severity}`\n\n🔍 Investigating..."
        return self.send_message(msg)

    def remediation_started(self, pod: str, action: str):
        """Remediation started message"""
        msg = f"⚡ *Remediation Execution Started*\n\n*Pod:* `{pod}`\n*Action:* `{action}`\n\n🛠️ Applying fix..."
        return self.send_message(msg)

    def remediation_result(self, pod: str, status: str, result_msg: str):
        """Final remediation result message"""
        emoji = "✅" if status == "Recovered" else "❌"
        msg = f"{emoji} *Remediation {status}*\n\n*Pod:* `{pod}`\n*Summary:* {result_msg}\n\n📊 Check cluster status for full details."
        return self.send_message(msg)

    def hitl_request(self, pod: str, diagnosis: str, action: str):
        """HITL approval request message with Block Kit interactive buttons"""
        msg = f"⚠️ *Human Approval Required (HITL)*\n\n*Pod:* `{pod}`\n*Diagnosis:* {diagnosis}\n*Proposed Action:* `{action}`"
        
        # Fulfill Deliverable 2: Slack Request with Approve/Reject buttons
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": msg
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Approve Execute"},
                        "style": "primary",
                        "value": "approve",
                        "action_id": "approve_plan"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "❌ Reject"},
                        "style": "danger",
                        "value": "reject",
                        "action_id": "reject_plan"
                    }
                ]
            }
        ]
        
        return self.send_message(text=msg, blocks=blocks)

slack_service = SlackUtil()
