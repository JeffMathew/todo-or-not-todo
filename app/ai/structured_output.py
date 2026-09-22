from pydantic import BaseModel, ValidationError

from app.ai.tool_calling import LLMClient, LLMClientError


class StructuredOutputError(Exception):
    """Raised when the LLM call fails, or its output doesn't validate."""


def get_structured_output[T: BaseModel](
    client: LLMClient,
    *,
    output_model: type[T],
    json_schema: dict,
    tool_name: str,
    tool_description: str,
    system_prompt: str,
    user_message: str,
) -> T:
    """Force a tool call and validate its result into output_model."""
    try:
        raw = client.call_tool(
            system_prompt=system_prompt,
            user_message=user_message,
            tool_name=tool_name,
            tool_description=tool_description,
            tool_schema=json_schema,
        )
    except LLMClientError as exc:
        raise StructuredOutputError(str(exc)) from exc

    try:
        return output_model.model_validate(raw)
    except ValidationError as exc:
        raise StructuredOutputError(
            "The AI returned data that didn't match the expected shape."
        ) from exc
