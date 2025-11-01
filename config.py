from typing import Tuple
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict
from xrpl.wallet import Wallet

class Settings(BaseSettings):
    # Accept .env, be case-insensitive, and IGNORE unknown/extra keys from env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # <-- critical: ignore xrpl_network, default_trust_limit, etc.
    )

    # Core XRPL / COL
    rpc_url: str = Field(
        default="https://s.altnet.rippletest.net:51234",
        validation_alias=AliasChoices("XRPL_RPC_URL", "RPC_URL"),
    )
    col_code: str = Field(
        default="COL",
        validation_alias=AliasChoices("COL_CURRENCY", "COL_CODE", "col_currency"),
    )
    col_decimals: int = Field(
        default=6,
        validation_alias=AliasChoices("COL_DECIMALS", "col_decimals"),
    )

    # Seeds (may be blank; we never raise if invalid)
    issuer_seed: str = Field(
        default="",
        validation_alias=AliasChoices("ISSUER_SEED", "COL_ISSUER_SEED", "col_issuer_seed"),
    )
    trader_seed: str = Field(
        default="",
        validation_alias=AliasChoices("TRADER_SEED", "COL_TRADER_SEED", "col_trader_seed"),
    )

    # Optional explicit classic addresses (skip derivation if provided)
    issuer_addr_env: str = Field(
        default="",
        validation_alias=AliasChoices("ISSUER_ADDR", "COL_ISSUER", "col_issuer"),
    )
    trader_addr_env: str = Field(
        default="",
        validation_alias=AliasChoices("TRADER_ADDR", "COL_DISTRIBUTOR", "col_distributor"),
    )

    # ---------- helpers ----------
    @staticmethod
    def _safe_addr(seed: str) -> Tuple[str, str]:
        """
        Return (address, err). Never raises.
        - address: "" if seed missing/invalid
        - err: "" when ok; else 'Type: message'
        """
        if not seed:
            return "", ""
        try:
            return Wallet.from_seed(seed).classic_address, ""
        except Exception as e:
            return "", f"{e.__class__.__name__}: {e}"

    # Derived / overridden addresses (NEVER raise)
    @property
    def issuer_addr(self) -> str:
        if self.issuer_addr_env:
            return self.issuer_addr_env
        addr, _ = self._safe_addr(self.issuer_seed)
        return addr

    @property
    def trader_addr(self) -> str:
        if self.trader_addr_env:
            return self.trader_addr_env
        addr, _ = self._safe_addr(self.trader_seed)
        return addr

    # Validation helpers (for /_debug + preflight 400s)
    @property
    def issuer_seed_error(self) -> str:
        _, err = self._safe_addr(self.issuer_seed)
        return err

    @property
    def trader_seed_error(self) -> str:
        _, err = self._safe_addr(self.trader_seed)
        return err

    # Back-compat uppercase attrs
    @property
    def RPC_URL(self): return self.rpc_url
    @property
    def COL_CODE(self): return self.col_code
    @property
    def COL_DECIMALS(self): return self.col_decimals
    @property
    def ISSUER_SEED(self): return self.issuer_seed
    @property
    def TRADER_SEED(self): return self.trader_seed
    @property
    def ISSUER_ADDR(self): return self.issuer_addr
    @property
    def TRADER_ADDR(self): return self.trader_addr


settings = Settings()
