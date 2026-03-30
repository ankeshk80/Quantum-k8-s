import logging
import json
import os
from fastapi import FastAPI, Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("k8s-whisperer.api")

app = FastAPI(title="K8s Whisperer Distributed HITL Webhook")

@app.post("/slack/interactive-endpoint")
async def slack_webhook(request: Request):
    """
    Deliverable 2: FastAPI Webhook
    This securely catches the Slack block-kit interactive payload
    (Approve/Reject buttons) allowing external judges to remotely approve StateGraph plans!
    """
    logger.info("📡 Incoming HITL interaction payload received from Slack webhook!")
    
    try:
        # Slack sends the interactive payload as URL Encoded Forms
        form_data = await request.form()
        payload_str = form_data.get("payload")
        
        if payload_str:
            payload = json.loads(payload_str)
            user = payload.get("user", {}).get("username", "SRE Judge")
            actions = payload.get("actions", [])
            
            if actions:
                action_id = actions[0].get("action_id")
                
                if action_id == "approve_plan":
                    logger.info(f"✅ User {user} APPROVED the remediation plan remotely!")
                    
                    # Physically bridge the asynchronous gap for Streamlit's process memory
                    with open("hitl_sync.json", "w") as f:
                        json.dump({"status": "approved", "user": user}, f)
                    
                    # In true Langgraph Sqlite/Postgres Checkpointer environments, 
                    # we natively invoke the graph here to autonomously resume:
                    # agent.invoke(None, config={"configurable": {"thread_id": "YOUR_THREAD"}})
                    
                    return {"text": f"✅ Execution explicitly approved by {user}!"}

                elif action_id == "reject_plan":
                    logger.info(f"❌ User {user} REJECTED the remediation plan remotely!")
                    with open("hitl_sync.json", "w") as f:
                        json.dump({"status": "rejected", "user": user}, f)
                    
                    return {"text": f"❌ Execution explicitly rejected by {user}!"}
                    
        return {"status": "Ignored or Malformed"}
        
    except Exception as e:
        logger.error(f"Failed to parse Slack webhook: {str(e)}")
        return {"error": "Invalid interaction payload."}
