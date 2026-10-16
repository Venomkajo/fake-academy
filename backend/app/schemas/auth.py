import pydantic


class LoginRequest(pydantic.BaseModel):
    """Body of POST /auth/login: credentials the user typed in."""

    email: pydantic.EmailStr
    password: str = pydantic.Field(max_length=128)


class TokenResponse(pydantic.BaseModel):
    """Response of POST /auth/login: the freshly issued JWT.

    The frontend will store `access_token` and send it back on every
    request in the `Authorization: Bearer <token>` header.
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int
