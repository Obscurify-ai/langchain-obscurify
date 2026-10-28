"""LangChain standard integration tests against the live Obscurify.ai API.

Needs OBSCURIFY_API_KEY. Run with: uv run --group test pytest tests/integration_tests
"""

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_tests.integration_tests import ChatModelIntegrationTests

from langchain_obscurify import ChatObscurify

MODEL = "deepseek/deepseek-v4-flash"


class TestChatObscurify(ChatModelIntegrationTests):
    @property
    def chat_model_class(self) -> type[BaseChatModel]:
        return ChatObscurify

    @property
    def chat_model_params(self) -> dict:
        return {"model": MODEL, "temperature": 0, "max_retries": 2}

    @property
    def has_tool_choice(self) -> bool:
        return True

    @property
    def supports_json_mode(self) -> bool:
        return True

    @property
    def supports_image_inputs(self) -> bool:
        return False

    @pytest.mark.xfail(reason="The API doesn't send a usage chunk when streaming yet.")
    def test_usage_metadata_streaming(self, model: BaseChatModel) -> None:
        super().test_usage_metadata_streaming(model)
