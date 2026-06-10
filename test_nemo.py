import os
import asyncio
from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.llm.providers import register_llm_provider
from langchain_core.language_models.llms import BaseLLM
from typing import Any, List, Optional

config = RailsConfig.from_path("./nemo_config")

# Mock LLM to test routing without API keys
class MockLLM(BaseLLM):
    def _generate(self, prompts: List[str], stop: Optional[List[str]] = None, **kwargs: Any):
        return None
    @property
    def _llm_type(self) -> str:
        return "mock"
    def invoke(self, *args, **kwargs):
        return "Mock response"
    async def ainvoke(self, *args, **kwargs):
        print(f"DEBUG: LLM Called with: {args}")
        return "Mock response"

register_llm_provider("mock_provider", MockLLM)
config.models[0].engine = "mock_provider"

rails = LLMRails(config)

res = rails.generate(messages=[{"role": "user", "content": "tell me a joke"}])
print("Final Response:", res)
