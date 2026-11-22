"""Official OpenAI Responses and Embeddings adapters; network access is explicitly gated."""
import json
import logging
import jsonschema
from backend.citations import ANSWER_SCHEMA
from backend.errors import AppError
from backend.usage import estimate_request

CALCULATION_TOOL = {
    "type": "function", "name": "calculate_depreciation",
    "description": "Calculate a supported depreciation procedure from explicitly supplied facts only. Never invent missing inputs. Use null for unused inputs.",
    "strict": True,
    "parameters": {
        "type": "object", "additionalProperties": False,
        "properties": {
            "method": {"type": "string", "enum": ["straight_line", "reducing_balance", "revised_estimate"]},
            **{key: {"type": ["string", "null"]} for key in (
                "cost", "residual", "life", "opening", "rate", "remaining_life", "months"
            )},
        },
        "required": ["method", "cost", "residual", "life", "opening", "rate", "remaining_life", "months"],
    },
}


class OpenAIProvider:
    def __init__(self, settings, ledger, session_id, client=None):
        self.settings, self.ledger, self.session_id = settings, ledger, session_id
        if not settings.api_enabled:
            raise AppError("Live API access is not enabled. Configure the provider, key and ALLOW_PAID_API.", "api_disabled")
        if client is None:
            from openai import OpenAI
            client = OpenAI(api_key=settings.api_key, base_url="https://api.openai.com/v1",
                            timeout=settings.timeout_seconds, max_retries=1)
        self.client = client

    def _call(self, function, payload, *, embedding=False):
        self.ledger.reserve(self.session_id, estimate_request(
            json.dumps(payload, ensure_ascii=False), self.settings, embedding=embedding
        ), self.settings)
        try:
            result = function(**payload)
        except Exception as error:
            code = type(error).__name__
            logging.getLogger(__name__).warning("provider_failure type=%s", code)
            messages = {
                "AuthenticationError": "The API credentials were rejected. Check the server configuration.",
                "RateLimitError": "The provider's request limit or quota was reached. Try later.",
                "APITimeoutError": "The AI provider timed out after bounded retries. Please retry later.",
                "APIConnectionError": "The AI provider could not be reached.",
            }
            raise AppError(messages.get(code, "The AI provider could not complete this request."), "provider") from None
        usage = getattr(result, "usage", None)
        if usage:
            inputs = getattr(usage, "input_tokens", getattr(usage, "prompt_tokens", 0)) or 0
            outputs = getattr(usage, "output_tokens", 0) or 0
            self.ledger.record(inputs, outputs, self.settings, embedding=embedding)
        return result

    def answer(self, instructions, inputs, *, allow_tools):
        payload = {
            "model": self.settings.model, "instructions": instructions, "input": inputs,
            "max_output_tokens": self.settings.max_output_tokens, "store": False,
            "text": {"format": {"type": "json_schema", "name": "ca_answer",
                                "schema": ANSWER_SCHEMA, "strict": True}},
        }
        if allow_tools:
            payload["tools"] = [CALCULATION_TOOL]
            payload["parallel_tool_calls"] = False
        response = self._call(self.client.responses.create, payload)
        if getattr(response, "status", "completed") != "completed":
            raise AppError("The model response was incomplete. Shorten the question or adjust the output limit.", "incomplete")
        calls = [item for item in response.output if getattr(item, "type", None) == "function_call"]
        if calls:
            if not allow_tools or len(calls) != 1 or calls[0].name != "calculate_depreciation":
                raise AppError("The model requested an unsupported tool.", "tool")
            try:
                arguments = json.loads(calls[0].arguments)
                jsonschema.validate(arguments, CALCULATION_TOOL["parameters"])
            except (ValueError, jsonschema.ValidationError):
                raise AppError("The calculation request was malformed.", "tool") from None
            return {"tool": arguments}
        try:
            return {"answer": json.loads(response.output_text)}
        except (TypeError, ValueError):
            raise AppError("The model refused the request or returned no usable answer.", "invalid_response") from None

    def embed(self, texts):
        response = self._call(self.client.embeddings.create, {
            "model": self.settings.embedding_model, "input": texts,
            "encoding_format": "float",
        }, embedding=True)
        return [item.embedding for item in sorted(response.data, key=lambda item: item.index)]
