"""User-shaped API responses — never expose the password hash."""

import pydantic

from app.models.user import UserRole


class UserPublic(pydantic.BaseModel):
    """How a user looks from the outside — e.g. the /auth/me response. Does NOT include the password hash, which is private to the server."""

    # from_attributes (Pydantic v2; v1 called it "orm_mode") tells
    # Pydantic this model can be built FROM an arbitrary Python object
    # by reading its ATTRIBUTES (user.id, user.email, ...) — not from
    # a dict. That lets an endpoint hand the raw SQLAlchemy `User`
    # object straight to response_model=UserPublic and let Pydantic
    # pick out exactly the fields listed below.
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    email: pydantic.EmailStr
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool