"""Message-shaped API payloads (README cards S3/W4): threads, announcements, receipts."""

import datetime

import pydantic


class UserBrief(pydantic.BaseModel):
    """A person's identity as message listings show it (never the email)."""

    id: int
    first_name: str
    last_name: str


class MessageOut(pydantic.BaseModel):
    """One message flattened with names, plus the caller's own read receipt.

    `read_by_caller` is True for everything the caller sent themselves and
    for received messages they already opened.
    """

    id: int
    sender_id: int
    sender_first_name: str
    sender_last_name: str
    sender_role: str
    recipient_id: int | None
    recipient_first_name: str | None
    recipient_last_name: str | None
    group_id: int | None
    group_name: str | None
    title: str | None
    content: str
    created_at: datetime.datetime
    read_by_caller: bool


class GroupWithMembers(pydantic.BaseModel):
    """One of the caller's teaching groups with its student members."""

    group_id: int
    group_name: str
    field_name: str
    students: list[UserBrief]


class ContactsResponse(pydantic.BaseModel):
    """Who the caller may write to: teachers (student) or groups with members (teacher)."""

    teachers: list[UserBrief]
    groups: list[GroupWithMembers]


class MessageCreate(pydantic.BaseModel):
    """Body of POST /messages — one individual message OR one group announcement.

    Announcements (group target) REQUIRE a title; private chat messages
    carry none — a title sent with a private target is dropped here.
    """

    title: str | None = pydantic.Field(default=None, max_length=255)
    content: str = pydantic.Field(min_length=1)
    recipient_id: int | None = None
    group_id: int | None = None

    @pydantic.model_validator(mode="after")
    def _exactly_one_target(self) -> "MessageCreate":
        """Require one target; announcements need a title, private chats keep none."""
        if (self.recipient_id is None) == (self.group_id is None):
            raise ValueError("Podaj dokładnie jednego odbiorcę: studenta albo grupę")
        if self.group_id is not None and not (self.title or "").strip():
            raise ValueError("Ogłoszenie grupowe musi mieć tytuł")
        if self.recipient_id is not None:
            # Chat messages never carry a title — drop it even if sent.
            self.title = None
        return self
