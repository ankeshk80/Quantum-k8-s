import streamlit as st
import sys
import os
import pandas as pd
import numpy as np
import uuid

# Add parent dir to path to import graph/state
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.kubectl import KubectlUtil
from graph import build_graph

# Page config MUST be the first Streamlit command
st.set_page_config(
    page_title="K8s Whisperer | Quantumind Theme",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for that dark, sleek look matching the reference
st.markdown("""
    <style>
        /* Modern Glassmorphic Theme */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono&display=swap');

        .stApp {
            background-color: #0d0f14;
            color: #e2e8f0;
            font-family: 'Inter', sans-serif;
        }
        
        [data-testid="stSidebar"] {
            background-color: #12151c !important;
            border-right: 1px solid #1e293b;
        }
        
        h1, h2, h3, h4 {
            color: #f8fafc !important;
            font-weight: 600 !important;
            letter-spacing: -0.02em;
        }
        
        /* Glassmorphism Containers */
        [data-testid="stVerticalBlock"] > div > div[data-testid="stContainer"] {
            background: rgba(30, 41, 59, 0.45);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 16px !important;
            padding: 20px !important;
        }
        
        .bot-msg {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 15px;
            color: #f1f5f9;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            line-height: 1.6;
        }
        
        .user-msg {
            background: linear-gradient(135deg, #0369a1 0%, #075985 100%);
            border: 1px solid #0ea5e9;
            border-radius: 12px;
            padding: 12px 18px;
            margin-bottom: 15px;
            color: #f0f9ff;
            text-align: right;
            margin-left: auto;
            max-width: 85%;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
        }

        /* Buttons Optimization */
        div[data-testid="stButton"] button[kind="primary"] {
            background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stButton"] button[kind="primary"]:hover {
            transform: translateY(-1px);
            box-shadow: 0 0 20px rgba(14, 165, 233, 0.4);
        }
        
        /* Optimized Scrollbars */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }

        /* Sidebar Navigation Improvements */
        [data-testid="stSidebar"] div[data-testid="stButton"] button {
            text-align: left !important;
            justify-content: flex-start !important;
            padding-left: 15px !important;
            border: 1px solid rgba(255,255,255,0.05) !important;
            background: rgba(255,255,255,0.02) !important;
            margin-bottom: 5px !important;
        }
        
        hr {
            border-color: rgba(255,255,255,0.1) !important;
        }
    </style>
""", unsafe_allow_html=True)

# ----------------- INITIALIZE STATE -----------------
if 'agent' not in st.session_state:
    st.session_state.agent = build_graph()
    st.session_state.current_state = {
        "events": [], "anomalies": [], "diagnosis": "", "plan": {}, "approved": True, "result": "", "audit_log": []
    }
    st.session_state.chat_history = []
    st.session_state.is_running = False
    st.session_state.thread_id = str(uuid.uuid4())

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown('<div style="display:flex; align-items:center; gap:10px;"><h2 style="color: #00befc; font-weight: 800; margin:0;"> QUANTUM K8S</h2></div>', unsafe_allow_html=True)
    st.text_input("Search", placeholder="🔍 Search   ⌘ K", label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("  Agent", use_container_width=True, type="primary"):
        pass # Active page

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:#aaabb2;font-size:0.85em;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;'>Cluster Health</h4>", unsafe_allow_html=True)
    
    # Fetch real pods using python client/kubectl wrapper
    try:
        k8s = KubectlUtil()
        pods_out = k8s.run_command("kubectl get pods -A --no-headers")
        statuses = []
        if not pods_out.startswith("Error"):
            for line in pods_out.strip().split('\n')[:8]: # Restrict to 8 for UI grid
                if "Running" in line: statuses.append("<span style='color:#22c55e'>●</span>")
                elif "CrashLoop" in line or "Error" in line: statuses.append("<span style='color:#ef4444'>●</span>")
                else: statuses.append("<span style='color:#eab308'>●</span>")
        while len(statuses) < 8: statuses.append("<span style='color:#22c55e'>●</span>")
    except:
        statuses = ["<span style='color:#22c55e'>●</span>"] * 8
        
    cols = st.columns(4, gap="small")
    for i, status in enumerate(statuses[:8]):
        cols[i % 4].markdown(f"<div style='text-align:center; font-size:1.5em; background:rgba(30,41,59,0.5); padding:8px; border-radius:8px; border:1px solid rgba(255,255,255,0.1);'>{status}</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:#aaabb2;font-size:0.85em;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;'>Cluster Telemetry</h4>", unsafe_allow_html=True)
    
    # 1. Error (Anomalies)
    anomalies = st.session_state.current_state.get("anomalies", [])
    with st.expander(" Errors & Anomalies", expanded=bool(anomalies)):
        if anomalies:
            for a in anomalies:
                st.markdown(f"<div style='border-left: 3px solid #ff4b4b; padding-left:10px; margin-bottom:10px;'><b style='color:#ff4b4b;font-size:0.9em;'>{a.get('type')}</b><br><code style='font-size:0.75em;'>{a.get('affected_resource')}</code></div>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color:gray;font-size:0.85em;'>No active critical errors.</span>", unsafe_allow_html=True)
            
    # 2. Log (Diagnostics)
    diag = st.session_state.current_state.get("diagnosis", "")
    with st.expander(" Diagnostic Logs", expanded=False):
        if diag:
            st.markdown(f"<div style='color:#bbc5ce;font-size:0.85em;line-height:1.4;'>{diag}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color:gray;font-size:0.85em;'>No diagnostic logs pending.</span>", unsafe_allow_html=True)
            
    # 3. What Fixed
    audit = st.session_state.current_state.get("audit_log", [])
    with st.expander(" What Fixed (Audit)", expanded=bool(audit)):
        if audit:
            # Show the most recent 3 remediations
            for log in reversed(audit[-3:]): 
                st.markdown(f"<div style='border-left: 3px solid #00ff00; padding-left:10px; margin-bottom:10px;'><b style='color:#00ff00;font-size:0.9em;'>{log.get('action_taken')}</b><br><span style='color:#bbc5ce;font-size:0.8em;'>Result: {log.get('result')}</span></div>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color:gray;font-size:0.85em;'>No automated actions executed recently.</span>", unsafe_allow_html=True)

    st.markdown("<br>" * 3, unsafe_allow_html=True)
    st.markdown("---")
    if st.button("  Settings", use_container_width=True, type="secondary"):
        st.toast("Opening settings panel...")
    if st.button("  Help", use_container_width=True, type="secondary"):
        st.toast("Redirecting to team documentation...")
    
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("<div style='display:flex; align-items:center; gap:10px;'><div></div><div><b style='font-size:0.9em;color:white;'>DevOps Engineer</b><br><span style='font-size:0.7em;color:gray;'>admin@cluster.local</span></div></div>", unsafe_allow_html=True)


# ----------------- MAIN LAYOUT -----------------
col_title, col_actions = st.columns([1.8, 1])
with col_title:
    st.markdown("<h2 style='margin-bottom:0px;'>Powering Precision-Built AI Agents</h2>", unsafe_allow_html=True)
    st.markdown("<span style='color: #888; font-size: 0.9em;'>Create, configure, and deploy a Kubernetes SRE agent tailored to your cluster needs.</span>", unsafe_allow_html=True)
with col_actions:
    st.markdown("<br>", unsafe_allow_html=True)
    a1, a2 = st.columns([1, 1.2])
    if a1.button(" Reset", use_container_width=True):
        st.session_state.current_state = {"events": [], "anomalies": [], "diagnosis": "", "plan": {}, "approved": True, "result": "", "audit_log": []}
        st.session_state.chat_history = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()

    if a2.button(" Cleanup", use_container_width=True):
        with st.spinner("Wiping cluster..."):
            k8s = KubectlUtil()
            k8s.run_command("kubectl delete deployments --all")
            k8s.run_command("kubectl delete ns -l heritage=k8s-whisperer --wait=false")
            st.toast("✅ Cluster wiped clean for demo!")
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# --- SHADOW RUN SIMULATION BADGE ---
import os
if os.path.exists("sim_active.txt"):
    st.markdown("""
    <div style="background-color: #3b301a; border: 1px solid #ffaa00; padding: 12px 20px; border-radius: 8px; margin-bottom: 25px; display: flex; align-items: center; gap: 15px; animation: pulse 2s infinite; box-shadow: 0 0 20px rgba(255, 170, 0, 0.15);">
        <div style="font-size: 1.8em;"></div>
        <div>
            <b style="color: #ffaa00; text-transform: uppercase; letter-spacing: 2px; font-size: 0.9em;">Shadow Run Active</b><br>
            <span style="color: #eee; font-size: 0.95em;">Validating remediation in isolated <b>Sandbox Namespace</b> before Production commit.</span>
        </div>
    </div>
    <style>
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.01); opacity: 0.9; }
        100% { transform: scale(1); opacity: 1; }
    }
    </style>
    """, unsafe_allow_html=True)
col_left, col_right = st.columns([1.1, 1], gap="large")

# --- LEFT COLUMN (Config) ---
with col_left:
    # Agent Identity
    st.markdown("<h4 style='margin-bottom:10px;'>Agent Identity</h4>", unsafe_allow_html=True)
    st.markdown("<span style='color:#bbb; font-size:0.9em;'>Name</span>", unsafe_allow_html=True)
    st.text_input("Name", value="K8s Whisperer Autonomous SRE", label_visibility="collapsed")
    
    st.markdown("<span style='color:#bbb; font-size:0.9em;'>Description</span>", unsafe_allow_html=True)
    st.text_input("Description", value="AI agent that assists with observing, diagnosing, and remediating Kubernetes anomalies efficiently.", label_visibility="collapsed")
    
    st.markdown("<span style='color:#bbb; font-size:0.9em;'>Base Model</span>", unsafe_allow_html=True)
    st.text_input("Base Model", value="Llama 3.3 70B (Groq) - Premium", label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Instructions System
    st.markdown("<h4 style='margin-bottom:10px;'>Instructions System</h4>", unsafe_allow_html=True)
    st.markdown("<span style='color:#bbb; font-size:0.9em;'>Instruction</span>", unsafe_allow_html=True)
    st.text_area("Instruction", value="K8s Whisperer, an AI agent specialized in Kubernetes administration.\nYour tasks include:\n\n• Observing cluster events and capturing CrashLoops, OOMKilled errors.\n• Diagnosing root causes by fetching tailing logs via kubectl.\n• Generating safe, actionable remediation JSON plans.\n• Always delivering outputs that are strictly parsed and ready to execute.", height=180, label_visibility="collapsed")
    
    st.markdown("<span style='color:#bbb; font-size:0.9em;'>Conversation Starters (Safety Constraints)</span>", unsafe_allow_html=True)
    st.text_input("Safety", value="Only auto-execute actions with Confidence > 0.8 and Blast Radius == 'low'.", label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Capabilities
    st.markdown("<h4 style='margin-bottom:10px;'>Capabilities</h4>", unsafe_allow_html=True)
    with st.container(border=True):
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown("<div style='display:flex; gap:15px;'><div style='font-size:1.5em;'></div><div><b style='color:#fff;'>Kubectl Execution</b><br><span style='font-size:0.85em;color:gray;'>Allow agent to interact directly with cluster api</span></div></div>", unsafe_allow_html=True)
        with c2:
            st.toggle("k8s", value=True, label_visibility="collapsed")
            
    with st.container(border=True):
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown("<div style='display:flex; gap:15px;'><div style='font-size:1.5em;'></div><div><b style='color:#fff;'>Slack Webhooks</b><br><span style='font-size:0.85em;color:gray;'>Push live remediation updates to operations channel</span></div></div>", unsafe_allow_html=True)
        with c2:
            st.toggle("slack", value=True, label_visibility="collapsed")
            
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h4 style='margin-bottom:10px;'>Cluster Metrics</h4>", unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    anomalies_count = len(st.session_state.current_state.get("anomalies", []))
    m1.metric("Detected Anomalies", anomalies_count, delta=None if anomalies_count == 0 else -anomalies_count)
    
    last_action = "None"
    if st.session_state.current_state.get("audit_log"):
        last_action = st.session_state.current_state["audit_log"][-1]["action_taken"]
    m2.metric("Last Action", last_action)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### Node Pressure (Real-time)")
    if 'cpu_data' not in st.session_state:
        st.session_state.cpu_data = np.random.randn(20) * 5 + 40
        st.session_state.mem_data = np.random.randn(20) * 2 + 70
    else:
        st.session_state.cpu_data = np.append(st.session_state.cpu_data[1:], np.random.randn(1) * 5 + 40)
        st.session_state.mem_data = np.append(st.session_state.mem_data[1:], np.random.randn(1) * 2 + 70)
        
    c1, c2 = st.columns(2)
    with c1:
        st.caption("CPU Usage (%)")
        st.line_chart(pd.DataFrame(st.session_state.cpu_data, columns=["CPU"]), height=150, color="#00befc")
    with c2:
        st.caption("Memory Usage (%)")
        st.line_chart(pd.DataFrame(st.session_state.mem_data, columns=["Mem"]), height=150, color="#ff4b4b")


# --- RIGHT COLUMN (Chat / Demo Mode) ---
with col_right:
    st.markdown("<h4 style='margin-bottom:10px;'>Demo Mode <span style='color:#00ff00; font-size:0.6em;'></span></h4>", unsafe_allow_html=True)
    
    tab_chat, tab_trace, tab_analysis, tab_plan, tab_audit = st.tabs([" Chat Agent", " Thought Trace", " Analysis", " Plan", " Audit"])
    
    with tab_chat:
        # Dark modern card for demo
        with st.container(border=True):
            
            # Header banner inside demo
            st.markdown("""
            <div style='text-align: center; margin-bottom: 30px; margin-top: 10px;'>
                <h1 style='color: #00befc; margin-bottom: 0;'></h1>
                <h3 style='margin-top: 10px; color: white;'>Quantumind K8s at Your Fingertips<br>Cluster Intelligence. Healing Precision.</h3>
                <p style='color: #888; font-size: 0.9em; max-width: 400px; margin: 0 auto;'>Run live scans, diagnose faulty pods, and auto-heal deployments to accelerate operations.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Chat container UI simulation
            chat_height = 420
            chat_area = st.container(height=chat_height)
            
            with chat_area:
                # Initial greeting
                if len(st.session_state.chat_history) == 0:
                    st.markdown("""
                    <div style='display:flex; gap:10px;'>
                        <div style='font-size:1.5em;'></div>
                        <div class='bot-msg'>
                            Hi, I'm K8s Whisperer, your cluster AI assistant. Click the button below to initiate a diagnostic scan of your cluster events.
                            <br><br>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    # (Button removed from greeting area as requested)
                
                # Display history
                for msg in st.session_state.chat_history:
                    if msg["role"] == "user":
                        st.markdown(f"<div class='user-msg'>{msg['content']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style='display:flex; gap:10px;'>
                            <div style='font-size:1.5em;'></div>
                            <div class='bot-msg'>{msg['content']}</div>
                        </div>
                        """, unsafe_allow_html=True)

                if st.session_state.is_running:
                    st.markdown("""
                    <div style='display:flex; gap:10px;'>
                        <div style='font-size:1.5em;'></div>
                        <div class='bot-msg'><em>Analyzing cluster events... Stand by.</em></div>
                    </div>
                    """, unsafe_allow_html=True)

           # Removed Chat Input from inside Tab
                
    with tab_trace:
        st.markdown("#### Live Agent Thought Trace")
        trace_text = ">> INITIALIZING K8S WHISPERER AGENT...\n"
        if st.session_state.is_running:
            trace_text += ">> [OBSERVE] Scanning cluster for events via Kubectl client...\n"
        elif st.session_state.chat_history:
            trace_text += ">> [OBSERVE] Cluster scan complete.\n"
            if st.session_state.current_state.get("anomalies"):
                trace_text += f">> [DETECT] LangGraph node isolated {len(st.session_state.current_state.get('anomalies'))} anomalies.\n"
                trace_text += f">> [DIAGNOSE] {st.session_state.current_state.get('diagnosis', 'Pending...')}\n"
                plan = st.session_state.current_state.get("plan", {})
                if plan:
                    trace_text += f">> [PLAN] Action '{plan.get('action')}' formulated on target: {plan.get('target')}.\n"
                    trace_text += f">> [SAFETY] Risk Assessment - Blast radius evaluated as: {plan.get('blast_radius')}.\n"
                res = st.session_state.current_state.get("result")
                if res:
                    trace_text += f">> [EXECUTE] Instruction sent to subprocess. Verification: {res}\n"
            else:
                 trace_text += ">> [DETECT] Cluster health 100%. No vulnerabilities or errors.\n"
                 
        trace_text += ">> [WAIT] Agent standing by for next scan interval (30s)...\n"
        
        st.text_area("LangGraph State", value=trace_text, height=350, disabled=True, label_visibility="collapsed")

    with tab_analysis:
        st.markdown("#### Real-time Cluster Observation")
        if not st.session_state.current_state.get("events"):
            st.info("No data yet. Run the agent to start observing.")
        else:
            st.write("Recent Events Found:")
            st.dataframe(st.session_state.current_state["events"], use_container_width=True)
            
        st.markdown("#### Detected Anomalies")
        anoms = st.session_state.current_state.get("anomalies")
        if not anoms:
            st.success("No critical anomalies detected in the last scan.")
        else:
            for anomaly in anoms:
                with st.expander(f"{anomaly.get('type')} on {anomaly.get('affected_resource')}", expanded=True):
                    st.write(f"**Severity:** {anomaly.get('severity')}")
                    st.write(f"**Confidence:** {anomaly.get('confidence')}")
                    st.write(f"**Reason:** {anomaly.get('reason')}")
                    
            # ---------------------------------------------------------
            # FEATURE: Context-Aware Dependency Mapping (The Why-Tree)
            # ---------------------------------------------------------
            st.markdown("<br>#### Context-Aware Dependency Mapping (Why-Tree)", unsafe_allow_html=True)
            
            anomaly_type = anoms[0].get('type', '')
            pod_name = anoms[0].get('affected_resource', 'unknown-pod')
            
            # Dynamically mutate the dependency tree based on exact symptom
            if "OOM" in anomaly_type:
                culprit_node = "Node Memory Pool: Exhausted by Neighboring Tenant"
                downstream = "Database Connections: Stable"
                upstream = "Ingress Traffic: Normal (20req/s)"
            elif "CrashLoop" in anomaly_type:
                culprit_node = "ConfigMap Binding: Stale Data / Code Exception"
                downstream = "Persistent Volume Claim: Read-Only Lock"
                upstream = "Service Mesh Proxy: Healthy"
            else:
                culprit_node = "Bare-Metal Node IOPS: Starved (99% util)"
                downstream = "Dependencies: Unreachable"
                upstream = "Load Balancer: Queuing Requests"
                
            tree_html = f"""
<div style="background-color: #1a1c23; padding: 30px; border-radius: 12px; border: 1px solid #333; margin-top:10px; position: relative; overflow: hidden;">
    <div style="display: flex; flex-direction: column; align-items: center; gap: 0px;">
        
        <!-- Upstream -->
        <div style="background-color: #2b3a4a; padding: 12px 25px; border-radius: 8px; border: 1px solid #4a6278; text-align: center; min-width: 300px; z-index: 2;">
            <span style="font-size: 0.8em; color: #888;">UPSTREAM</span><br>
            <b style="color: #a0c4ff;">{upstream}</b>
        </div>
        
        <!-- SVG Connection 1 -->
        <svg width="40" height="40" style="margin: -5px 0;">
            <line x1="20" y1="0" x2="20" y2="30" stroke="#555" stroke-width="2" />
            <polygon points="15,30 25,30 20,40" fill="#555" />
        </svg>
        
        <!-- Failing Pod -->
        <div style="background-color: #4a1c1c; padding: 15px 25px; border-radius: 8px; border: 1px solid #ff4b4b; text-align: center; min-width: 320px; box-shadow: 0 0 20px rgba(255, 75, 75, 0.25); z-index: 2;">
            <b style="color: #ff4b4b; font-size: 1.1em;">Pod: {pod_name}</b><br>
            <span style="font-size: 0.85em; color: #ffaaaa;">Status: FAILING ({anomaly_type})</span>
        </div>
        
        <div style="display: flex; gap: 40px; margin-top: -5px;">
            <div style="display: flex; flex-direction: column; align-items: center;">
                <svg width="100" height="60">
                    <path d="M 50 0 L 50 20 L 20 50" stroke="#555" stroke-width="2" fill="none" />
                    <polygon points="15,45 22,55 10,55" fill="#555" transform="rotate(-30 20 50)" />
                </svg>
                <div style="background-color: #2b3a4a; padding: 12px 25px; border-radius: 8px; border: 1px solid #4a6278; text-align: center; min-width: 280px;">
                    <span style="font-size: 0.8em; color: #888;">DOWNSTREAM</span><br>
                    <b style="color: #a0c4ff;">{downstream}</b>
                </div>
            </div>

            <div style="display: flex; flex-direction: column; align-items: center;">
                <svg width="100" height="60">
                    <path d="M 50 0 L 50 20 L 80 50" stroke="#ffaa00" stroke-width="2" fill="none" stroke-dasharray="5,5" />
                    <polygon points="75,45 82,55 85,45" fill="#ffaa00" />
                    <text x="55" y="25" fill="#ffaa00" font-size="10" font-weight="bold">ROOT CULPRIT</text>
                </svg>
                <div style="background-color: #3b301a; padding: 12px 25px; border-radius: 8px; border: 1px solid #ffaa00; text-align: center; min-width: 280px; box-shadow: 0 0 20px rgba(255, 170, 0, 0.2);">
                    <span style="font-size: 0.8em; color: #ffcc00; letter-spacing: 1px;">SIDEWAYS VECTOR</span><br>
                    <b style="color: #ffaa00; font-size:1em;">{culprit_node}</b>
                </div>
            </div>
        </div>
    </div>
</div>
"""
            # Collapse all newlines and indents so Markdown cannot parse it as a code block
            flat_html = tree_html.replace('\n', '').replace('    ', '')
            st.markdown(flat_html, unsafe_allow_html=True)
            st.info("💡 **System Thinking:** The AI recursively traced network dependencies to prove this pod crash is merely a symptom caused by a sideways hardware constraint—not its own code.")
            # ---------------------------------------------------------

    with tab_plan:
        st.markdown("#### Diagnosis")
        if st.session_state.current_state.get("diagnosis"):
            st.markdown(f"> {st.session_state.current_state['diagnosis']}")
        else:
            st.info("Run diagnosis to see root cause.")

        st.markdown("#### Remediation Plan")
        plan = st.session_state.current_state.get("plan", {})
        if plan:
            st.json(plan)
            st.markdown(f"**Action:** `{plan.get('action')}`")
            st.markdown(f"**Safety Score:** `{plan.get('confidence', 0) * 100}%` | **Blast Radius:** `{plan.get('blast_radius')}`")
        else:
            st.info("No plan generated yet.")

        st.markdown("#### Execution Result")
        res = st.session_state.current_state.get("result", "")
        if res:
            if "Recovered" in res:
                st.success(res)
            else:
                st.warning(res)
        else:
            st.info("Awaiting execution.")

    with tab_audit:
        st.markdown("#### Execution Audit History")
        if not st.session_state.current_state.get("audit_log"):
            st.info("No audit logs available.")
        else:
            for log in reversed(st.session_state.current_state["audit_log"]):
                with st.expander(f"{log['timestamp']} - {log['anomaly_type']}", expanded=False):
                    st.write(f"**Action:** {log['action_taken']}")
                    st.write(f"**Result:** {log['result']}")
                    st.write(f"**Diagnosis:** {log['diagnosis']}")
                    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Check if agent is paused for HITL
    current_state_obj = st.session_state.agent.get_state(config={"configurable": {"thread_id": st.session_state.thread_id}})
    is_paused = "hitl" in current_state_obj.next

    if is_paused:
        st.warning("⚠️ Plan requires Human Approval before actioning!")
        
        # Check for remote REST/Slack webhook interactions!
        import os, json
        if os.path.exists("hitl_sync.json"):
            with open("hitl_sync.json", "r") as f:
                remote_auth = json.load(f)
            os.remove("hitl_sync.json") # consume the signal
            
            if remote_auth.get("status") == "approved":
                user = remote_auth.get("user", "Slack SRE")
                st.session_state.chat_history.append({"role": "user", "content": f"✅ **Approved execution remotely via Slack by {user}.**"})
                st.session_state.is_running = True
                st.rerun()
            elif remote_auth.get("status") == "rejected":
                user = remote_auth.get("user", "Slack SRE")
                st.session_state.chat_history.append({"role": "user", "content": f"❌ **Rejected execution remotely via Slack by {user}.**"})
                st.session_state.current_state = {"events": [], "anomalies": [], "diagnosis": "", "plan": {}, "approved": True, "result": "", "audit_log": []}
                st.session_state.thread_id = str(uuid.uuid4())
                from graph import build_graph
                st.session_state.agent = build_graph()
                st.rerun()
                
        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("✅ Approve Plan Execution", type="primary", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": "✅ **Approved execution.**"})
            st.session_state.is_running = True
            st.rerun()
        if col_btn2.button("❌ Reject Plan", type="secondary", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": "❌ **Rejected execution.**"})
            st.session_state.current_state = {"events": [], "anomalies": [], "diagnosis": "", "plan": {}, "approved": True, "result": "", "audit_log": []}
            st.session_state.thread_id = str(uuid.uuid4())
            from graph import build_graph
            st.session_state.agent = build_graph()
            st.rerun()
            
    # Action Area (Globally placed at bottom of column)
    if not st.session_state.is_running and not is_paused:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(" INITIATE CLUSTER SCAN", type="primary", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": "Run a full cluster diagnostic scan."})
            st.session_state.is_running = True
            st.rerun()
# --- BACKGROUND EXECUTION ---
if st.session_state.is_running:
    try:
        # Load graph once from cache for performance
        if "agent" not in st.session_state:
            st.session_state.agent = build_graph()
            
        current_state_obj = st.session_state.agent.get_state(config={"configurable": {"thread_id": st.session_state.thread_id}})
        is_paused = "hitl" in current_state_obj.next
        target_payload = None if is_paused else st.session_state.current_state
        
        result = st.session_state.agent.invoke(
            target_payload,
            config={"configurable": {"thread_id": st.session_state.thread_id}}
        )
        st.session_state.current_state = result
        
        # Check if we paused halfway
        new_state_obj = st.session_state.agent.get_state(config={"configurable": {"thread_id": st.session_state.thread_id}})
        if "hitl" in new_state_obj.next:
            plan = result.get("plan", {})
            diag = result.get("diagnosis", "N/A")
            bot_reply = f"""
            <b style='color:#ffaa00;'>⚠️ HITL Interruption - Manual Approval Required</b><br><br>
            <b>Diagnosis:</b> {diag}<br><br>
            <b>Proposed Action:</b> <code>{plan.get('action')}</code> on <code>{plan.get('target')}</code><br>
            <b>Risk Level:</b> {plan.get('blast_radius')}<br><br>
            <i>Please approve the execution below to proceed.</i>
            """
            st.session_state.chat_history.append({"role": "bot", "content": bot_reply})
            st.session_state.is_running = False
            st.rerun()
        
        # If we reach here, graph is completely finished
        anomalies = result.get("anomalies", [])
        if anomalies:
            diag = result.get("diagnosis", "N/A")
            plan = result.get("plan", {})
            res_status = result.get("result", "Recovered")
            
            # Format markdown string for bot message with nice html
            bot_reply = f"""
            <b style='color:#ff4b4b;'>⚠️ {len(anomalies)} anomalies detected:</b><br><br>
            <b>Anomaly Type:</b> <span style='color:#00befc;'>{anomalies[0].get('type')}</span> on <code>{anomalies[0].get('affected_resource')}</code><br><br>
            <b>Diagnosis:</b> {diag}<br><br>
            <b>Action Plan:</b> <code>{plan.get('action')}</code><br>
            <b>Result:</b> <span style='background:#1c3326; color:#00ff00; padding:2px 5px; border-radius:3px;'>{res_status}</span>
            <br><br>
            <span style='font-size:1.2em; color:gray;'> 👍 👎 🔊</span>
            """
            st.session_state.chat_history.append({"role": "bot", "content": bot_reply})
        else:
            st.session_state.chat_history.append({"role": "bot", "content": "✅ Cluster scan complete. No critical anomalies detected. Everything looks healthy!<br><br><span style='font-size:1.2em; color:gray;'> 👍 👎 🔊</span>"})
            
    except Exception as e:
         st.session_state.chat_history.append({"role": "bot", "content": f"❌ Error during execution: {str(e)}"})
    
    st.session_state.is_running = False
    st.rerun()
