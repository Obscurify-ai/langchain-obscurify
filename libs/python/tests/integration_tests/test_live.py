"""Obscurify.ai-specific live checks: reasoning, async streaming, agents."""

import pytest
from langchain_core.messages import AIMessageChunk
from langchain_core.tools import tool

from langchain_obscurify import ChatObscurify

REASONING_MODEL = "z-ai/glm-5.3-flash"


def test_reasoning_effort_returns_reasoning() -> None:
    model = ChatObscurify(model=REASONING_MODEL, reasoning_effort="low", max_tokens=2000)
    msg = model.invoke("Is 221 prime? Answer yes or no.")
    assert msg.content
    assert msg.additional_kwargs.get("reasoning_content")
    assert msg.response_metadata["model_provider"] == "obscurify"


def test_reasoning_streams() -> None:
    model = ChatObscurify(model=REASONING_MODEL, reasoning_effort="low", max_tokens=2000)
    full: AIMessageChunk | None = None
    for chunk in model.stream("Is 221 prime? Answer yes or no."):
        full = chunk if full is None else full + chunk
    assert full is not None
    assert "no" in full.text.lower()
    assert full.additional_kwargs.get("reasoning_content")


@pytest.mark.asyncio
async def test_async_stream() -> None:
    model = ChatObscurify(model="deepseek/deepseek-v4-flash", max_tokens=50)
    text = ""
    async for chunk in model.astream("Say the word 'banana' and nothing else."):
        text += chunk.text
    assert "banana" in text.lower()


def test_agent_tool_loop() -> None:
    from langchain.agents import create_agent

    calls: list[str] = []

    @tool
    def get_weather(city: str) -> str:
        """Get the current weather for a city."""
        calls.append(city)
        return f"It is 21C and sunny in {city}."

    agent = create_agent(
        ChatObscurify(model="deepseek/deepseek-v4-flash", temperature=0),
        tools=[get_weather],
    )
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "What's the weather in Oslo?"}]}
    )
    assert calls and "oslo" in calls[0].lower()
    assert "21" in result["messages"][-1].text
