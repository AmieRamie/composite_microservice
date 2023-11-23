from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List

class trade_quantity_model(BaseModel):
    num_shares: int
    price_per_share: float
    # class Config:
    #     orm_mode = True

class PortfolioComposition(BaseModel):
    ticker: str
    num_shares: int
    avg_price: float
    current_price: float

class data_returns(BaseModel):
    status_code:int
    text:str
    body:dict


class PortfolioModel(BaseModel):
    member_id: int
    is_benchmark: str
    portfolio_value: float
    cash_balance: float
    portfolio: List[PortfolioComposition]

class pagination_model(BaseModel):
    data: List[PortfolioModel]
    links: list
    
class non_pagination_model(BaseModel):
    data: List[PortfolioModel]

class sql_query_str(BaseModel):
    query:str

## MEMBERS SCHEMA ##
## MEMBERS SCHEMA ##
class MemberSchema(BaseModel):
    member_name: str
    portfolio_value: float
    age: int

class Member(MemberSchema):
    id: Optional[int]

    class Config:
        orm_mode = True
