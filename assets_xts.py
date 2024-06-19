import logging
import os
import sys
import json
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
import requests
from common import today_date
import pandas as pd
from assets import extract_ticker_info
from remote_db_ops import get_option_inst_id

user_id = 'BR052'
host = "https://algozy.rathi.com:3000"
# socket_url = f"wss://algozy.rathi.com:3000/marketdata/socket.io/"
socket_url = f"wss://algozy.rathi.com:3000"
access_token = ''
data_api_key = '9af31b94f3999bd12c6e89'
data_api_secret = 'Evas244$3H'
interactive_api_key = 'dabfe67ee2286b19a7b664'
interactive_api_secret = 'Mbqk087#Y1'

# def login():
#     url = f"{host}/apimarketdata/auth/login"
#     payload = {"appKey": data_api_key, "secretKey": data_api_secret, "source": "WebAPI"}
#     response = requests.post(url=url, json=payload)
#     logger.info(response.content)
#     data = response.json()
#     return data
#
# info = login()
# access_token = info['result']['token']


def get_expiry(sym):
    ge_url = f'{host}/apimarketdata/instruments/instrument/expiryDate'
    #     ge_header = {'authorization': access_token}
    ge_payload = {'exchangeSegment': 2, 'series': 'FUTIDX', 'symbol': sym}
    ge_response = requests.get(url=ge_url, params=ge_payload)

    if ge_response.status_code == 200:
        ge_data = ge_response.json()
        exp = pd.to_datetime(sorted(ge_data['result'])[0].split('T')[0]).date().strftime('%d%b%Y')
        return exp
    else:
        # logger.error(f'Error in getting the expiry date. Status code: {ge_response.status_code}')
        return None
def get_fut_inst_id(exchange_segment, series, symbol, expiry_date):
    url = f"{host}/apimarketdata/instruments/instrument/futureSymbol"
    params = {
        "exchangeSegment": exchange_segment,
        "series": series,
        "symbol": symbol,
        "expiryDate": expiry_date,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data_response = response.json()
        exch_id = data_response['result'][0]['ExchangeInstrumentID']
        return exch_id
    else:
        print(f'Error in fetching future symbol. Status code: {response.status_code}. Response: {response.text}')

def get_close_price(exch_id, start_time, end_time):
    url = "http://172.16.47.54:8006/make_csv_from_tbt_data"
    payload = json.dumps({
        "exchange_segment": 'NSEFO',
        "exchange_instrument_id": str(exch_id),
        "start_date": str(today_date.strftime('%b %d %Y')),
        "end_date": str(today_date.strftime('%b %d %Y')),
        "start_time": str(start_time),
        "end_time": str(end_time),
        "compression_value": "60"
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.json())
    a = response.json()
    close_price = response.json()['Close']['0']
    print('close price is', float(close_price))
    return float(close_price)
    # if 'Close' in a and isinstance(a['Close'], dict):
    #     close_price = a['Close']['0']
    #     return float(close_price)
    # else:
    #     print(f"Error: 'Close' key not found or not a dictionary in the response.")
    #     return(0)
    # print(type(text_resp), type(text_resp['Close']['0']))

def get_fut_price(sym):
    fut_exp = get_expiry(sym)
    exch_id = get_fut_inst_id(exchange_segment = 2, series = 'FUTIDX', symbol = sym, expiry_date=fut_exp)
    fut_close_920 = get_close_price(exch_id, start_time = '091859', end_time = '091959')
    return(fut_close_920)

def get_option_price(ticker, start_time, end_time):
    stt = start_time.strftime('%H%M%S')
    ett = end_time.strftime('%H%M%S')
    option_inst_id = get_option_inst_id(ticker)
    print(f'option_inst_id is {option_inst_id}')
    option_close = get_close_price(option_inst_id, start_time = stt, end_time = ett)
    return(option_close)

# futc = get_fut_price('nifty')
# print(f'future close price of nifty is {futc}')
# print(type(futc))
# start = '09:18:59'
# end = '09:19:59'
# optc= get_option_price(ticker = 'NIFTY20JUN2423450PE.NFO', start_time=start, end_time=end)
# print(f'option close price is {optc}')

# che = get_close_price('35004','091859', '091959')
# print(che)