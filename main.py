import logging
from graph import build_graph

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("k8s-whisperer.cli")

def main():
    logger.info("Starting K8s Whisperer CLI Agent...")
    
    # Initialize the agent
    agent = build_graph()

    # Initial state
    initial_state = {
        "events": [],
        "anomalies": [],
        "diagnosis": "",
        "plan": {},
        "approved": True,
        "result": "",
        "audit_log": []
    }

    try:
        # Invoke the agent
        logger.info("📊 Running agent workflow...")
        final_state = agent.invoke(
            initial_state,
            config={"configurable": {"thread_id": "cli-demo"}}
        )

        print("\n" + "="*50)
        print("AGENT SCAN COMPLETE")
        print("="*50)
        
        anomalies_found = len(final_state.get("anomalies", []))
        print(f"🔍 Anomalies Found: {anomalies_found}")
        
        if anomalies_found > 0:
            print(f"🧪 Diagnosis: {final_state.get('diagnosis')}")
            print(f"🛠️ Action Taken: {final_state.get('audit_log', [{}])[-1].get('action_taken', 'N/A')}")
            print(f"📊 Final Result: {final_state.get('result')}")
        else:
            print("✅ No critical issues found in this run.")
            
        print("="*50 + "\n")

    except Exception as e:
        logger.error(f"❌ Agent execution failed: {e}")

if __name__ == "__main__":
    main()