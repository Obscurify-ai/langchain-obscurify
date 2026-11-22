# langchain-obscurify

LangChain integrations for [Obscurify.ai](https://obscurify.ai/?utm_source=langchain-obscurify), a private AI chat service with an OpenAI-compatible API (200+ models). Obscurify.ai doesn't store prompts or responses, and an account is a random account code with no email.

| Language | Package | Class | Source |
|---|---|---|---|
| Python | [`langchain-obscurify`](https://pypi.org/project/langchain-obscurify/) | `ChatObscurify` | [`libs/python`](libs/python) |
| JavaScript / TypeScript | [`@obscurify/langchain`](https://www.npmjs.com/package/@obscurify/langchain) | `ChatObscurify` | [`libs/js`](libs/js) |

Both support invoke, streaming, tool calling, structured output, reasoning effort and LangChain agents.

## Quick start

Get an API key: create an account at [obscurify.ai](https://obscurify.ai/?utm_source=langchain-obscurify), add a balance (the API works on every plan with a positive balance; new accounts may get $1 of starter credit while this month's promo budget lasts), then click **Show API Key** on https://obscurify.ai/account.

```bash
export OBSCURIFY_API_KEY="sk-obs1_..."
```

Python:

```bash
pip install -U langchain-obscurify
```

```python
from langchain_obscurify import ChatObscurify

model = ChatObscurify(model="deepseek/deepseek-v4-flash")
print(model.invoke("Write a haiku about privacy.").content)
```

JavaScript:

```bash
npm install @obscurify/langchain @langchain/core
```

```ts
import { ChatObscurify } from "@obscurify/langchain";

const model = new ChatObscurify({ model: "deepseek/deepseek-v4-flash" });
console.log((await model.invoke("Write a haiku about privacy.")).content);
```

Full docs: [Python README](libs/python/README.md), [JavaScript README](libs/js/README.md), and the API reference at https://obscurify.ai/api-docs.

## Tests

The tests call the live API, so they need `OBSCURIFY_API_KEY`.

```bash
cd libs/python && uv run --group test pytest tests/integration_tests   # includes LangChain's standard integration tests
cd libs/js && npm install && npm run test:int
```

## Releases

Tag `py-vX.Y.Z` to publish the Python package to PyPI and `js-vX.Y.Z` to publish the npm package. Both use trusted publishing from GitHub Actions.

MIT licensed. Questions: https://obscurify.ai/contact
