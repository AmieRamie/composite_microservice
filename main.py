from fastapi import FastAPI, Response, HTTPException, Query
from fastapi.responses import RedirectResponse

import uvicorn


from resources.model import non_pagination_model, pagination_model, trade_quantity_model, sql_query_str, PortfolioModel
from resources.model import MemberSchema, Member
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

### MEMBERS ###
# Put can update entries of the members DB. Takes in the member name and optional arguments for
# portfolio value, member_name, and age
@app.put("/api/composite/update_member/{member_id}", response_model=non_pagination_model)
async def update_member(member_id: int, member_name = None, portfolio_value = None, age = None):
    # Find the updated member
    get_member = requests.get(f'http://members-docker-env.eba-wdqjeu7i.us-east-2.elasticbeanstalk.com/members/id/{member_id}/')
    if get_member.status_code != 200:
        raise HTTPException(status_code=get_member.status_code, detail=get_member.json()['error'])

    member_update = get_member.json()
    if member_name is not None:
        member_update['member_name'] = member_name
    if portfolio_value is not None:
        member_update['portfolio_value'] = portfolio_value
    if age is not None:
        member_update['age'] = age

    response = requests.put(
        'http://members-docker-env.eba-wdqjeu7i.us-east-2.elasticbeanstalk.com/update_member/',
        json=member_update)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['error'])
    else:
        return response.json()

## GET will return a member json when looking up the DB by member_id
@app.get("/api/composite/member_id/{member_id}", response_model=non_pagination_model)
async def update_stock_price(member_id: int):
    response = requests.get(f'http://members-docker-env.eba-wdqjeu7i.us-east-2.elasticbeanstalk.com/members/id/{member_id}/')
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['error'])
    else:
        return response.json()

## GET will return a member json when looking up the DB by member_name
@app.get("/api/composite/member_name/{member_name}", response_model=non_pagination_model)
async def update_stock_price(member_name: str):
    response = requests.get(f'http://members-docker-env.eba-wdqjeu7i.us-east-2.elasticbeanstalk.com/members/id/{member_name}/')
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['error'])
    else:
        return response.json()

## GET will return a list of members
@app.get("/api/composite/all_members/", response_model=non_pagination_model)
async def update_stock_price(offset: int = None, limit: int = None):
    path = 'http://members-docker-env.eba-wdqjeu7i.us-east-2.elasticbeanstalk.com/members/?'
    if offset is not None:
        path += f'offset={offset}&'
    if limit is not None:
        path += f'limit={limit}'

    response = requests.get(path)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['error'])
    else:
        return response.json()


## GET will return a member json with search parameters
@app.get("/api/composite/search_members/", response_model=non_pagination_model)
async def update_stock_price(offset: int = 0,
                             limit: int = Query(default=10, le=100),
                             member_name: str = None,
                             age_gte: float = None,
                             age_lt: float = None,
                             portfolio_value_gte: float = None,
                             portfolio_value_lt: float = None,
                             sort_by: str = None,):
    path = 'http://members-docker-env.eba-wdqjeu7i.us-east-2.elasticbeanstalk.com/members/search/?'
    if offset is not None:
        path += f'offset={offset}&'
    if limit is not None:
        path += f'limit={limit}&'
    if member_name is not None:
        path += f'member_name={member_name}&'
    if age_gte is not None:
        path += f'age_gte={age_gte}&'
    if age_lt is not None:
        path += f'age_lt={age_lt}&'
    if portfolio_value_gte is not None:
        path += f'portfolio_value_gte={portfolio_value_gte}&'
    if portfolio_value_lt is not None:
        path += f'portfolio_value_lt={portfolio_value_lt}&'
    if sort_by is not None:
        path += f'sort_by={sort_by}'

    response = requests.get(path)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['error'])
    else:
        return response.json()

### END MEMBERS ###


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8011)
