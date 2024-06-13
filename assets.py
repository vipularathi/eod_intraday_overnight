import pandas as pd
import numpy as np
import datetime
import mibian
import os
import glob
from common import root_dir, logger
import re
import datetime

def ceiling_xcl(x, y):
    if y == 0:
        raise ValueError("The divisor 'y' cannot be zero.")
    remainder = x % y
    if remainder == 0:
        return int(x)
    else:
        return int(x + (y - remainder))

def get_greeks(list_for_greeks, opt_type, int_rate=0, annual_div=0):
    underlying_price = list_for_greeks[0]
    strike = list_for_greeks[1]
    exp = list_for_greeks[2]
    #     exp = days_left
    if opt_type == 'CE':
        call_price = list_for_greeks[3]
        try:
            calc = mibian.Me([underlying_price, strike, int_rate, annual_div, exp], callPrice=call_price)
            IV = calc.impliedVolatility
            c = mibian.Me([underlying_price, strike, int_rate, annual_div, exp], volatility=IV)
            #         return pd.concat([new_col], row)
            print(f'\n call {underlying_price}, {strike}, {exp}, {call_price}, {IV}')
            return IV, c.callDelta, c.gamma, c.callTheta, c.vega
        except Exception as e:
            print(f"Error calculating greeks for CE: {e}")
            return np.nan, np.nan, np.nan, np.nan
    if opt_type == 'PE':
        put_price = list_for_greeks[4]
        try:
            calc = mibian.Me([underlying_price, strike, int_rate, annual_div, exp], putPrice=put_price)
            IV = calc.impliedVolatility
            c = mibian.Me([underlying_price, strike, int_rate, annual_div, exp], volatility=IV)
            print(f'\n put {underlying_price}, {strike}, {exp}, {put_price}, {IV}')
            return IV, c.putDelta, c.gamma, c.putTheta, c.vega
        except Exception as e:
            print(f"Error calculating greeks for PE: {e}")
            return np.nan, np.nan, np.nan, np.nan

def calc_business_days(today_date, exp_date):
    holidays_23 = ['2023-01-26', '2023-03-07', '2023-03-30', '2023-04-04', '2023-04-07', '2023-04-14', '2023-05-01',
                   '2023-06-29', '2023-08-15', '2023-09-19', '2023-10-02', '2023-10-24', '2023-11-14', '2023-11-27',
                   '2023-12-25']
    holidays_24 = ['2024-01-22', '2024-01-26', '2024-03-08', '2024-03-25', '2024-03-29', '2024-04-11', '2024-04-17',
                   '2024-05-01', '2024-05-20', '2024-06-17', '2024-07-17', '2024-08-15', '2024-10-02', '2024-11-01',
                   '2024-11-15', '2024-12-25']
    holidays = holidays_23 + holidays_24

    holidays = pd.to_datetime(holidays)  # Convert string dates to datetime objects
    excluded_dates = ['2024-01-20', '2024-03-02', '2024-05-04', '2024-05-18', '2024-06-01', '2024-07-06', '2024-08-03',
                      '2024-09-14', '2024-10-05', '2024-11-09', '2024-12-07']
    excluded_dates = pd.to_datetime(excluded_dates)
    holidays = holidays[~holidays.isin(excluded_dates)]  # Remove the excluded dates from the holidays list

    exp_date = pd.to_datetime(exp_date)
    today_date = pd.to_datetime(today_date)

    business_days_left = pd.bdate_range(start=today_date, end=exp_date, holidays=holidays, freq='C', weekmask='1111100')
    actual_bus_days = len(business_days_left) - 1
    return actual_bus_days

def sumproduct(df_fut, chk_row_list, col1, col2):
    sumproduct = 0
    for chk_index in chk_row_list:
        sumproduct += df_fut.loc[chk_index, col1] * df_fut.loc[chk_index, col2]
    return sumproduct

# Function to extract data from ticker
def extract_ticker_info(ticker):
    # Regular expression to capture the different parts of the ticker
    pattern = r'([A-Z]+)(\d{2})([A-Z]{3})(\d{2})(\d{4,5})([A-Z]+)\.NFO'
    match = re.match(pattern, ticker)

    if match:
        symbol, day, month, year, strike, opttype = match.groups()
        expiry = f"{day}-{month.capitalize()}-{year}"
        #         print(symbol, expiry, strike, opttype)
        return symbol, expiry, strike, opttype
    elif 'FUT' in ticker:
        pattern = r'([A-Z]+)(\d{2})([A-Z]{3})(\d{2})FUT\.NFO'
        match = re.match(pattern, ticker)
        if match:
            symbol, day, month, year = match.groups()
            expiry = f"{day}-{month.capitalize()}-{year}"
            return symbol, expiry, None, 'XX'

def change_format():
    filename = glob.glob(f'GFD*')[0]
    filepath = os.path.join(root_dir, filename)
    df = pd.read_csv(filepath, index_col=False)
    df[['Symbol', 'Expiry', 'Strike', 'Opttype']] = df['Ticker'].apply(lambda row: pd.Series(extract_ticker_info(row)))
    new_df = df[df['Time'] != '15:30:59']
    data_file_path = os.path.join(root_dir, f'Data_NSEFO_{datetime.datetime.now().date()}')
    new_df.to_csv(filepath, index=False)
    logger.info('GFD file format changed to Data_NSEFO')
    return True

# today_date = datetime.datetime.strptime('05-jun-24', '%d-%b-%y').date()
# exp_time = datetime.datetime.strptime('12-jun-24', '%d-%b-%y').date()
# bus = calc_business_days(today_date, exp_time)
# print(bus)