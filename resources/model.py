from __future__ import annotations
from pydantic import BaseModel
from typing import List

class trade_quantity_model(BaseModel):
    num_shares: int
    ticker: str
    # class Config:
    #     orm_mode = True

class PortfolioComposition(BaseModel):
    ticker: str
    num_shares: int
    avg_price: float
    current_price: float

class PortfolioModel(BaseModel):
    member_id: int
    is_benchmark: str
    portfolio_value: float
    portfolio: List[PortfolioComposition]




