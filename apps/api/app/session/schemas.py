from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.session.roles import Role


class RosterPerson(BaseModel):
    model_config = ConfigDict(extra="forbid")

    person_id: str
    name: str
    rank: str
    tile_order: int
    active: bool
    default_screen: int
    roles: list[Role] = Field(default_factory=lambda: [Role.WATCH_OFFICER])

    @property
    def role_set(self) -> frozenset[Role]:
        return frozenset(self.roles)


class RosterResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RosterPerson]


class SessionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    person_id: str = Field(min_length=1)


class SessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    person_id: str
    name: str
    rank: str
    started_at: datetime
    expires_at: datetime
    token: str
    default_screen: int
