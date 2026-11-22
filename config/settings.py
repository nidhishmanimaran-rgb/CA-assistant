"""Explicit, validated server configuration. Credentials never leave this module's consumers."""
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Mapping
import os

from dotenv import dotenv_values
from backend.errors import AppError

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    provider: str = "demo"
    model: str = "gpt-6.1-terra"
    api_key: str = field(default="", repr=False)
    allow_paid_api: bool = False
    embedding_backend: str = "local"
    embedding_model: str = "text-embedding-3-small"
    data_dir: Path = ROOT / "data"
    timeout_seconds: int = 40
    max_output_tokens: int = 1800
    daily_budget_usd: Decimal = Decimal("1")
    input_price: Decimal = Decimal("1")
    output_price: Decimal = Decimal("5")
    embedding_price: Decimal = Decimal("0.02")
    session_rpm: int = 8
    global_rpm: int = 30
    max_upload_mb: int = 10
    max_pdf_pages: int = 150
    app_password: str = field(default="", repr=False)
    require_password: bool = False

    @property
    def api_enabled(self) -> bool:
        return self.provider == "openai" and bool(self.api_key) and self.allow_paid_api


def load_settings(secrets: Mapping | None = None, environ: Mapping | None = None,
                  env_file: Path | None = None) -> Settings:
    # No environment mutation: existing environment > cloud secrets > local .env.
    values = dict(dotenv_values(env_file or ROOT / ".env"))
    values.update(dict(secrets or {}))
    values.update(dict(os.environ if environ is None else environ))

    def text(key, default=""):
        value = values.get(key)
        return str(default if value is None or value == "" else value).strip()

    def flag(key, default=False):
        value = text(key, str(default)).lower()
        if value not in ("true", "false", "1", "0"):
            raise AppError(f"{key} must be true or false.", "configuration")
        return value in ("true", "1")

    def integer(key, default, lower, upper):
        try:
            result = int(text(key, default))
            if not lower <= result <= upper:
                raise ValueError()
            return result
        except ValueError:
            raise AppError(f"{key} must be between {lower} and {upper}.", "configuration") from None

    def money(key, default):
        try:
            result = Decimal(text(key, default))
            if not result.is_finite() or result < 0 or result > 1000:
                raise InvalidOperation()
            return result
        except InvalidOperation:
            raise AppError(f"{key} must be a finite amount from 0 to 1000.", "configuration") from None

    provider = text("LLM_PROVIDER", "demo")
    embedding = text("EMBEDDING_BACKEND", "local")
    if provider not in ("demo", "openai") or embedding not in ("local", "openai"):
        raise AppError("Use LLM_PROVIDER=demo/openai and EMBEDDING_BACKEND=local/openai.", "configuration")
    result = Settings(
        provider=provider, model=text("LLM_MODEL", "gpt-6.1-terra"),
        api_key=text("OPENAI_API_KEY"), allow_paid_api=flag("ALLOW_PAID_API"),
        embedding_backend=embedding, embedding_model=text("EMBEDDING_MODEL", "text-embedding-3-small"),
        data_dir=Path(text("DATA_DIR", str(ROOT / "data"))).expanduser().resolve(),
        timeout_seconds=integer("API_TIMEOUT_SECONDS", 40, 5, 120),
        max_output_tokens=integer("MAX_OUTPUT_TOKENS", 1800, 256, 8000),
        daily_budget_usd=money("DAILY_BUDGET_USD", "1"),
        input_price=money("INPUT_PRICE_PER_MILLION", "1"),
        output_price=money("OUTPUT_PRICE_PER_MILLION", "5"),
        embedding_price=money("EMBEDDING_PRICE_PER_MILLION", "0.02"),
        session_rpm=integer("SESSION_REQUESTS_PER_MINUTE", 8, 1, 60),
        global_rpm=integer("GLOBAL_REQUESTS_PER_MINUTE", 30, 1, 300),
        max_upload_mb=integer("MAX_UPLOAD_MB", 10, 1, 20),
        max_pdf_pages=integer("MAX_PDF_PAGES", 150, 1, 300),
        app_password=text("APP_PASSWORD"), require_password=flag("REQUIRE_PASSWORD"),
    )
    if result.require_password and len(result.app_password) < 12:
        raise AppError("Set APP_PASSWORD to at least 12 characters before enabling protected access.", "configuration")
    if result.model != "gpt-6.1-terra" and not all(values.get(k) for k in (
        "INPUT_PRICE_PER_MILLION", "OUTPUT_PRICE_PER_MILLION"
    )):
        raise AppError("Set current input/output token prices when changing LLM_MODEL.", "configuration")
    return result
