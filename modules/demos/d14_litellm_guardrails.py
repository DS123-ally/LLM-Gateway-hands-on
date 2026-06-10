import streamlit as st
import os
import requests
import json
from modules.utils import get_primary_model, require_keys

def render():
    st.title("LiteLLM Guardrails (Proxy)")
    st.write(
        "LiteLLM features a built-in proxy server that can natively enforce Enterprise Guardrails "
        "(like Llama Guard, Presidio PII Masking, Lakera, and Aporia) completely transparently "
        "before the request ever hits your main LLM!"
    )

    st.divider()
    require_keys()

    st.subheader("1. Start the LiteLLM Proxy Server")
    st.info(
        "To run this demo, you must start the LiteLLM Proxy Server in a separate terminal window. "
        "Because Windows PowerShell defaults to an older encoding, you must set UTF-8 before running the proxy."
    )
    st.code('$env:PYTHONIOENCODING="utf-8"\nuv run litellm --config litellm_guardrails_config.yaml --port 4000', language="powershell")

    st.subheader("2. Test the Proxy Guardrails")
    st.write("Send a request through the local LiteLLM Proxy. If a guardrail intercepts it, the proxy will return a `400 Bad Request`.")

    prompt = st.text_area("Test Prompt:", value="Tell me a joke.")

    if st.button("Send to LiteLLM Proxy", type="primary"):
        with st.spinner("Calling Proxy..."):
            try:
                # Call the local LiteLLM Proxy
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer sk-1234" # Dummy key
                }
                payload = {
                    "model": "groq-model",
                    "messages": [{"role": "user", "content": prompt}]
                }
                
                # Check if proxy is running
                try:
                    res = requests.post("http://localhost:4000/v1/chat/completions", headers=headers, json=payload, timeout=5)
                except requests.exceptions.ConnectionError:
                    st.error("🚨 **Connection Error!** The LiteLLM Proxy is not running on port 4000. Please run the command above in a separate terminal!")
                    st.stop()

                if res.status_code != 200:
                    st.error(f"🚨 **Request Blocked by LiteLLM Guardrail!**")
                    st.error(f"HTTP {res.status_code}: {res.text}")
                else:
                    data = res.json()
                    st.success("✅ **Request Passed!**")
                    st.write("**Response:**")
                    st.info(data['choices'][0]['message']['content'])
                    st.caption("This request bypassed the Custom Guardrail and was successfully routed to Groq!")
            except Exception as e:
                st.error(f"Error: {e}")

