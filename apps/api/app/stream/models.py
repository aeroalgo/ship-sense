from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


Channel = str


class SubscribeMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["subscribe"]
    subscription_id: str | None = None
    channels: list[Channel] = Field(min_length=1)
    tags: list[str] | None = None
    resume_cursor: dict[Channel, int] = Field(default_factory=dict)
    snapshot: bool = False


class PingMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["ping"]


class UnsubscribeMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["unsubscribe"]
    subscription_id: str | None = None


IncomingMessage = SubscribeMessage | PingMessage | UnsubscribeMessage


def parse_message(payload: Any) -> IncomingMessage:
    if not isinstance(payload, dict):
        raise ValueError("message must be a JSON object")
    action = payload.get("action")
    if action == "subscribe":
        return SubscribeMessage.model_validate(payload)
    if action == "ping":
        return PingMessage.model_validate(payload)
    if action == "unsubscribe":
        return UnsubscribeMessage.model_validate(payload)
    raise ValueError("unsupported action")
