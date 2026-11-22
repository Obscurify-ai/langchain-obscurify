# langchain-obscurify

LangChain chat model for [Obscurify.ai](https://obscurify.ai/?utm_source=langchain-obscurify), a private AI chat service with an OpenAI-compatible API (200+ models).

`ChatObscurify` supports invoke, streaming, async, tool calling, structured output and reasoning effort.

## Install

```bash
pip install -U langchain-obscurify
```

## Get an API key

1. Create an account at [obscurify.ai](https://obscurify.ai/?utm_source=langchain-obscurify). An account is a random account code: no email, username or phone.
2. Add a balance. The API works on every plan with a positive balance. New accounts may get $1 of starter credit while this month's promo budget lasts (see https://obscurify.ai/pricing).
3. Open https://obscurify.ai/account and click **Show API Key**. Keys look like `sk-obs1_...`.

```bash
export OBSCURIFY_API_KEY="sk-obs1_..."
```

## Usage

```python
from langchain_obscurify import ChatObscurify

model = ChatObscurify(model="deepseek/deepseek-v4-flash", temperature=0)

print(model.invoke("Write a haiku about privacy.").content)

for chunk in model.stream("Count to five."):
    print(chunk.text, end="", flush=True)
```

### Tool calling

```python
from langchain_core.tools import tool


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"It is sunny in {city}."


msg = model.bind_tools([get_weather]).invoke("What's the weather in Paris?")
print(msg.tool_calls)
```

### Structured output

```python
from pydantic import BaseModel


class Joke(BaseModel):
    setup: str
    punchline: str


print(model.with_structured_output(Joke).invoke("Tell me a joke about cats"))
```

### Reasoning

```python
model = ChatObscurify(model="z-ai/glm-5.3-flash", reasoning_effort="low")
msg = model.invoke("Is 221 prime?")
print(msg.additional_kwargs.get("reasoning_content"))
print(msg.content)
```

### Agents

```python
from langchain.agents import create_agent

agent = create_agent(ChatObscurify(model="deepseek/deepseek-v4-flash"), tools=[get_weather])
agent.invoke({"messages": [{"role": "user", "content": "Weather in Oslo?"}]})
```

## Models

Any model ID from `GET https://obscurify.ai/v1/models` works, for example `deepseek/deepseek-v4-flash`, `meta-llama/llama-3.3-70b-instruct`, `z-ai/glm-5.3-flash` or `qwen/qwen3.8-27b`. Frontier models need the Casual plan; uncensored models need Pro. Prices per model: https://obscurify.ai/models.

## Configuration

| Argument | Env var | Default |
|---|---|---|
| `api_key` | `OBSCURIFY_API_KEY` | none (required) |
| `base_url` | `OBSCURIFY_API_BASE` | `https://obscurify.ai/v1` |

All other `ChatOpenAI` arguments (`temperature`, `max_tokens`, `timeout`, `max_retries`, `reasoning_effort`, `model_kwargs`, ...) work the same way.

## Privacy

Obscurify.ai doesn't store prompts or responses, and scrambles identities before requests reach model providers. Models in the "Zero retention" category of `/v1/models` run only on zero-data-retention routes, which rely on their providers' published policies. Other models follow their provider's own policy. Details: https://obscurify.ai/privacy.

## Links

- API docs: https://obscurify.ai/api-docs
- Source: https://github.com/Obscurify-ai/langchain-obscurify
- JavaScript package: [`@obscurify/langchain`](https://www.npmjs.com/package/@obscurify/langchain)
- Contact: https://obscurify.ai/contact

MIT licensed.
