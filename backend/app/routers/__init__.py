# This package contains one router per domain module (auth, users,
# grades, ...). Each router owns one URL prefix and is registered in
# app/main.py.

from app.routers import auth, admin

__all__ = ["auth", "admin"]
