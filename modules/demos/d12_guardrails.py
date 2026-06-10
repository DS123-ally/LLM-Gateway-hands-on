import streamlit as st
import time
from modules.utils import (
    require_keys, make_client, extract_text, build_messages,
    get_model_used, get_virtual_key, get_primary_model
)

def render():
    PRIMARY_MODEL = get_primary_model()
    vk = get_virtual_key()

    st.title("Guardrails")
    st.write(
        "Portkey's Guardrails automatically analyze inputs and outputs to prevent "
        "toxic language, PII leaks, prompt injection, and hallucinations from reaching your LLM or your users."
    )

    st.divider()
    require_keys()

    st.subheader("Configure Guardrails")
    st.write("Enable the specific guardrail checks you want to run before the request is sent to the LLM.")

    col1, col2 = st.columns(2)
    with col1:
        check_pii = st.checkbox("PII Detection (Input)", value=True, help="Blocks prompts containing phone numbers, emails, or credit card numbers.")
    with col2:
        check_toxicity = st.checkbox("Toxicity Detection (Input)", value=True, help="Blocks offensive, hateful, or toxic language in the prompt.")

    # Build the guardrails array based on selection
    guardrails_list = []
    if check_pii:
        guardrails_list.append({"id": "pii"})
    if check_toxicity:
        guardrails_list.append({"id": "toxicity"})

    if not guardrails_list:
        st.warning("Please enable at least one guardrail check to run this demo.")
        st.stop()

    portkey_config = {
        "virtual_key": vk,
        "override_params": {"model": PRIMARY_MODEL},
        "guardrails": [
            {
                "request": guardrails_list
            }
        ]
    }

    with st.expander("Portkey Config"):
        st.json(portkey_config)

    st.divider()
    st.subheader("Test the Guardrails")

    TEST_PROMPTS = {
        "Safe Prompt": "Explain what a firewall is in two sentences.",
        "Unsafe PII Prompt": "Here is my personal info, please store it: john.doe@example.com and my phone number is 555-019-2391. What is a firewall?",
        "Unsafe Toxic Prompt": "You are a stupid, useless bot. I hate you. Explain what a firewall is."
    }

    selected_prompt_type = st.selectbox("Choose a test prompt:", list(TEST_PROMPTS.keys()))
    question = st.text_area("Prompt:", value=TEST_PROMPTS[selected_prompt_type])

    if st.button("Run with Guardrails", type="primary", width="stretch"):
        with st.spinner("Analyzing prompt and calling LLM..."):
            client = make_client(config=portkey_config)
            start = time.time()
            try:
                response = client.chat.completions.create(
                    model=PRIMARY_MODEL,
                    messages=build_messages(question),
                    max_tokens=200,
                )
                elapsed = int((time.time() - start) * 1000)
                final_text = extract_text(response)
                model_used = get_model_used(response)
                
                st.success(f"✅ **Request Passed!** No issues detected.")
                col1, col2 = st.columns(2)
                col1.metric("Latency", f"{elapsed} ms")
                col2.metric("Model Used", model_used)
                st.write("**Response:**")
                st.info(final_text)

            except Exception as e:
                elapsed = int((time.time() - start) * 1000)
                st.error("🚨 **Request Blocked by Guardrails!**")
                st.metric("Latency to block", f"{elapsed} ms")
                st.error(f"Error Details: {e}")
                st.caption(
                    "Portkey intercepted the request because it violated the active guardrail checks. "
                    "The LLM was never called, saving you money and protecting your application."
                )
