import pandas as pd
import numpy as np
import datetime
import mibian
import os
import glob

from assets import ceiling_xcl, get_greeks, calc_business_days
from common import root_dir, logs_dir, logger

# def ceiling_xcl(x, y):
#     if y == 0:
#         raise ValueError("The divisor 'y' cannot be zero.")
#     remainder = x % y
#     if remainder == 0:
#         return int(x)
#     else:
#         return int(x + (y - remainder))

def get_ce_pe_price(row_index, opt_type):
    # ce_ticker = row['CE']
    if opt_type == 'CE':
        ticker = df_fut.loc[row_index, 'ce']
    if opt_type == 'PE':
        ticker = df_fut.loc[row_index, 'pe']
    time = df_fut.loc[row_index, 'time']
    price = df.loc[(df['Ticker'] == ticker) & (df['Time'] == time), 'Close'].values[0]
    return price

def sumproduct(chk_row_list, col1, col2):
    sumproduct = 0
    for chk_index in chk_row_list:
        sumproduct += df_fut.loc[chk_index, col1] * df_fut.loc[chk_index, col2]
    return sumproduct

# def get_greeks(list_for_greeks, opt_type, int_rate=0, annual_div=0):
#     underlying_price = list_for_greeks[0]
#     strike = list_for_greeks[1]
#     exp = list_for_greeks[2]
#     #     exp = days_left
#     if opt_type == 'CE':
#         call_price = list_for_greeks[3]
#         try:
#             calc = mibian.Me([underlying_price, strike, int_rate, annual_div, exp], callPrice=call_price)
#             IV = calc.impliedVolatility
#             c = mibian.Me([underlying_price, strike, int_rate, annual_div, exp], volatility=IV)
#             #         return pd.concat([new_col], row)
#             print(f'\n call {underlying_price}, {strike}, {exp}, {call_price}, {IV}')
#             return IV, c.callDelta, c.gamma, c.callTheta, c.vega
#         except Exception as e:
#             print(f"Error calculating greeks for CE: {e}")
#             return np.nan, np.nan, np.nan, np.nan
#     if opt_type == 'PE':
#         put_price = list_for_greeks[4]
#         try:
#             calc = mibian.Me([underlying_price, strike, int_rate, annual_div, exp], putPrice=put_price)
#             IV = calc.impliedVolatility
#             c = mibian.Me([underlying_price, strike, int_rate, annual_div, exp], volatility=IV)
#             print(f'\n put {underlying_price}, {strike}, {exp}, {put_price}, {IV}')
#             return IV, c.putDelta, c.gamma, c.putTheta, c.vega
#         except Exception as e:
#             print(f"Error calculating greeks for PE: {e}")
#             return np.nan, np.nan, np.nan, np.nan
#
# def calc_business_days(today_date, exp_date):
#     holidays_23 = ['2023-01-26', '2023-03-07', '2023-03-30', '2023-04-04', '2023-04-07', '2023-04-14', '2023-05-01',
#                    '2023-06-29', '2023-08-15', '2023-09-19', '2023-10-02', '2023-10-24', '2023-11-14', '2023-11-27',
#                    '2023-12-25']
#     holidays_24 = ['2024-01-22', '2024-01-26', '2024-03-08', '2024-03-25', '2024-03-29', '2024-04-11', '2024-04-17',
#                    '2024-05-01', '2024-05-20', '2024-06-17', '2024-07-17', '2024-08-15', '2024-10-02', '2024-11-01',
#                    '2024-11-15', '2024-12-25']
#     holidays = holidays_23 + holidays_24
#
#     holidays = pd.to_datetime(holidays)  # Convert string dates to datetime objects
#     excluded_dates = ['2024-01-20', '2024-03-02', '2024-05-04', '2024-05-18', '2024-06-01', '2024-07-06', '2024-08-03',
#                       '2024-09-14', '2024-10-05', '2024-11-09', '2024-12-07']
#     excluded_dates = pd.to_datetime(excluded_dates)
#     holidays = holidays[~holidays.isin(excluded_dates)]  # Remove the excluded dates from the holidays list
#
#     exp_date = pd.to_datetime(exp_date)
#     today_date = pd.to_datetime(today_date)
#
#     business_days_left = pd.bdate_range(start=today_date, end=exp_date, holidays=holidays, freq='C', weekmask='1111100')
#     actual_bus_days = len(business_days_left) - 1
#     return actual_bus_days

ticker, sym_list, exp_list = [], [], []
df_fut = pd.DataFrame()

# root_dir = os.path.dirname(os.path.abspath(__file__))
filename = glob.glob(f'Data*')
csv_file = os.path.join(root_dir, filename[0])

# df = pd.read_csv(r"C:\Users\vipul\Documents\AR\for_eod\eod_data\Data_NSEFO_2024_05_28_15_32_06.csv", index_col = False)
df = pd.read_csv(csv_file, index_col=False)
# gh = df
#----------------------------------------------------------------
#taking use i/p
# sym_ip = str(input('Enter the name of symbol to use'))
# sym_list.append(sym_ip)
# exp_ip = str(input('Enter the expiry to the symbol'))
# exp_list.append(sym_ip)
# try:
#     if len(sym_list) == len(exp_list):

# sym_list = ['BANKNIFTY', 'NIFTY', 'MIDCPNIFTY', 'FINNIFTY'] #take user's i/p
# exp_list = ['29-May-24', '30-May-24', '', ''] #take user's i/p

sym_list = ['BANKNIFTY']
exp_list = ['12-Jun-24']
#----------------------------------------------------------------
multiple = {
        'BANKNIFTY': {'fstrike': 100, 'round_off':100, 'delta': 15},
        'NIFTY': {'fstrike':100, 'round_off': 50, 'delta': 25},
        'FINNIFTY': {'fstrike':50, 'round_off': 50, 'delta': 40},
        'MIDCPNIFTY': {'fstrike':50, 'round_off': 25, 'delta': 75}
}
chk = True
#implement check for sym list and exp_list

prev_day_data = {'use_strike': 23000, 'strd_price': 253.7, 'strd_theta': 4424051.16}

for i in range(len(sym_list)):
    sym = sym_list[i]
    exp = exp_list[i]
    # ---------------------------------------------------------------
    df_fut['time'] = df.loc[
        (df['Symbol'] == sym) & (df['Expiry'] == exp) & (df['Opttype'] == 'XX'), 'Time']
    df_fut.reset_index()
    # ----------------------------------------------------------------
    df_fut['minute_elapsed'] = [i + 1 for i in range(375)]
    # ----------------------------------------------------------------
    df_fut['fut'] = df.loc[
        (df['Symbol'] == sym) & (df['Expiry'] == exp) & (df['Opttype'] == 'XX'), 'Close'].values
    # ----------------------------------------------------------------
    row_index = df_fut.loc[df_fut['time'] == '09:15:59'].index[0]
    starting_index = row_index
    # ----------------------------------------------------------------
    f_strike = df_fut.loc[row_index, 'fut']
    f_multiple = float(multiple[sym]['fstrike'])
    fut_strike = int(f_multiple * round(f_strike // f_multiple))
    df_fut['fstrike'] = fut_strike
    # ----------------------------------------------------------------
    #     BANKNIFTY29MAY2449400CE.NFO
    type_list = ['CE', 'PE']
    for each in type_list:
        ticker.append((sym + pd.to_datetime(exp).strftime('%d%b%y') + str(
            df_fut['fstrike']) + each + '.NFO').upper())

    df_fut[ticker[0]] = df.loc[
        (df['Symbol'] == sym) & (df['Expiry'] == exp) & (df['Opttype'] == 'CE') & (
                    df['Strike'] == fut_strike), 'Close'].values
    df_fut[ticker[1]] = df.loc[
        (df['Symbol'] == sym) & (df['Expiry'] == exp) & (df['Opttype'] == 'PE') & (
                    df['Strike'] == fut_strike), 'Close'].values
    # ----------------------------------------------------------------
    df_fut['forward'] = df_fut['fstrike'] + df_fut[ticker[0]] - df_fut[ticker[1]]
    # ----------------------------------------------------------------
    df_fut['round_off'] = df_fut['forward'].apply(lambda x: ceiling_xcl(x, multiple[sym]['round_off']))  # this will have all the strikes
    # ----------------------------------------------------------------
    df_fut['straddle_qty'] = -50000
    # ----------------------------------------------------------------
    chk = True
    chk_row_list = []
    for j in range(375):
        # ----------------------------------------------------------------
        if chk:
            chk_row_list.append(row_index)
            df_fut.loc[row_index, 'use_strike'] = df_fut.loc[row_index, 'round_off']
        if row_index == starting_index:
            df_fut.loc[row_index,'use_strike'] = prev_day_data['use_strike']
        # ----------------------------------------------------------------
        chk_index = chk_row_list[-1]
        # ----------------------------------------------------------------
        df_fut.loc[row_index, 'ce'] = str(sym + pd.to_datetime(exp).strftime('%d%b%y') + str(round(
            df_fut.loc[chk_index, 'use_strike'])) + 'CE.NFO').upper()
        # fg = (sym + pd.to_datetime(exp).strftime('%d%b%y') + str(round(
        #     df_fut.loc[chk_index, 'use_strike'])) + 'CE.NFO').upper()
        df_fut.loc[row_index, 'ce_price'] = get_ce_pe_price(row_index, opt_type='CE')
        # ----------------------------------------------------------------
        df_fut.loc[row_index, 'pe'] = (sym + pd.to_datetime(exp).strftime('%d%b%y') + str(
            round(df_fut.loc[chk_index, 'use_strike'])) + 'PE.NFO').upper()
        df_fut.loc[row_index, 'pe_price'] = get_ce_pe_price(row_index, opt_type='PE')
        # ----------------------------------------------------------------
        df_fut.loc[row_index, 'straddle_price'] = df_fut.loc[row_index, 'ce_price'] + df_fut.loc[row_index, 'pe_price']
        # ----------------------------------------------------------------
        now = datetime.datetime.now()
        #         today_date = now.date() #use this
        today_date = datetime.datetime.strptime('28-may-24', '%d-%b-%y').date()  # fixing 28 may for now
        exp_date = datetime.datetime.strptime(exp, '%d-%b-%y').date()
        business_days_left = calc_business_days(today_date, exp_date)
        df_fut.loc[row_index, 'TTE'] = (business_days_left + (1 - (df_fut.loc[row_index, 'minute_elapsed']) / 375))
        # ----------------------------------------------------------------
        # calculating option greeks
        start_time = datetime.datetime.now()
        list_for_greeks = [df_fut.loc[row_index, 'forward'], df_fut.loc[chk_row_list[-1], 'use_strike'],
                           df_fut.loc[row_index, 'TTE'], df_fut.loc[row_index, 'ce_price'],
                           df_fut.loc[row_index, 'pe_price']]
        df_fut.loc[row_index, 'ce_iv'], df_fut.loc[row_index, 'ce_delta'], df_fut.loc[row_index, 'ce_gamma'], \
        df_fut.loc[row_index, 'ce_theta'], df_fut.loc[row_index, 'ce_vega'] = get_greeks(list_for_greeks, opt_type='CE')
        # ----------------------------------------------------------------
        df_fut.loc[row_index, 'pe_iv'], df_fut.loc[row_index, 'pe_delta'], df_fut.loc[row_index, 'pe_gamma'], \
        df_fut.loc[row_index, 'pe_theta'], df_fut.loc[row_index, 'pe_vega'] = get_greeks(list_for_greeks, opt_type='PE')
        #------------------------------------------------------------------------------------------
        straddle_delta_calc = df_fut.loc[row_index, 'straddle_qty'] * (df_fut.loc[row_index, 'ce_delta'] + df_fut.loc[row_index, 'pe_delta'])
        if row_index == starting_index:
            df_fut.loc[row_index, 'strd_delta'] = straddle_delta_calc
        else:
            df_fut.loc[row_index,'strd_delta'] = straddle_delta_calc + df_fut.loc[row_index - 1,'net_fut']
        # sum_delta_trade = 0
        # if chk == True:
        #     if len(chk_row_list)>1:
        #         if row_index == (chk_row_list[-2] + 1):
        #             for index in chk_row_list[:-2]:
        #                 sum_delta_trade += df_fut.loc[index, 'delta_trade']
        #             df_fut.loc[row_index, 'strd_delta'] = straddle_delta_calc + sum_delta_trade
        #     for index in chk_row_list[:-1]:
        #         sum_delta_trade += df_fut.loc[index, 'delta_trade']
        #     df_fut.loc[row_index, 'strd_delta'] = straddle_delta_calc + sum_delta_trade
        # else:
        #     for index in chk_row_list:
        #         sum_delta_trade += df_fut.loc[index, 'delta_trade']
        #     df_fut.loc[row_index, 'strd_delta'] = straddle_delta_calc + sum_delta_trade

        # ------------------------------------------------------------------------------------------
        df_fut.loc[row_index, 'strd_gamma'] = ((df_fut.loc[row_index, 'straddle_qty'] * df_fut.loc[row_index, 'ce_gamma']) + (
                    df_fut.loc[row_index, 'straddle_qty'] * df_fut.loc[row_index, 'pe_gamma']))
        df_fut.loc[row_index, 'strd_theta'] = ((df_fut.loc[row_index, 'straddle_qty'] * df_fut.loc[row_index, 'ce_theta']) + (
                    df_fut.loc[row_index, 'straddle_qty'] * df_fut.loc[row_index, 'pe_theta']))
        df_fut.loc[row_index, 'strd_vega'] = ((df_fut.loc[row_index, 'straddle_qty'] * df_fut.loc[row_index, 'ce_vega']) + (
                    df_fut.loc[row_index, 'straddle_qty'] * df_fut.loc[row_index, 'pe_vega']))
        # ----------------------------------------------------------------
        #         if chk:
        #             df_fut.loc[row_index, 'hedge_pt'] = np.sqrt(df_fut.loc[row_index, 'theta'] / (2 * abs(df_fut.loc[row_index, 'gamma'])))

        df_fut.loc[row_index, 'hedge_pt'] = (np.sqrt(
            df_fut.loc[chk_row_list[0], 'strd_theta'] / (2 * abs(df_fut.loc[chk_row_list[0], 'strd_gamma']))))
        # ----------------------------------------------------------------
        df_fut.loc[row_index, 'D/G'] = (df_fut.loc[row_index, 'strd_delta'] / df_fut.loc[row_index, 'strd_gamma'])
        # ----------------------------------------------------------------
        condition = abs(df_fut.loc[row_index, 'D/G']) > abs(df_fut.loc[row_index, 'hedge_pt'])
        if condition:
            df_fut.loc[row_index, 'check'] = 'CHK'
        else:
            df_fut.loc[row_index, 'check'] = ''
        # ----------------------------------------------------------------
        # if (row_index == starting_index) or (str(df_fut.loc[row_index-1, 'check']) == 'CHK'):
        #     df_fut.loc[row_index, 'option_pnl'] = 0
        # else:
        #     df_fut.loc[row_index, 'option_pnl'] = df_fut.loc[row_index, 'straddle_qty'] * (
        #             df_fut.loc[row_index, 'straddle_price'] - df_fut.loc[row_index - 1, 'straddle_price'])
        if (row_index == starting_index):
            df_fut.loc[row_index, 'option_pnl'] = round((df_fut.loc[row_index, 'straddle_qty'] * (
                        df_fut.loc[row_index,'straddle_price'] - prev_day_data['strd_price'])), 2)
        elif chk:
            df_fut.loc[row_index, 'option_pnl'] = 0
        else:
            df_fut.loc[row_index, 'option_pnl'] = round((df_fut.loc[row_index, 'straddle_qty'] * (
                        df_fut.loc[row_index,'straddle_price'] - df_fut.loc[row_index - 1,'straddle_price'])), 2)
        # ----------------------------------------------------------------
        if chk or row_index == starting_index:
            deltatrade_calc = 0
            deltatrade_calc = multiple[sym]['delta'] * round(
                df_fut.loc[row_index, 'strd_delta'] / multiple[sym]['delta'])

            if df_fut.loc[row_index, 'strd_delta'] > 0:
                use_multiple = -1
            else:
                use_multiple = 1
            df_fut.loc[row_index, 'delta_trade'] = use_multiple * abs(deltatrade_calc)
        # ----------------------------------------------------------------
        sum_delta_trade = 0
        for ri in chk_row_list:
            sum_delta_trade += df_fut.loc[ri, 'delta_trade']
        df_fut.loc[row_index, 'net_fut'] = sum_delta_trade
        # ----------------------------------------------------------------
        if (row_index == starting_index):
            df_fut.loc[row_index, 'fut_pnl'] = 0
        else:
            sp_result = sumproduct(chk_row_list, col1='delta_trade', col2='forward')
            df_fut.loc[row_index, 'fut_pnl'] = round(((df_fut.loc[row_index, 'forward'] - (sp_result/sum_delta_trade)) * df_fut.loc[row_index, 'net_fut']), 2)
        # ----------------------------------------------------------------
        x = starting_index
        y = row_index
        cum_sum = 0
        if row_index == starting_index:
            df_fut.loc[row_index, 'cum_pnl'] = 0
        else:
            while x <= y:
                cum_sum += df_fut.loc[x, 'option_pnl']
                x += 1
            df_fut.loc[row_index, 'cum_pnl'] = round((cum_sum + df_fut.loc[row_index, 'fut_pnl']), 2)
        # ----------------------------------------------------------------
        if row_index == starting_index:
            df_fut.loc[row_index, 'final_pnl'] = 0
        else:
            df_fut.loc[row_index, 'final_pnl'] = round((df_fut.loc[row_index, 'cum_pnl'] / abs(df_fut.loc[row_index, 'straddle_qty'])), 2)
        # ----------------------------------------------------------------
        if str(df_fut.loc[row_index, 'check']) == 'CHK':
            chk = True
        else:
            chk = False
        row_index += 1

    # df_fut.loc[chk_row_list[0], 'option_pnl'], df_fut.loc[chk_row_list[0], 'fut_pnl'], df_fut.loc[
    #     chk_row_list[0], 'cum_pnl'] = 0, 0, 0
    # for each in chk_row_list:
    #     df_fut.loc[each, 'option_pnl'] = 0
    df_fut.to_csv('test_intraday_try1.csv')