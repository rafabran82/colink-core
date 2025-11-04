from pydantic import BaseModel, Field

class AirdropReq(BaseModel):
    to: str = Field(description="Destination classic address")
    amount: str = Field(description="IOU value (string)")

class TrustlineReq(BaseModel):
    limit: str = Field(default="1000000", description="Trust limit value (string)")

class OfferReq(BaseModel):
    side: str = Field(description='"SELL_COL" or "BUY_COL"')
    iou: str = Field(description="Amount of COL as string")
    xrp: str = Field(description="Amount of XRP as string")

class OrderbookResp(BaseModel):
    bids: list
    asks: list

