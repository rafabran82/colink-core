from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from xrpl.wallet import Wallet

class Settings(BaseSettings):
    # Load .env; allow extra so older env names don't break things
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    # Canonical (lowercase) fields; aliases let .env use either UPPER or lower
    rpc_url: str = Field(default="https://s.altnet.rippletest.net:51234", alias="RPC_URL")
    col_code: str = Field(default="COL", alias="COL_CODE")
    col_decimals: int = Field(default=6, alias="COL_DECIMALS")
    issuer_seed: str = Field(default="", alias="ISSUER_SEED")
    trader_seed: str = Field(default="", alias="TRADER_SEED")

    # Derived addresses from seeds (empty string if seed not set)
    @property
    def issuer_addr(self) -> str:
        return Wallet.from_seed(self.issuer_seed).classic_address if self.issuer_seed else ""

    @property
    def trader_addr(self) -> str:
        return Wallet.from_seed(self.trader_seed).classic_address if self.trader_seed else ""

    # Back-compat UPPERCASE properties so old code still works
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
