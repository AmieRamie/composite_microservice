from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import RedirectResponse

import uvicorn


from resources.model import non_pagination_model, pagination_model, trade_quantity_model, sql_query_str, PortfolioModel
from typing import List
import requests

import asyncio
import pandas as pd

app = FastAPI()

def put(request_url):
    r = requests.put(request_url)
    return r.json()

@app.get("/")
async def root():
    return {'message':'This works!'}

@app.post("/api/composite/{member_id}/buy_stock/", response_model=non_pagination_model)
async def buy_stock(member_id:int,item: trade_quantity_model):
    trade_quantity_info = item.dict()
    ticker = trade_quantity_info['ticker']
    num_shares = trade_quantity_info['num_shares']
    #Getting updated price for ticker from Lambda function microservice !!!REPLACE WITH STOCK MICROSERVICE ENDPOINT!!!
    headers = {"x-api-key": "jHZjspQE0uA9tSL8eWwK5knja7tmnC81ekpOzGF8"}

    response = requests.post('https://dph6awgc5h.execute-api.us-east-2.amazonaws.com/default/update_stock_info_containerized',json = {"ticker":ticker},headers = headers)
    if response.status_code!=200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['error'])
    print(res.json())
    #Using the updated price info and the number of shares bought of a given ticker to update the portfolio value for the member
    current_ticker_info = res.json()
    response = requests.post(f'http://ec2-13-58-213-131.us-east-2.compute.amazonaws.com:8015/api/portfolios/{member_id}/buy_stock/{ticker}',json = {"num_shares":num_shares,"price_per_share":float(current_ticker_info['current_price'])})
    
    #update the stock db with the current price TODO!!!
    
    if response.status_code!=200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])
    else:
        return response.json()

@app.post("/api/composite/{member_id}/sell_stock/", response_model=non_pagination_model)
async def sell_stock(member_id:int,item: trade_quantity_model):
    trade_quantity_info = item.dict()
    ticker = trade_quantity_info['ticker']
    num_shares = trade_quantity_info['num_shares']
    #Getting updated price for ticker from Lambda function microservice !!!REPLACE WITH STOCK MICROSERVICE ENDPOINT!!!
    headers = {"x-api-key": "jHZjspQE0uA9tSL8eWwK5knja7tmnC81ekpOzGF8"}
    response = requests.post('https://dph6awgc5h.execute-api.us-east-2.amazonaws.com/default/update_stock_info_containerized',json = {"ticker":ticker},headers = headers)
    if response.status_code!=200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['error'])
    print(res.json())
    #Using the updated price info and the number of shares bought of a given ticker to update the portfolio value for the member
    current_ticker_info = res.json()
    response = requests.post(f'http://ec2-13-58-213-131.us-east-2.compute.amazonaws.com:8015/api/portfolios/{member_id}/sell_stock/{ticker}',json = {"num_shares":num_shares,"price_per_share":float(current_ticker_info['current_price'])},headers = headers)
    
    if response.status_code!=200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])
    else:
        return response.json()

@app.post("/api/composite/add_member/{member_id}", response_model=non_pagination_model)
async def add_member(member_id:int):
    #SSO would have to send request to this endpoint
    
    #1. Add member with creds to member service !!!TODO!!!
    #2. Add new portfolio for member
    result = await asyncio.gather(
        # asyncio.create_task(put()),
        # asyncio.create_task(put(f'http://ec2-13-58-213-131.us-east-2.compute.amazonaws.com:8015/api/portfolios/add_portfolio/{member_id}'))
        ## PBY: updated link with POST instead of PUT for add member
        asyncio.create_task(post(f'http://members-docker-env.eba-wdqjeu7i.us-east-2.elasticbeanstalk.com/add_member/{member_id}'))
    )
    response = result[1]
    if response.status_code!=200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['error'])
    else:
        return response

@app.delete("/api/composite/delete_member/{member_id}", response_model=non_pagination_model)
async def remove_member(member_id:int):
    #1. Delete member with creds to member service !!!TODO!!!
    #2. Delete new portfolio for member
    result = await asyncio.gather(
        # asyncio.create_task(put()),
        # asyncio.create_task(put(f'http://ec2-13-58-213-131.us-east-2.compute.amazonaws.com:8015/api/portfolios/delete_portfolio/{member_id}'))
        ## PBY: Updated link with DELETE instead of PUT for delete member
        asyncio.create_task(put(f'http://members-docker-env.eba-wdqjeu7i.us-east-2.elasticbeanstalk.com/remove_member/{member_id}'))
    )
    response = result[1]
    if response.status_code!=200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['error'])
    else:
        return response

@app.put("/api/composite/update_stock_price/{ticker}", response_model=non_pagination_model)
async def update_stock_price(ticker:str):
    #Getting updated price for ticker from Lambda function microservice !!!REPLACE WITH STOCK MICROSERVICE ENDPOINT!!!
    headers = {"x-api-key": "jHZjspQE0uA9tSL8eWwK5knja7tmnC81ekpOzGF8"}
    response = requests.post('https://dph6awgc5h.execute-api.us-east-2.amazonaws.com/default/update_stock_info_containerized',json = {"ticker":ticker},headers = headers)
    if response.status_code!=200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['error'])
    else:
        return response.json()

@app.get("/api/composite/get_portfolios/", response_model=pagination_model)
async def get_specific_portfolio(query_str: str = None, limit: int = 25, page: int = 0):
    print(query_str, limit, page)
    request_url = f"http://ec2-13-58-213-131.us-east-2.compute.amazonaws.com:8015/api/portfolios/?"
    if (pd.notnull(query_str))&(query_str!=''):
        request_url = request_url + f"query_str={query_str}&"
    request_url = request_url + f"limit={limit}&"
    request_url = request_url + f"page={page}"
    print(request_url)
    response = requests.get(request_url)
    if response.status_code!=200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])
    else:
        return response.json()
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8011)
