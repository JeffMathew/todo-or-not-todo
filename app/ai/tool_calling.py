from typing import Annotated, Any, Protocol

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import Depends

from app.config import settings


class LLMClientError(Exception):
    """Raised when the underlying LLM call fails or returns something unusable."""


class LLMClient(Protocol):
    """Minimal interface: force a named tool call, get back its raw input dict.

    Implement this against a different provider's API to plug it in - see
    README.md's "Extending LLMClient for other providers" section.
    """

    def call_tool(
        self,
        *,
        system_prompt: str,
        user_message: str,
        tool_name: str,
        tool_description: str,
        tool_schema: dict[str, Any],
    ) -> dict[str, Any]:
        """Force the model to call tool_name and return its raw input dict."""
        ...


class BedrockLLMClient:
    """Calls AWS Bedrock's Converse API with forced tool use.

    Works unchanged with any model Bedrock hosts, since Converse normalizes
    every vendor's response into the same shape - that's what lets this one
    class serve both Anthropic and OpenAI models without provider-specific code.
    """

    def __init__(self, model_id: str | None, region: str | None) -> None:
        if not model_id or not region:
            raise LLMClientError(
                "AI features require BEDROCK_MODEL_ID and AWS_REGION to be set."
            )
        self._model_id = model_id
        self._client = boto3.client("bedrock-runtime", region_name=region)

    def call_tool(
        self,
        *,
        system_prompt: str,
        user_message: str,
        tool_name: str,
        tool_description: str,
        tool_schema: dict[str, Any],
    ) -> dict[str, Any]:
        """Call Bedrock's Converse API and return the tool call's input dict."""
        try:
            response = self._client.converse(
                modelId=self._model_id,
                system=[{"text": system_prompt}],
                messages=[{"role": "user", "content": [{"text": user_message}]}],
                toolConfig={
                    "tools": [
                        {
                            "toolSpec": {
                                "name": tool_name,
                                "description": tool_description,
                                "inputSchema": {"json": tool_schema},
                            }
                        }
                    ],
                    "toolChoice": {"tool": {"name": tool_name}},
                },
            )
        except (ClientError, BotoCoreError) as exc:
            raise LLMClientError(f"Bedrock call failed: {exc}") from exc

        content = response.get("output", {}).get("message", {}).get("content", [])
        for block in content:
            if "toolUse" in block:
                return block["toolUse"]["input"]
        raise LLMClientError("Model did not return a tool call.")


def get_llm_client() -> LLMClient:
    """FastAPI dependency: build a BedrockLLMClient from the configured model/region."""
    return BedrockLLMClient(settings.bedrock_model_id, settings.aws_region)


LLMClientDep = Annotated[LLMClient, Depends(get_llm_client)]
