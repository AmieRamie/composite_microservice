from fastapi import FastAPI, Response, HTTPException, Query
from fastapi.responses import RedirectResponse

import uvicorn



import timeit 
from resources.model import non_pagination_model, pagination_model, trade_quantity_model, sql_query_str, PortfolioModel, SecuritiesModel, InfoWatchlistModel, MemberSchema, Member

from typing import List
import requests
import urllib
import asyncio
import aiohttp
import pandas as pd

app = FastAPI()

def put(request_url):
    r = requests.put(request_url)
    return r.json()
def delete(request_url):
    r = requests.delete(request_url)
    return r.json()

async def fetch(session, url,request_type,return_json):
    try:
        if request_type == 'get':
            async with session.get(url) as response:
                status = response.status  # Synchronous, no await needed
                json_data = await response.json()  if return_json else {} # Asynchronous, await needed
                return status, json_data
        elif request_type == 'put':
            async with session.put(url) as response:
                status = response.status  # Synchronous, no await needed
                json_data = await response.json()  if return_json else {} # Asynchronous, await needed
                return status, json_data
        elif request_type == 'post':
            async with session.post(url) as response:
                status = response.status  # Synchronous, no await needed
                json_data = await response.json()  if return_json else {} # Asynchronous, await needed
                return status, json_data
        elif request_type == 'delete':
            async with session.delete(url) as response:
                status = response.status  # Synchronous, no await needed
                json_data = await response.json()  if return_json else {} # Asynchronous, await needed
                return status, json_data
    except Exception as e:
        return str(e)

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

@app.post("/api/composite/add_member/{member_name}", response_model=non_pagination_model)
async def add_member(member_name:str):
    #SSO would have to send request to this endpoint
    start = timeit.default_timer()
    response = requests.post(f'http://members-docker-env.eba-wdqjeu7i.us-east-2.elasticbeanstalk.com/add_member/{member_name}')
    print(response.json())
    if response.status_code!=200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])
    member_id = response.json()['id']
    response = requests.put(f'http://ec2-13-58-213-131.us-east-2.compute.amazonaws.com:8015/api/portfolios/add_portfolio/{member_id}')
    end = timeit.default_timer()
    print(end-start)
    print(response.json())
    #1. Add member with creds to member service !!!TODO!!!
    #2. Add new portfolio for member

    if response.status_code!=200:
        raise HTTPException(status_code=response.status_code, detail="user already exists")
    else:
        return response.json()

@app.delete("/api/composite/delete_member_syncronous/{member_id}", response_model=non_pagination_model)
async def delete_member_syncronous(member_id:str):
    #SSO would have to send request to this endpoint
    start = timeit.default_timer()
    response = requests.delete(f'http://members-docker-env.eba-wdqjeu7i.us-east-2.elasticbeanstalk.com/remove_member/{member_id}')
    print(response.json())
    if response.status_code!=200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])
    response = requests.delete(f'http://ec2-13-58-213-131.us-east-2.compute.amazonaws.com:8015/api/portfolios/delete_portfolio/{member_id}')
    end = timeit.default_timer()
    print(end-start)
    print(response.json())
    #1. Add member with creds to member service !!!TODO!!!
    #2. Add new portfolio for member

    if response.status_code!=200:
        raise HTTPException(status_code=response.status_code, detail="user already exists")
    else:
        return response.json()

@app.delete("/api/composite/delete_member/{member_id}")
async def remove_member(member_id:int):
    #1. Delete member with creds to member service !!!TODO!!!
    #2. Delete new portfolio for member
    urls = [(f'http://members-docker-env.eba-wdqjeu7i.us-east-2.elasticbeanstalk.com/remove_member/{member_id}','delete',False),(f'http://ec2-13-58-213-131.us-east-2.compute.amazonaws.com:8015/api/portfolios/delete_portfolio/{member_id}','delete',True)]
    async with aiohttp.ClientSession() as session:
        start = timeit.default_timer()
        tasks = [fetch(session, url[0],url[1],url[2]) for url in urls]
        results = await asyncio.gather(*tasks)
        end = timeit.default_timer()
        print(end-start)
        print(results)

        status_code = results[1][0]
        json = results[1][1]
        print(json)
        if status_code!=200:
            raise HTTPException(status_code=status_code, detail='error with input')
        else:
            return json

@app.get("/api/composite/get_security_price/{ticker}", response_model=SecuritiesModel)
async def get_stock_price(ticker:str):
    response = requests.get(f'http://ec2-18-222-118-35.us-east-2.compute.amazonaws.com:8015/securities/{ticker}')

    if response.status_code!=200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])
    else:
        return response.json()
    
@app.get("/api/composite/get_infowatchlist/{ticker}", response_model=InfoWatchlistModel)
async def get_stock_infowatchlist(ticker:str):
    response = requests.get(f'http://ec2-18-222-118-35.us-east-2.compute.amazonaws.com:8015/securities/{ticker}/info_watchlist')

    if response.status_code!=200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])
    else:
        print(response.json())
        return response.json()
    
    
@app.get("/api/composite/get_top_stocks_by_price/", response_model=List[SecuritiesModel])
async def get_top_stocks_by_price(limit: int = 10, offset: int = 0):
    response = requests.get(f'http://ec2-18-222-118-35.us-east-2.compute.amazonaws.com:8015/top_securities_by_price/?limit=' + str(limit) + "&offset" + str(offset))

    if response.status_code!=200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])
    else:
        return response.json()

@app.get("/api/composite/custom_stock_search/", response_model=List[InfoWatchlistModel])
async def get_custom_stock_search(query: str= None, limit: int = 10, page: int = 0):
    if query != None:
        query = urllib.parse.quote_plus(query)
        response = requests.get(f'http://ec2-18-222-118-35.us-east-2.compute.amazonaws.com:8015/securities/custom_security_search/?query='+ query +'&limit=' + str(limit) + "&page=" + str(page))
    else:
        response = requests.get(f'http://ec2-18-222-118-35.us-east-2.compute.amazonaws.com:8015/securities/custom_security_search/?limit=' + str(limit) + "&page=" + str(page))


    if response.status_code!=200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])
    else:
        return response.json()
    
@app.put("/api/composite/update_security_price/{ticker}", response_model = SecuritiesModel)
async def update_security_price(ticker:str):
    response = requests.put(f'http://ec2-18-222-118-35.us-east-2.compute.amazonaws.com:8015/securities/{ticker}/update_security_price')

    if response.status_code!=200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])
    else:
        return response.json()

@app.delete("/api/composite/delete_security/{ticker}")
async def delete_stock(ticker:str):
    response = requests.delete(f'http://ec2-18-222-118-35.us-east-2.compute.amazonaws.com:8015/securities/{ticker}/delete_security')

    if response.status_code!=200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])
    else:
        return response.json()
    
@app.post("/api/composite/add_security/{ticker}")
async def add_stock(ticker:str, current_price: float = 0):
    current_price = round(current_price, 2)
    response = requests.post(f'http://ec2-18-222-118-35.us-east-2.compute.amazonaws.com:8015/securities/{ticker}/add_security?current_price=' + str(current_price))

    if response.status_code!=200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])
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
@app.put("/api/composite/update_member/{member_id}", response_model=Member)
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
@app.get("/api/composite/member_id/{member_id}", response_model=Member)
async def update_stock_price(member_id: int):
    response = requests.get(f'http://members-docker-env.eba-wdqjeu7i.us-east-2.elasticbeanstalk.com/members/id/{member_id}/')
    print(response)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['error'])
    else:
        return response.json()

## GET will return a member json when looking up the DB by member_name
@app.get("/api/composite/member_name/{member_name}", response_model=Member)
async def update_stock_price(member_name: str):
    response = requests.get(f'http://members-docker-env.eba-wdqjeu7i.us-east-2.elasticbeanstalk.com/members/member_name/{member_name}/')
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['error'])
    else:
        return response.json()

## GET will return a list of members
@app.get("/api/composite/all_members/", response_model=List[Member])
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
@app.get("/api/composite/search_members/", response_model=List[Member])
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
