import streamlit as st
from modules.utils import (
    require_keys, make_client, timed_call, extract_text,
    build_messages, show_diagram, question_selector, get_model_used,
    get_primary_model, get_virtual_key
)
from modules.diagrams import ROUTING_DIAGRAM
from modules.questions import INTERESTING_QUESTIONS


def render():
    PRIMARY_MODEL = get_primary_model()
    st.title("Routing & Observability")
    st.write(
        "Every request now passes through Portkey before reaching Groq. "
        "Your code barely changes — but every call is automatically logged to your Portkey dashboard "
        "with token counts, latency, cost, and the full prompt and response."
    )

    with st.expander("Architecture", expanded=True):
        show_diagram(ROUTING_DIAGRAM, height=300)
        st.caption("Portkey acts as a transparent proxy. Same API shape — full visibility added.")

    st.divider()

    require_keys()

    st.subheader("The Code Change")
    st.code(
        f"""from portkey_ai import Portkey

portkey = Portkey(
    api_key="YOUR_PORTKEY_KEY",
    virtual_key="{get_virtual_key() or 'your-virtual-key-slug'}"
)

response = portkey.chat.completions.create(
    model="{PRIMARY_MODEL}",
    messages=[{{"role": "user", "content": "..."}}]
)
print(response.choices[0].message.content)
""",
        language="python"
    )
    st.caption("That's the entire change. Same response format as OpenAI SDK. Everything else happens automatically.")

    st.divider()

    question = question_selector("routing", INTERESTING_QUESTIONS)

    @st.cache_resource
    def get_router():
        from semantic_router import Route, SemanticRouter
        from semantic_router.encoders import FastEmbedEncoder
        encoder = FastEmbedEncoder()
        casual = Route(
            name="casual_chat",
            utterances=["hello", "how are you", "tell me a joke", "good morning", "what's up", "hi there",]
        )
        complex_task = Route(
            name="complex_task",
            utterances=["solve this math equation", "write a python script", "explain quantum physics", "analyze this data", "how does a database work","Agentic AI realted things","Cloud and Devops","LLM Security"]
        )
        return SemanticRouter(encoder=encoder, routes=[casual, complex_task], auto_sync="local")

    # Semantic intent classification for conditional routing
    router = get_router()
    route_choice = router(question).name
    
    is_complex = route_choice != "casual_chat"
    routed_model = PRIMARY_MODEL if is_complex else "llama-3.1-8b-instant"
    if st.button("Run Through Gateway", type="primary", width="stretch"):
        with st.spinner(f"Routing to {routed_model}..."):
            try:
                client = make_client()
                response, elapsed = timed_call(client, build_messages(question), model=routed_model)
                text = extract_text(response)
                model = get_model_used(response)
                st.session_state.routing_result = {
                    "text": text,
                    "latency": elapsed,
                    "model": model,
                    "tokens": getattr(getattr(response, "usage", None), "total_tokens", "—"),
                    "routed_model": routed_model,
                    "is_complex": is_complex
                }
            except Exception as e:
                st.error(f"Error: {e}")
                return

    if st.session_state.get("routing_result"):
        r = st.session_state.routing_result
        st.divider()
        st.subheader("Result")

        col1, col2, col3 = st.columns(3)
        col1.metric("Latency", f"{r['latency']} ms")
        col2.metric("Total Tokens", r["tokens"])
        col3.metric("Complexity", "Complex" if r["is_complex"] else "Simple", delta="Routed to " + r["routed_model"].split("-")[0])

        st.write(r["text"])
        st.caption(f"Model actually used: {r['model']}")

        st.divider()
        st.subheader("Semantic Routing in Action")
        st.write(
            f"Instead of basic keyword matching, the Gateway used **Semantic Router** with vector embeddings! "
            f"It mathematically compared your prompt to known intents and triggered the `{route_choice or 'default'}` route, "
            f"dynamically sending your request to `{r['routed_model']}`."
        )
        st.success("Check portkey.ai > Logs to see this request appear.")
