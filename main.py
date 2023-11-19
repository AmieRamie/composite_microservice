from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import RedirectResponse

import uvicorn


from resources.model import trade_quantity_model, PortfolioModel
from typing import List
import requests

import asyncio

app = FastAPI()


@app.get("/")
async def root():
    return {'message':'This works!'}

@app.post("/api/composite/{member_id}/buy_stock/", response_model=List[PortfolioModel])
async def buy_stock(member_id:int,item: trade_quantity_model):
    trade_quantity_info = item.dict()
    ticker = trade_quantity_info['ticker']
    num_shares = trade_quantity_info['num_shares']
    #Getting updated price for ticker from Lambda function microservice
    headers = {"x-api-key": "jHZjspQE0uA9tSL8eWwK5knja7tmnC81ekpOzGF8"}

    res = requests.post('https://dph6awgc5h.execute-api.us-east-2.amazonaws.com/default/update_stock_info_containerized',json = {"ticker":ticker},headers = headers)

    print(res.json())
    #Using the updated price info and the number of shares bought of a given ticker to update the portfolio value for the member
    current_ticker_info = res.json()
    response = requests.post(f'http://ec2-13-58-213-131.us-east-2.compute.amazonaws.com:8015/api/portfolios/{member_id}/buy_stock/{ticker}',json = {"num_shares":num_shares,"price_per_share":float(current_ticker_info['current_price'])})
    
    #update the stock db with the current price TODO!!!
    
    return response.json()

@app.post("/api/composite/{member_id}/sell_stock/", response_model=List[PortfolioModel])
async def sell_stock(member_id:int,item: trade_quantity_model):
    trade_quantity_info = item.dict()
    ticker = trade_quantity_info['ticker']
    num_shares = trade_quantity_info['num_shares']
    #Getting updated price for ticker from Lambda function microservice
    headers = {"x-api-key": "jHZjspQE0uA9tSL8eWwK5knja7tmnC81ekpOzGF8"}
    res = requests.post('https://dph6awgc5h.execute-api.us-east-2.amazonaws.com/default/update_stock_info_containerized',json = {"ticker":ticker},headers = headers)

    print(res.json())
    #Using the updated price info and the number of shares bought of a given ticker to update the portfolio value for the member
    current_ticker_info = res.json()
    response = requests.post(f'http://ec2-13-58-213-131.us-east-2.compute.amazonaws.com:8015/api/portfolios/{member_id}/sell_stock/{ticker}',json = {"num_shares":num_shares,"price_per_share":float(current_ticker_info['current_price'])},headers = headers)
    
    #update the stock db with the current price
    
    return response.json()

@app.post("/api/composite/update_stock_price/{ticker}", response_model=List[PortfolioModel])
async def update_stock_price(ticker:str):
    print(ticker)
    return response.json()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8011)