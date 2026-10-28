"""Obscurify.ai chat model for LangChain."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any, Literal, TypeAlias

import openai
from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models import LangSmithParams, LanguageModelInput
from langchain_core.messages import AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGenerationChunk, ChatResult
from langchain_core.runnables import Runnable
from langchain_core.utils import from_env, secret_from_env
from langchain_openai.chat_models.base import BaseChatOpenAI
from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator
from typing_extensions import Self

from langchain_obscurify._version import __version__

DEFAULT_API_BASE = "https://obscurify.ai/v1"

_DictOrPydanticClass: TypeAlias = dict[str, Any] | type[BaseModel]
_DictOrPydantic: TypeAlias = dict[str, Any] | BaseModel


class ChatObscurify(BaseChatOpenAI):
    """Chat model for the Obscurify.ai API.

    Obscurify.ai is a private AI chat service with an OpenAI-compatible API.
    Model IDs look like `deepseek/deepseek-v4-flash` or
    `meta-llama/llama-3.3-70b-instruct`; list them with
    `GET https://obscurify.ai/v1/models`.

    Setup:
        Install the package and set your API key (from
        https://obscurify.ai/account, "Show API Key"):

        ```bash
        pip install -U langchain-obscurify
        export OBSCURIFY_API_KEY="sk-obs1_..."
        ```

    Key init args (completion params):
        model: Model ID, e.g. `deepseek/deepseek-v4-flash`.
        temperature: Sampling temperature.
        max_tokens: Max number of tokens to generate.
        reasoning_effort: Reasoning effort for reasoning models
            (`none`, `low`, `medium`, `high`, ... depending on the model).

    Key init args (client params):
        api_key: Obscurify.ai API key. Read from `OBSCURIFY_API_KEY` if not passed.
        base_url: API base URL. Read from `OBSCURIFY_API_BASE` if set,
            otherwise `https://obscurify.ai/v1`.
        timeout: Request timeout.
        max_retries: Max number of retries.

    Instantiate:
        ```python
        from langchain_obscurify import ChatObscurify

        model = ChatObscurify(model="deepseek/deepseek-v4-flash", temperature=0)
        ```

    Invoke:
        ```python
        model.invoke("Write a haiku about privacy.")
        ```

    Stream:
        ```python
        for chunk in model.stream("Count to five."):
            print(chunk.text, end="")
        ```

    Tool calling:
        ```python
        from pydantic import BaseModel, Field


        class GetWeather(BaseModel):
            '''Get the current weather in a given location'''

            location: str = Field(..., description="City, e.g. Paris")


        model_with_tools = model.bind_tools([GetWeather])
        model_with_tools.invoke("What's the weather in Paris?").tool_calls
        ```

    Structured output:
        ```python
        class Joke(BaseModel):
            setup: str
            punchline: str


        model.with_structured_output(Joke).invoke("Tell me a joke about cats")
        ```

    Reasoning:
        Reasoning text, when a model returns it, is in
        `message.additional_kwargs["reasoning_content"]`.

        ```python
        model = ChatObscurify(model="z-ai/glm-5.3-flash", reasoning_effort="low")
        ```
    """

    model_name: str = Field(alias="model")
    """The name of the model."""
    api_key: SecretStr | None = Field(
        default_factory=secret_from_env("OBSCURIFY_API_KEY", default=None)
    )
    """Obscurify.ai API key."""
    api_base: str = Field(
        alias="base_url",
        default_factory=from_env("OBSCURIFY_API_BASE", default=DEFAULT_API_BASE),
    )
    """Obscurify.ai API base URL.

    Automatically read from env variable `OBSCURIFY_API_BASE` if not provided.
    """

    stream_usage: bool | None = True
    """Ask for token usage when streaming (`stream_options.include_usage`)."""

    model_config = ConfigDict(populate_by_name=True)

    @property
    def _llm_type(self) -> str:
        """Return type of chat model."""
        return "chat-obscurify"

    @property
    def lc_secrets(self) -> dict[str, str]:
        """A map of constructor argument names to secret ids."""
        return {"api_key": "OBSCURIFY_API_KEY"}

    @classmethod
    def is_lc_serializable(cls) -> bool:
        """Return whether this model can be serialized by LangChain."""
        return True

    @classmethod
    def get_lc_namespace(cls) -> list[str]:
        """Get the namespace of the LangChain object."""
        return ["langchain_obscurify", "chat_models"]

    def _get_ls_params(
        self, stop: list[str] | None = None, **kwargs: Any
    ) -> LangSmithParams:
        ls_params = super()._get_ls_params(stop=stop, **kwargs)
        ls_params["ls_provider"] = "obscurify"
        return ls_params

    @model_validator(mode="after")
    def _set_obscurify_version(self) -> Self:
        self._add_version("langchain-obscurify", __version__)
        return self

    @model_validator(mode="after")
    def validate_environment(self) -> Self:
        """Validate the API key and build the OpenAI clients."""
        if self.api_base == DEFAULT_API_BASE and not (
            self.api_key and self.api_key.get_secret_value()
        ):
            msg = "OBSCURIFY_API_KEY must be set (or pass api_key=...)."
            raise ValueError(msg)
        client_params: dict = {
            k: v
            for k, v in {
                "api_key": self.api_key.get_secret_value() if self.api_key else None,
                "base_url": self.api_base,
                "timeout": self.request_timeout,
                "max_retries": self.max_retries,
                "default_headers": self.default_headers,
                "default_query": self.default_query,
            }.items()
            if v is not None
        }
        if not (self.client or None):
            sync_specific: dict = {"http_client": self.http_client}
            self.root_client = openai.OpenAI(**client_params, **sync_specific)
            self.client = self.root_client.chat.completions
        if not (self.async_client or None):
            async_specific: dict = {"http_client": self.http_async_client}
            self.root_async_client = openai.AsyncOpenAI(
                **client_params, **async_specific
            )
            self.async_client = self.root_async_client.chat.completions
        return self

    def _create_chat_result(
        self,
        response: dict | openai.BaseModel,
        generation_info: dict | None = None,
    ) -> ChatResult:
        rtn = super()._create_chat_result(response, generation_info)
        for generation in rtn.generations:
            if generation.message.response_metadata is None:
                generation.message.response_metadata = {}
            generation.message.response_metadata["model_provider"] = "obscurify"

        if not isinstance(response, openai.BaseModel):
            return rtn
        choices = getattr(response, "choices", None)
        if choices:
            extra = getattr(choices[0].message, "model_extra", None) or {}
            reasoning = extra.get("reasoning") or extra.get("reasoning_content")
            if reasoning:
                rtn.generations[0].message.additional_kwargs["reasoning_content"] = (
                    reasoning
                )
        return rtn

    def _convert_chunk_to_generation_chunk(
        self,
        chunk: dict,
        default_chunk_class: type,
        base_generation_info: dict | None,
    ) -> ChatGenerationChunk | None:
        generation_chunk = super()._convert_chunk_to_generation_chunk(
            chunk, default_chunk_class, base_generation_info
        )
        if (choices := chunk.get("choices")) and generation_chunk:
            message = generation_chunk.message
            if isinstance(message, AIMessageChunk):
                message.response_metadata = {
                    **message.response_metadata,
                    "model_provider": "obscurify",
                }
                delta = choices[0].get("delta") or {}
                reasoning = delta.get("reasoning") or delta.get("reasoning_content")
                if reasoning:
                    message.additional_kwargs["reasoning_content"] = reasoning
        return generation_chunk

    def _fix_v1_block_indexes(
        self, chunk: ChatGenerationChunk, state: dict[str, int]
    ) -> ChatGenerationChunk:
        """Keep text and tool-call content blocks apart in v1 streams.

        Some models stream a little text before a tool call. Chat Completions
        numbers both from 0, so with `output_version="v1"` the text block and the
        first tool call block would merge into one. When text came first, shift
        every tool call index in the stream by one.
        """
        if self.output_version != "v1":
            return chunk
        message = chunk.message
        if not isinstance(message, AIMessageChunk):
            return chunk
        if message.tool_call_chunks:
            if "shift" not in state:
                state["shift"] = 1 if state.get("text") else 0
            if state["shift"]:
                for tool_chunk in message.tool_call_chunks:
                    if isinstance(tool_chunk.get("index"), int):
                        tool_chunk["index"] += state["shift"]
        elif message.content and "shift" not in state:
            state["text"] = 1
        return chunk

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        state: dict[str, int] = {}
        for chunk in super()._stream(
            messages, stop=stop, run_manager=run_manager, **kwargs
        ):
            yield self._fix_v1_block_indexes(chunk, state)

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        state: dict[str, int] = {}
        async for chunk in super()._astream(
            messages, stop=stop, run_manager=run_manager, **kwargs
        ):
            yield self._fix_v1_block_indexes(chunk, state)

    def with_structured_output(
        self,
        schema: _DictOrPydanticClass | None = None,
        *,
        method: Literal[
            "function_calling", "json_mode", "json_schema"
        ] = "function_calling",
        include_raw: bool = False,
        strict: bool | None = None,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, _DictOrPydantic]:
        """Model wrapper that returns outputs formatted to match the given schema.

        Defaults to `function_calling`, which works on every model that supports
        tools. `json_schema` and `json_mode` are passed through for models that
        support them.
        """
        return super().with_structured_output(
            schema, method=method, include_raw=include_raw, strict=strict, **kwargs
        )
