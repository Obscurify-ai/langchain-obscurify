// Live tests against the Obscurify.ai API. Needs OBSCURIFY_API_KEY.
import { describe, expect, test } from "vitest";
import { AIMessageChunk } from "@langchain/core/messages";
import { tool } from "@langchain/core/tools";
import { z } from "zod";
import { ChatObscurify } from "../src/index.js";

const MODEL = "deepseek/deepseek-v4-flash";
const REASONING_MODEL = "z-ai/glm-5.3-flash";

const getWeather = tool(async ({ city }) => `It is 21C and sunny in ${city}.`, {
  name: "get_weather",
  description: "Get the current weather for a city.",
  schema: z.object({ city: z.string() }),
});

describe("ChatObscurify (live)", { timeout: 120_000 }, () => {
  test("invoke", async () => {
    const model = new ChatObscurify({ model: MODEL, maxTokens: 30 });
    const res = await model.invoke("Say the word 'banana' and nothing else.");
    expect(String(res.content).toLowerCase()).toContain("banana");
    expect(res.usage_metadata?.input_tokens).toBeGreaterThan(0);
    expect(res.response_metadata.model_provider).toBe("obscurify");
  });

  test("string model constructor", async () => {
    const model = new ChatObscurify(MODEL, { maxTokens: 10 });
    const res = await model.invoke("Reply with OK.");
    expect(String(res.content).length).toBeGreaterThan(0);
  });

  test("stream", async () => {
    const model = new ChatObscurify({ model: MODEL, maxTokens: 60 });
    let full: AIMessageChunk | undefined;
    let n = 0;
    for await (const chunk of await model.stream("Count from 1 to 5, comma separated.")) {
      full = full ? full.concat(chunk) : chunk;
      n++;
    }
    expect(n).toBeGreaterThan(1);
    expect(String(full?.content)).toContain("3");
  });

  test("tool calling (invoke and stream)", async () => {
    const model = new ChatObscurify({ model: MODEL, temperature: 0 }).bindTools([getWeather], {
      tool_choice: "any",
    });
    const res = await model.invoke("What's the weather in Paris?");
    expect(res.tool_calls?.[0]?.name).toBe("get_weather");
    expect(String(res.tool_calls?.[0]?.args.city).toLowerCase()).toContain("paris");

    let full: AIMessageChunk | undefined;
    for await (const chunk of await model.stream("What's the weather in Oslo?")) {
      full = full ? full.concat(chunk) : chunk;
    }
    expect(full?.tool_calls?.[0]?.name).toBe("get_weather");
  });

  test("structured output", async () => {
    const model = new ChatObscurify({ model: MODEL, temperature: 0 });
    const joke = await model
      .withStructuredOutput(z.object({ setup: z.string(), punchline: z.string() }))
      .invoke("Tell me a joke about cats");
    expect(joke.setup.length).toBeGreaterThan(0);
    expect(joke.punchline.length).toBeGreaterThan(0);
  });

  test("reasoning effort returns reasoning", async () => {
    const model = new ChatObscurify({ model: REASONING_MODEL, reasoning: { effort: "low" }, maxTokens: 2000 });
    const res = await model.invoke("Is 221 prime? Answer yes or no.");
    expect(String(res.content).toLowerCase()).toContain("no");
    expect(res.additional_kwargs.reasoning_content).toBeTruthy();

    let full: AIMessageChunk | undefined;
    for await (const chunk of await model.stream("Is 221 prime? Answer yes or no.")) {
      full = full ? full.concat(chunk) : chunk;
    }
    expect(full?.additional_kwargs.reasoning_content).toBeTruthy();
  });

  test("agent tool loop", async () => {
    const { createAgent } = await import("langchain");
    const agent = createAgent({
      model: new ChatObscurify({ model: MODEL, temperature: 0 }),
      tools: [getWeather],
    });
    const out = await agent.invoke({
      messages: [{ role: "user", content: "What's the weather in Lima?" }],
    });
    const last = out.messages[out.messages.length - 1];
    expect(String(last.content)).toContain("21");
  });
});
