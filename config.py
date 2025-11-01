from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from xrpl.wallet import Wallet

class Settings(BaseSettings):
    # XRPL
    rpc_url: str = Field(default="https://s.altnet.rippletest.net:51234", alias="RPC_URL")
    col_code: str = Field(default="COL", alias="COL_CODE")
    col_decimals: int = Field(default=6, alias="COL_DECIMALS")

    # Optional seeds (not needed for PAPER_MODE)
    issuer_seed: Optional[str] = Field(default=None, alias="ISSUER_SEED")
    trader_seed: Optional[str] = Field(default=None, alias="TRADER_SEED")

    # Optional explicit addresses (used if provided; otherwise derived from seeds)
    issuer_addr_env: Optional[str] = Field(default=None, alias="ISSUER_ADDR")
    trader_addr_env: Optional[str] = Field(default=None, alias="TRADER_ADDR")

    # PAPER MODE toggle (1/true/on)
    paper_mode: bool = Field(default=False, alias="PAPER_MODE")

    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)

    @property
    def issuer_seed_error(self) -> str:
        s = (self.issuer_seed or "").strip()
        if not s:
            return ""
        try:
            Wallet.from_seed(s)
            return ""
        except Exception as e:
            return f"{e.__class__.__name__}: {e}"

    @property
    def trader_seed_error(self) -> str:
        s = (self.trader_seed or "").strip()
        if not s:
            return ""
        try:
            Wallet.from_seed(s)
            return ""
        except Exception as e:
            return f"{e.__class__.__name__}: {e}"

    @property
    def issuer_addr(self) -> str:
        if self.issuer_addr_env:
            return self.issuer_addr_env
        if self.issuer_seed and not self.issuer_seed_error:
            return Wallet.from_seed(self.issuer_seed).classic_address
        return ""

    @property
    def trader_addr(self) -> str:
        if self.trader_addr_env:
            return self.trader_addr_env
        if self.trader_seed and not self.trader_seed_error:
            return Wallet.from_seed(self.trader_seed).classic_address
        return ""

settings = Settings()
