"""Runtime configuration, read from environment variables.

Everything config-related lives here, so the rest of the app imports plain
names (JWT_SECRET, CORS_ORIGINS, ...) and never touches os.environ — one
place to look, one place to fail loudly.
"""

import os

# Secret used to sign/verify JWTs — required, the app fails fast without it.
JWT_SECRET = os.environ["JWT_SECRET"]

JWT_ALGORITHM = "HS256"

# Access-token lifetime in minutes (defaults to one hour).
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "60"))

# CORS: which browser origins may call this API. The browser (not us)
# enforces CORS — this list is us answering the browser's question
# "may origin X talk to you?". Comma-separated; the Vite dev server is
# published at http://localhost:5173.
CORS_ORIGINS = [origin.strip().rstrip("/") for origin in os.environ.get("FRONTEND_ENDPOINT", "").split(",") if origin.strip()]
