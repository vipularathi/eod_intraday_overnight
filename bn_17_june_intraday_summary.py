import time
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import datetime
import mibian
import os
import glob
import sqlalchemy as sql
import seaborn as sns
import matplotlib.dates as mdates
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from openpyxl.utils.dataframe import dataframe_to_rows
import io
import sys
import yfinance as yf

from bn_14_june_intraday import df_fut_copied, today_date
from bn_14_june_overnight import prev_day_data, df_fut as df_overnight

sym_list = ['NIFTY', 'FINNIFTY', 'MIDCPNIFTY']
exp_list = ['13-Jun-24', '18-Jun-24', '14-Jun-24']
tick_list = ['^NSEI', 'NIFTY_FIN_SERVICE.NS', '^NSEMDCP50']
# tick_list = ['^NSEI', '^NSEBANK', 'NIFTY_FIN_SERVICE.NS', '^NSEMDCP50']

for i in range(len(sym_list)):
    sym = sym_list[i]
    exp = exp_list[i]
    ticker = tick_list[i]

    # 1
    # today_date = datetime.datetime.now().date()
    today_date = datetime.datetime.strptime('10-jun-24', '%d-%b-%y').date()

    # 2
    exp

    # 3
    starting_index = df_fut_copied.loc[df_fut_copied['time'] == '09:15:59'].index[0]
    ending_index = df_fut_copied.loc[df_fut_copied['time'] == '15:29:59'].index[0]
    bod = df_fut_copied.loc[starting_index, 'TTE']

    # 4
    eod = df_fut_copied.loc[ending_index, 'TTE']

    # 5
    yesterday = today_date - datetime.timedelta(days=1)
    # yt_spot_close = prev_day_data[sym]['use_strike']
    df1 = yf.download(ticker, start = yesterday, end = today_date)
    if not len(df1):
        ticker_output = yf.Ticker(ticker)
        last_close = ticker_output.info['previousClose']
    else:
        last_close = df1['Close'].values[0]

    # 6
    tmrw = today_date + datetime.timedelta(days=1)
    df2 = yf.download(ticker, start = today_date, end = tmrw)
    spot_close_today = round(df2['Close'].values[0], 2)

    # 7
    overnight_theta = prev_day_data[sym]['strd_theta'] / 50000

    #8
    overnight_pnl = df_overnight.loc[ending_index, 'cum_pnl'] / 50000

    # 9
    overnight_pts = overnight_pnl * 2

    # 10
    overnight_theta_retn = cumpnl at 3:20 / overnight_theta

    # 11
    will accumulate later

    # 12
    intraday_theta = df_fut_copied.loc[starting_index, 'strd_theta'] / 50000

    # 13
    intraday_pnl = df_fut_copied.loc[ending_index, 'cum_pnl'] / 50000

    # 14
    # intraday_pts = intraday_pnl * 2
    intraday_pts = intraday_pnl

    # 15
    intraday_theta_retn = intraday_pnl / intraday_theta

    # 16
    will accumulate later

    # 17
    strd_initiation_price = df_fut_copied.loc[starting_index, 'straddle_price']

    # 18
    strd_exit_price = df_fut_copied.loc[ending_index, 'straddle_price']

    # 19
    eod_bod = df_overnight.loc[starting_index, 'cum_pnl']
    eod_bod_pts = eod_bod / 50000

    # 20
    eod_bod_intraday = eod_bod_pts + intraday_pts