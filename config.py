from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# xrpl imports are only used when seeds are present/valid
try:
    from xrpl.wallet import Wallet
except Exception:  # xrpl not installed or similar
    Wallet = None  # type: ignore


def _derive_address_from_seed(seed: str) -> tuple[str, str]:
    """
    Returns (classic_address, error_string). If seed is empty or invalid, address="", error explains why.
    Never raises.
    """
    if not seed:
        return "", ""
    if Wallet is None:
        return "", "xrpl not available in environment"
    try:
        w = Wallet.from_seed(seed)
        return w.classic_address, ""
    except Exception as e:
        return "", f"{type(e).__name__}: {e}"


class Settings(BaseSettings):
    # --- pydantic-settings v2 config ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignore unknown/legacy envs
    )

    # --- Network / asset config ---
    rpc_url: str = Field(
        default="https://s.altnet.rippletest.net:51234",
        validation_alias="RPC_URL",
    )
    col_code: str = Field(default="COL", validation_alias="COL_CODE")
    col_decimals: int = Field(default=6, validation_alias="COL_DECIMALS")

    # --- Paper engine flag ---
    paper_mode: bool = Field(default=False, validation_alias="PAPER_MODE")

    # --- Optional explicit addresses (bypass seed derivation when present) ---
    issuer_addr_env: str = Field(default="", validation_alias="ISSUER_ADDR")
    trader_addr_env: str = Field(default="", validation_alias="TRADER_ADDR")

    # --- Optional secrets (may be blank) ---
    issuer_seed: str = Field(default="", validation_alias="ISSUER_SEED")
    trader_seed: str = Field(default="", validation_alias="TRADER_SEED")

    # --- Seed validation results (computed lazily) ---
    _issuer_addr_from_seed: str | None = None
    _issuer_seed_err: str = ""
    _trader_addr_from_seed: str | None = None
    _trader_seed_err: str = ""

    def _ensure_seed_checks(self) -> None:
        if self._issuer_addr_from_seed is None:
            addr, err = _derive_address_from_seed(self.issuer_seed)
            self._issuer_addr_from_seed, self._issuer_seed_err = addr, err
        if self._trader_addr_from_seed is None:
            addr, err = _derive_address_from_seed(self.trader_seed)
            self._trader_addr_from_seed, self._trader_seed_err = addr, err

    # Exposed properties used by routes/debug:
    @property
    def issuer_addr(self) -> str:
        if self.issuer_addr_env:
            return self.issuer_addr_env
        self._ensure_seed_checks()
        return self._issuer_addr_from_seed or ""

    @property
    def trader_addr(self) -> str:
        if self.trader_addr_env:
            return self.trader_addr_env
        self._ensure_seed_checks()
        return self._trader_addr_from_seed or ""

    @property
    def issuer_seed_error(self) -> str:
        self._ensure_seed_checks()
        return self._issuer_seed_err

    @property
    def trader_seed_error(self) -> str:
        self._ensure_seed_checks()
        return self._trader_seed_err


# Singleton settings object
settings = Settings()
