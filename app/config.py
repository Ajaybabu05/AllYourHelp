import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:

    # --------------------------------------------------
    # Core application settings
    # --------------------------------------------------

    SECRET_KEY = os.getenv("SECRET_KEY")

    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY is not set. Add a strong SECRET_KEY to your .env file."
        )

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError(
            "DATABASE_URL is not set. Add your PostgreSQL connection string to .env."
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --------------------------------------------------
    # Debug / environment
    # --------------------------------------------------

    DEBUG = os.getenv(
        "FLASK_DEBUG",
        "0"
    ).lower() in ("1", "true", "yes")

    # Set APP_ENV=production when deploying.
    APP_ENV = os.getenv(
        "APP_ENV",
        "development"
    ).lower()

    # --------------------------------------------------
    # Session and cookie security
    # --------------------------------------------------

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = (
        os.getenv(
            "SESSION_COOKIE_SECURE",
            "False"
        ).lower() == "true"
    )

    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE

    # Limit how long an inactive session remains valid.
    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=30
    )

    SESSION_REFRESH_EACH_REQUEST = True

    # --------------------------------------------------
    # Request limits
    # --------------------------------------------------

    # Protect the application from unexpectedly large uploads.
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # --------------------------------------------------
    # Email configuration
    # --------------------------------------------------

    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(
        os.getenv(
            "MAIL_PORT",
            587
        )
    )
    MAIL_USE_TLS = os.getenv(
        "MAIL_USE_TLS",
        "True"
    ).lower() == "true"
    MAIL_USE_SSL = os.getenv(
        "MAIL_USE_SSL",
        "False"
    ).lower() == "true"

    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")
