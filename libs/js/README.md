# @obscurify/langchain

LangChain.js chat model for [Obscurify.ai](https://obscurify.ai/?utm_source=langchain-obscurify-js), a private AI chat service with an OpenAI-compatible API (200+ models).

`ChatObscurify` supports invoke, streaming, tool calling, structured output and reasoning effort.

## Install

```bash
npm install @obscurify/langchain @langchain/core
```

## Get an API key

1. Create an account at [obscurify.ai](https://obscurify.ai/?utm_source=langchain-obscurify-js). An account is a random account number: no email, username or phone.
2. Add a balance. The API works on every plan with a positive balance. New accounts get $1 of starter credit (limits apply; see https://obscurify.ai/pricing).
3. Open https://obscurify.ai/account and click **Show API Key**. Keys look like `sk-obs1_...`.

```bash
export OBSCURIFY_API_KEY="sk-obs1_..."
```

## Usage

```ts
import { ChatObscurify } from "@obscurify/langchain";

const model = new ChatObscurify({ model: "deepseek/deepseek-v4-flash", temperature: 0 });

const res = await model.invoke("Write a haiku about privacy.");
console.log(res.content);

for await (const chunk of await model.stream("Count to five.")) {
  process.stdout.write(String(chunk.content));
}
```

### Tool calling

```ts
import { tool } from "@langchain/core/tools";
import { z } from "zod";

const getWeather = tool(async ({ city }) => `It is sunny in ${city}.`, {
  name: "get_weather",
  description: "Get the current weather for a city.",
  schema: z.object({ city: z.string() }),
});

const msg = await model.bindTools([getWeather]).invoke("What's the weather in Paris?");
console.log(msg.tool_calls);
```

### Structured output

```ts
const joke = await model
  .withStructuredOutput(z.object({ setup: z.string(), punchline: z.string() }))
  .invoke("Tell me a joke about cats");
```

### Reasoning

```ts
const thinker = new ChatObscurify({ model: "z-ai/glm-5.3-flash", reasoning: { effort: "low" } });
const res = await thinker.invoke("Is 221 prime?");
console.log(res.additional_kwargs.reasoning_content);
```

### Agents

```ts
import { createAgent } from "langchain";

const agent = createAgent({ model, tools: [getWeather] });
await agent.invoke({ messages: [{ role: "user", content: "Weather in Oslo?" }] });
```

## Models

Any model ID from `GET https://obscurify.ai/v1/models` works, for example `deepseek/deepseek-v4-flash`, `meta-llama/llama-3.3-70b-instruct`, `z-ai/glm-5.3-flash` or `qwen/qwen3.8-27b`. Frontier models need the Casual plan; uncensored models need Pro. Prices per model: https://obscurify.ai/model_cards.

## Configuration

| Option | Env var | Default |
|---|---|---|
| `apiKey` | `OBSCURIFY_API_KEY` | none (required) |
| `baseURL` | `OBSCURIFY_API_BASE` | `https://obscurify.ai/v1` |

All other `ChatOpenAI` options (`temperature`, `maxTokens`, `timeout`, `maxRetries`, `reasoning`, `modelKwargs`, ...) work the same way.

## Privacy

Obscurify.ai doesn't store prompts or responses, scrambles identities before requests reach model providers, and sends text requests only over zero-data-retention routes. Details: https://obscurify.ai/privacy.

## Links

- API docs: https://obscurify.ai/api-docs
- Source: https://github.com/Obscurify-ai/langchain-obscurify
- Python package: [`langchain-obscurify`](https://pypi.org/project/langchain-obscurify/)
- Contact: https://obscurify.ai/contact

MIT licensed.
