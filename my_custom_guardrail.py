from litellm.integrations.custom_logger import CustomLogger

class MyGuardrail(CustomLogger):
    def __init__(self):
        print("Initialized MyGuardrail")

    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        messages = data.get("messages", [])
        for msg in messages:
            content = msg.get("content", "").lower()
            if "joke" in content or "ignore" in content or "hack" in content:
                raise Exception("Blocked by LiteLLM Custom Guardrail: Unsafe keyword detected!")
        return data

proxy_handler_instance = MyGuardrail()
