import streamlit as st
import os
import time
import uuid
import json
from portkey_ai import Portkey, PORTKEY_GATEWAY_URL

# Page config
st.set_page_config(page_title="LLM Gateway Demo", page_icon="🌐", layout="wide")

st.title("🌐 LLM Gateway with Portkey")
st.markdown("### Zero to Production: A Complete Hands-On Guide for Enterprise AI Systems")
st.markdown("> **What you'll build:** A progressively enhanced LLM setup — starting from a raw direct API call, then routing every request through a production-grade gateway with observability, retries, fallbacks, caching, and more.")

# --- Sidebar: Configuration ---
st.sidebar.header("⚙️ Configuration")

portkey_api_key = st.sidebar.text_input("Portkey API Key", type="password", help="Get this from Portkey Dashboard")
groq_api_key = st.sidebar.text_input("Groq API Key (For Baseline)", type="password", help="Required only for Baseline experiment")
vk_primary = st.sidebar.text_input("Primary Virtual Key Slug", value="vk1", help="Virtual key configured in Portkey for Groq")
primary_model = st.sidebar.selectbox("Primary Model", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"], index=0)

vk_fallback = st.sidebar.text_input("Fallback Virtual Key Slug", value="vk2", help="Virtual key configured in Portkey for a fallback model")
fallback_model = st.sidebar.selectbox("Fallback Model", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"], index=1)

st.sidebar.markdown("---")

# Navigation
experiment = st.sidebar.radio(
    "Select Experiment",
    (
        "Baseline (No Gateway)",
        "Exp 1: Basic Gateway Call",
        "Exp 2: Metadata & Observability",
        "Exp 3: Automatic Retries",
        "Exp 4: Request Timeouts",
        "Exp 5: Fallbacks",
        "Exp 6: Load Balancing",
        "Exp 7: Request Caching",
        "Exp 11: Streaming"
    )
)

GROQ_MODEL = f"@{vk_primary}/{primary_model}"
GROQ_MODEL_SMALL = f"@{vk_fallback}/{fallback_model}"

def init_portkey(config=None):
    if not portkey_api_key:
        st.warning("Please enter your Portkey API Key in the sidebar to run this experiment.")
        st.stop()
    if config:
        return Portkey(api_key=portkey_api_key, config=config)
    return Portkey(api_key=portkey_api_key)

# Helpers for UI
def show_results(q, answer, ms_taken, label):
    st.info(f"**Q:** {q}")
    st.success(f"**A:** {answer}")
    st.caption(f"⏱ {ms_taken:.0f}ms | {label}")

st.markdown("---")
st.header(experiment)

if experiment == "Baseline (No Gateway)":
    st.markdown("**Goal:** See what a raw LLM call looks like — no routing, no logging, no resilience.")
    if not groq_api_key:
        st.warning("Please enter your Groq API Key in the sidebar to run the Baseline.")
    else:
        q = st.text_input("Ask a question", "What is Kubernetes in one sentence?")
        if st.button("Run Baseline"):
            with st.spinner("Running..."):
                from langchain_groq import ChatGroq
                from langchain_core.messages import HumanMessage
                try:
                    raw_groq = ChatGroq(api_key=groq_api_key, model="llama-3.3-70b-versatile", temperature=0)
                    t0 = time.time()
                    r = raw_groq.invoke([HumanMessage(content=q)])
                    ms = (time.time() - t0) * 1000
                    show_results(q, r.content, ms, "direct Groq — no gateway")
                except Exception as e:
                    st.error(f"Error: {e}")

elif experiment == "Exp 1: Basic Gateway Call":
    st.markdown("**Goal:** Same call, same answer — but now every request is logged in your Portkey dashboard.")
    st.code(f'''portkey.chat.completions.create(
    model="@{vk_primary}/{primary_model}",
    messages=[{{"role":"user","content":q}}]
)''', language="python")
    
    q = st.text_input("Ask a question", "What is AI and gen ai?")
    if st.button("Run Exp 1"):
        with st.spinner("Routing via Portkey Gateway..."):
            portkey = init_portkey()
            try:
                t0 = time.time()
                r = portkey.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[{"role":"user","content":q}]
                )
                ms = (time.time() - t0) * 1000
                show_results(q, r.choices[0].message.content, ms, "routed via Portkey gateway")
                st.info("✅ Check portkey.ai → Logs to see the request fully logged!")
            except Exception as e:
                st.error(f"Error: {e}")

elif experiment == "Exp 2: Metadata & Observability":
    st.markdown("**Goal:** Tag every request with user, session, and feature info so you can filter and analyse in the dashboard.")
    st.code('''portkey.with_options(
    metadata={
        "_user": "alice",
        "session_id": session,
        "feature": "enterprise-rag",
        "environment": "streamlit"
    }
).chat.completions.create(...)''', language="python")

    user_name = st.text_input("User Name", "alice")
    feature_name = st.text_input("Feature Name", "enterprise-rag")
    q = st.text_input("Ask a question", "What is Kubernetes RBAC?")
    
    if st.button("Run Exp 2"):
        with st.spinner("Sending with metadata..."):
            portkey = init_portkey()
            session_id = str(uuid.uuid4())[:8]
            try:
                t0 = time.time()
                r = portkey.with_options(
                    metadata={
                        "_user": user_name,
                        "session_id": session_id,
                        "feature": feature_name,
                        "environment": "streamlit"
                    }
                ).chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[{"role": "user", "content": q}]
                )
                ms = (time.time() - t0) * 1000
                st.write(f"👤 **User:** {user_name} | 🔧 **Feature:** {feature_name}")
                show_results(q, r.choices[0].message.content, ms, "routed with metadata")
            except Exception as e:
                st.error(f"Error: {e}")

elif experiment == "Exp 3: Automatic Retries":
    st.markdown("**Goal:** Portkey automatically retries failed requests with exponential backoff. App code never sees transient 429/5xx errors.")
    retry_config = {
        "retry": {
            "attempts": 3,
            "on_status_codes": [429, 500, 502, 503, 504]
        }
    }
    st.json(retry_config)
    q = st.text_input("Ask a question", "What is an AI?")
    
    if st.button("Run Exp 3"):
        with st.spinner("Executing with Retry Config..."):
            portkey_retry = init_portkey(retry_config)
            try:
                t0 = time.time()
                r = portkey_retry.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[{"role": "user", "content": q}]
                )
                ms = (time.time() - t0) * 1000
                show_results(q, r.choices[0].message.content, ms, "succeeded with retries enabled")
            except Exception as e:
                st.error(f"All attempts failed: {e}")

elif experiment == "Exp 4: Request Timeouts":
    st.markdown("**Goal:** Kill requests that take too long. Returns HTTP 408 on timeout.")
    timeout_ms = st.number_input("Timeout (ms)", min_value=100, max_value=30000, value=10000)
    timeout_config = {"request_timeout": timeout_ms}
    st.json(timeout_config)
    
    q = st.text_input("Ask a question", "Explain Kubernetes networking in 2 sentences.")
    
    if st.button("Run Exp 4"):
        with st.spinner(f"Executing with {timeout_ms}ms timeout..."):
            portkey_timeout = init_portkey(timeout_config)
            try:
                t0 = time.time()
                r = portkey_timeout.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[{"role": "user", "content": q}]
                )
                ms = (time.time() - t0) * 1000
                show_results(q, r.choices[0].message.content, ms, f"Response within {timeout_ms}ms timeout")
            except Exception as e:
                st.error(f"⏱ Timed out or Error: {e}")

elif experiment == "Exp 5: Fallbacks":
    st.markdown("**Goal:** If the primary model fails, automatically switch to the fallback. Users never see the error.")
    
    st.markdown("### Part 1: Normal Execution (Primary works)")
    fallback_config = {
        "strategy": {"mode": "fallback"},
        "targets": [
            {"override_params": {"model": GROQ_MODEL}},        # primary
            {"override_params": {"model": GROQ_MODEL_SMALL}}   # fallback
        ]
    }
    st.json(fallback_config)
    q1 = st.text_input("Question (Normal)", "What is Intel Technology?")
    if st.button("Run Primary"):
        with st.spinner("Running..."):
            portkey_fallback = init_portkey(fallback_config)
            try:
                t0 = time.time()
                r = portkey_fallback.chat.completions.create(messages=[{"role": "user", "content": q1}])
                ms = (time.time() - t0) * 1000
                show_results(q1, r.choices[0].message.content, ms, "primary served")
            except Exception as e:
                st.error(str(e))
                
    st.markdown("---")
    st.markdown("### Part 2: Forced Fallback (Bad Primary Key)")
    st.markdown("Primary target uses a deliberately invalid key to trigger a 401 error, forcing the fallback.")
    forced_fallback_config = {
        "strategy": {"mode": "fallback"},
        "targets": [
            {
                "provider": "groq",
                "api_key": "gsk_FAKE_INVALID_KEY_THIS_WILL_FAIL",   # bad key
                "override_params": {"model": primary_model}
            },
            {"override_params": {"model": fallback_model}}         # fallback
        ]
    }
    st.json(forced_fallback_config)
    q2 = st.text_input("Question (Forced Fallback)", "What is Gen AI?")
    if st.button("Run Forced Fallback"):
        with st.spinner("Running and falling back..."):
            portkey_forced = init_portkey(forced_fallback_config)
            try:
                t0 = time.time()
                r = portkey_forced.chat.completions.create(messages=[{"role": "user", "content": q2}])
                ms = (time.time() - t0) * 1000
                show_results(q2, r.choices[0].message.content, ms, "fallback served (primary failed as expected)")
            except Exception as e:
                st.error(str(e))

elif experiment == "Exp 6: Load Balancing":
    st.markdown("**Goal:** Split traffic between providers by weight. Use for gradual migration, A/B testing, or cost control.")
    
    col1, col2 = st.columns(2)
    weight_primary = col1.slider("Weight: Primary Model", 0.0, 1.0, 0.7)
    weight_fallback = col2.slider("Weight: Fallback Model", 0.0, 1.0, 0.3)
    
    load_balance_config = {
        "strategy": {"mode": "loadbalance"},
        "targets": [
            {"override_params": {"model": GROQ_MODEL}, "weight": weight_primary},
            {"override_params": {"model": GROQ_MODEL_SMALL}, "weight": weight_fallback}
        ]
    }
    st.json(load_balance_config)
    
    num_requests = st.number_input("Number of requests to send", 1, 10, 5)
    
    if st.button("Run Load Balancing Test"):
        with st.spinner("Sending requests..."):
            portkey_lb = init_portkey(load_balance_config)
            for i in range(int(num_requests)):
                q = f"Question {i+1}: Explain Load Balancing briefly."
                try:
                    t0 = time.time()
                    r = portkey_lb.chat.completions.create(messages=[{"role": "user", "content": q}])
                    ms = (time.time() - t0) * 1000
                    st.write(f"**Req {i+1} [{ms:.0f}ms]:** {r.choices[0].message.content[:100]}...")
                except Exception as e:
                    st.error(f"Req {i+1}: ERROR - {e}")
            st.info("Check Portkey Logs to see which provider served each request.")

elif experiment == "Exp 7: Request Caching":
    st.markdown("**Goal:** Cache responses to identical questions. Second call is instant and costs nothing.")
    cache_config = {"cache": {"mode": "simple"}}
    st.json(cache_config)
    
    q = st.text_input("Ask a question to cache", "Define Kubernetes ConfigMap in one sentence.")
    
    col1, col2 = st.columns(2)
    
    if col1.button("1. Run First Call (Cache Miss)"):
        with st.spinner("Calling LLM..."):
            portkey_cached = init_portkey(cache_config)
            t0 = time.time()
            r1 = portkey_cached.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": q}],
                temperature=0,
                max_tokens=120,
            )
            t1 = (time.time() - t0) * 1000
            st.session_state['cache_q'] = q
            st.session_state['cache_ans'] = r1.choices[0].message.content
            st.session_state['cache_time'] = t1
            st.success(f"**Call 1 (Miss):** {t1:.0f}ms")
            st.write(r1.choices[0].message.content)
            
    if col2.button("2. Run Second Call (Cache Hit)"):
        with st.spinner("Checking Cache..."):
            portkey_cached = init_portkey(cache_config)
            t0 = time.time()
            r2 = portkey_cached.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": q}],
                temperature=0,
                max_tokens=120,
            )
            t2 = (time.time() - t0) * 1000
            st.success(f"**Call 2 (Hit):** {t2:.0f}ms")
            st.write(r2.choices[0].message.content)
            
            if 'cache_time' in st.session_state:
                speedup = st.session_state['cache_time'] / t2 if t2 > 0 else 999
                st.info(f"Speedup: **{speedup:.1f}x**")

elif experiment == "Exp 11: Streaming":
    st.markdown("**Goal:** Stream tokens back to the client as they are generated. Gateway features still apply.")
    q = st.text_input("Ask a question", "Explain what an LLM gateway does in exactly 3 bullet points.")
    
    if st.button("Start Streaming"):
        portkey = init_portkey()
        placeholder = st.empty()
        full_response = ""
        
        t0 = time.time()
        stream = portkey.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": q}],
            stream=True
        )
        
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full_response += delta
                placeholder.markdown(full_response + "▌")
                
        placeholder.markdown(full_response)
        ms = (time.time() - t0) * 1000
        st.caption(f"⏱ {ms:.0f}ms total stream time")
