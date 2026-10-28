import type { BaseMessage, BaseMessageChunk } from "@langchain/core/messages";
import { getEnvironmentVariable } from "@langchain/core/utils/env";
import {
  ChatOpenAICompletions,
  type ChatOpenAICallOptions,
  type ChatOpenAIFields,
  type OpenAIClient,
} from "@langchain/openai";

export const OBSCURIFY_BASE_URL = "https://obscurify.ai/v1";

export interface ChatObscurifyCallOptions extends ChatOpenAICallOptions {}

export interface ChatObscurifyInput extends ChatOpenAIFields {
  /**
   * Obscurify.ai API key (`sk-obs1_...`). Defaults to the
   * `OBSCURIFY_API_KEY` environment variable.
   */
  apiKey?: string;
  /**
   * API base URL. Defaults to `OBSCURIFY_API_BASE` or https://obscurify.ai/v1.
   */
  baseURL?: string;
}

/**
 * Chat model for the Obscurify.ai API, a private AI service with an
 * OpenAI-compatible API.
 *
 * ```ts
 * import { ChatObscurify } from "@obscurify/langchain";
 *
 * const model = new ChatObscurify({ model: "deepseek/deepseek-v4-flash" });
 * const res = await model.invoke("Write a haiku about privacy.");
 * ```
 *
 * Reasoning text, when a model returns it, is in
 * `message.additional_kwargs.reasoning_content`.
 */
export class ChatObscurify extends ChatOpenAICompletions<ChatObscurifyCallOptions> {
  static lc_name() {
    return "ChatObscurify";
  }

  _llmType() {
    return "obscurify";
  }

  get lc_secrets(): { [key: string]: string } | undefined {
    return { apiKey: "OBSCURIFY_API_KEY" };
  }

  lc_serializable = true;

  lc_namespace = ["obscurify", "chat_models"];

  constructor(
    modelOrFields?: string | ChatObscurifyInput,
    fieldsArg?: Omit<ChatObscurifyInput, "model">
  ) {
    const fields: ChatObscurifyInput =
      typeof modelOrFields === "string"
        ? { ...(fieldsArg ?? {}), model: modelOrFields }
        : (modelOrFields ?? {});
    const apiKey = fields.apiKey || getEnvironmentVariable("OBSCURIFY_API_KEY");
    if (!apiKey) {
      throw new Error(
        'Obscurify.ai API key not found. Set the OBSCURIFY_API_KEY environment variable or pass "apiKey".'
      );
    }
    const baseURL =
      fields.baseURL ||
      fields.configuration?.baseURL ||
      getEnvironmentVariable("OBSCURIFY_API_BASE") ||
      OBSCURIFY_BASE_URL;
    super({
      streamUsage: true,
      ...fields,
      apiKey,
      configuration: { ...fields.configuration, baseURL },
    });
  }

  get streamEventProvider() {
    return "obscurify";
  }

  protected override _convertCompletionsDeltaToBaseMessageChunk(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    delta: Record<string, any>,
    rawResponse: OpenAIClient.Chat.Completions.ChatCompletionChunk,
    defaultRole?: OpenAIClient.Chat.ChatCompletionRole
  ): BaseMessageChunk {
    const chunk = super._convertCompletionsDeltaToBaseMessageChunk(
      delta,
      rawResponse,
      defaultRole
    );
    const reasoning = delta.reasoning ?? delta.reasoning_content;
    if (typeof reasoning === "string" && reasoning) {
      chunk.additional_kwargs.reasoning_content = reasoning;
    }
    chunk.response_metadata = {
      ...chunk.response_metadata,
      model_provider: "obscurify",
    };
    return chunk;
  }

  protected override _convertCompletionsMessageToBaseMessage(
    message: OpenAIClient.ChatCompletionMessage,
    rawResponse: OpenAIClient.ChatCompletion
  ): BaseMessage {
    const msg = super._convertCompletionsMessageToBaseMessage(message, rawResponse);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const extra = message as any;
    const reasoning = extra.reasoning ?? extra.reasoning_content;
    if (typeof reasoning === "string" && reasoning) {
      msg.additional_kwargs.reasoning_content = reasoning;
    }
    msg.response_metadata = { ...msg.response_metadata, model_provider: "obscurify" };
    return msg;
  }
}
