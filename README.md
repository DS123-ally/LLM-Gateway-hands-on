# LLM Gateway Architecture Demo

This project demonstrates an enterprise-grade LLM Gateway architecture using **Portkey** and **LiteLLM**. It showcases how to build a robust, provider-agnostic AI backend capable of advanced routing, failovers, and guardrails, all while maintaining full observability.

## 🌟 Key Features

### 1. Unified API
The application uses a unified API standard (OpenAI format). This means you can swap between models from entirely different providers (e.g., Groq, Mistral, OpenAI, Google Gemini) without changing a single line of your core application code!

### 2. Semantic Routing (`d02_routing.py`)
Instead of relying on fragile keyword matching, the application uses **Semantic Router** with `FastEmbed` mathematical vector embeddings. 
- It instantly converts user prompts into high-dimensional vectors.
- It calculates semantic similarity to route "Casual Chats" to the lightweight and lightning-fast `gemma2-9b-it` model.
- It routes "Complex Tasks" (coding, math, reasoning) to the massive `llama-3.3-70b-versatile` model to ensure high quality while saving costs.

### 3. Cross-Architecture Fallbacks (`d06_fallbacks.py`)
If the primary Llama 3.3 model experiences downtime or hits a rate limit (429/500 errors), the Gateway automatically and seamlessly reroutes the exact same request to a backup model (`mixtral-8x7b-32768`). The frontend application receives the response normally, completely unaware that a major failover occurred.

### 4. Custom Guardrails (`d14_litellm_guardrails.py`)
A custom LiteLLM Proxy is used to intercept requests *before* they reach the LLM. Using a custom Python callback (`my_custom_guardrail.py`), it actively scans the user's prompt for banned keywords and blocks malicious requests instantly, protecting your system from prompt injections and abuse.

### 5. Streaming Normalization (`d10_streaming.py`)
Different open-source models often stream their token chunks in wildly different formats. The Gateway normalizes all incoming streams into a standard structure, preventing your frontend from breaking when the backend model architecture changes.

### 6. Full Observability
Every request that passes through the Gateway is automatically logged in the Portkey dashboard. You get instant access to:
- Full prompt and response text
- Token usage and estimated cost
- Millisecond latency tracking
- The exact model that served the response

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- `uv` package manager installed
- A [Portkey API Key](https://portkey.ai/)
- A [Groq API Key](https://console.groq.com/)

### Installation

1. Install dependencies using `uv`:
```bash
uv sync
```

2. Configure your API keys in the `.env` file:
```env
GROQ_API_KEY=your_groq_key
PORTKEY_API_KEY=your_portkey_key
PORTKEY_VIRTUAL_KEY=your_virtual_key
```

### Running the Application

To start the interactive Streamlit application, run:
```bash
uv run streamlit run app.py
```

### Running the LiteLLM Guardrail Proxy
If you are testing the Guardrails demo, you must start the LiteLLM Proxy in a separate terminal window:
```bash
$env:PYTHONIOENCODING="utf-8"
uv run litellm --config litellm_guardrails_config.yaml --port 4000
```
