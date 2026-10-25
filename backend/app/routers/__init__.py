"""One router per domain module; each owns one URL prefix, registered in app/main.py."""

from app.routers import auth, admin

__all__ = ["auth", "admin"]
