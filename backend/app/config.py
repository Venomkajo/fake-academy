import os

# Secret used to sign/verify JWTs — required, the app fails fast without it.
JWT_SECRET = os.environ["JWT_SECRET"]

JWT_ALGORITHM = "HS256"

# Access-token lifetime in minutes (defaults to one hour).
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "60"))
