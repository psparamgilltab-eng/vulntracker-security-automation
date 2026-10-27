
import os
import secrets


# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./vulntracker.db",
)

# JWT configuration.
# A temporary random key keeps local development working if SECRET_KEY
# is not configured. Set a persistent SECRET_KEY in every real deployment.
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)

# Keep the signing algorithm fixed to the supported secure algorithm.
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)

# Optional database credentials for deployments that use a database
# requiring separate credentials. Do not use these as embedded secrets.
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Optional internal service API key.
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")

# Notification service URL
NOTIFY_SERVICE_URL = os.getenv(
    "NOTIFY_SERVICE_URL",
    "http://localhost:3001",
)
