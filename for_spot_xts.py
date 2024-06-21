from datetime import datetime
import pandas as pd
from Connect import XTSConnect
from MarketDataSocketClient import MDSocket_io

# MarketData API Credentials
API_KEY = "e78a8d7023e841f7913809"
API_SECRET = "Egya351@Hm"
source = "WEBAPI"

# Initialise
xt = XTSConnect(API_KEY, API_SECRET, source)

# login for authorize token
response = xt.marketdata_login()

# stored the userID and Token
set_MarketDataToken = response['result']['token']
set_muserID = response['result']['userID']
# print("Login",response)
response1 = xt.get_ohlc(exchangeSegment=1,
                        exchangeInstrumentID=2885,
                        startTime="Jun 20 2024 091500",
                        endTime="Jun 20 2024 153000",
                        compressionValue=60)
print(response1)