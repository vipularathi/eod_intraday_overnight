import time

import pandas as pd
import numpy as np
import datetime
import mibian
import os
import glob
import sqlalchemy as sql

from assets import ceiling_xcl, get_greeks, calc_business_days
from common import root_dir, logs_dir, logger
from remote_db_ops import from_master

def get_ce_pe_price(row_index, opt_type):
    # ce_ticker = row['CE']
    if opt_type == 'CE':
        ticker = df_fut.loc[row_index, 'ce']
    if opt_type == 'PE':
        ticker = df_fut.loc[row_index, 'pe']
    time = df_fut.loc[row_index, 'time']
    price = df.loc[(df['Ticker'] == ticker) & (df['Time'] == time), 'Close'].values[0]
    return price

ticker, sym_list, exp_list = [], [], []

# root_dir = os.path.dirname(os.path.abspath(__file__))
filename = glob.glob(f'Data*')
csv_file = os.path.join(root_dir, filename[0])

# df = pd.read_csv(r"C:\Users\vipul\Documents\AR\for_eod\eod_data\Data_NSEFO_2024_05_28_15_32_06.csv", index_col = False)
df = pd.read_csv(csv_file, index_col=False)
# gh = df
#----------------------------------------------------------------

#take user's i/p
sym_list = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
exp_list = ['13-Jun-24', '12-Jun-24', '11-Jun-24']
#----------------------------------------------------------------
multiple = {
        'BANKNIFTY': {'fstrike': 100, 'round_off':100, 'delta': 15},
        'NIFTY': {'fstrike':100, 'round_off': 50, 'delta': 25},
        'FINNIFTY': {'fstrike':50, 'round_off': 50, 'delta': 40},
        'MIDCPNIFTY': {'fstrike':50, 'round_off': 25, 'delta': 75}
}
chk = True
#implement check for sym list and exp_list

for i in range(len(sym_list)):
    df_fut = pd.DataFrame()
    sym = sym_list[i]
    exp = exp_list[i]
    # ---------------------------------------------------------------
    # get monthly expiry of sym = future expiry
    fut_expiry = from_master(sym)
    # ---------------------------------------------------------------
    length_count = len(df.loc[
        (df['Symbol'] == sym) & (df['Expiry'] == fut_expiry) & (df['Opttype'] == 'XX'), 'Time'])

# ----------------------------------------------------------------------------------------------
    #to check the length of future data available so that this would not affect the creation of df of length 375
    if length_count == 375:
        df_fut['time'] = df.loc[
            (df['Symbol'] == sym) & (df['Expiry'] == fut_expiry) & (df['Opttype'] == 'XX'), 'Time']
    else:
        ffstrike_loc = df[(df['Symbol'] == sym) & (df['Expiry'] == exp) & (df['Opttype'] == 'CE') & (df['Time'] == '09:19:59')]
        ffstrike_value = int(ffstrike_loc['Strike'].mean())
        f_multiple = float(multiple[sym]['fstrike'])
        ffstrike_value_calc = int(f_multiple * round(ffstrike_value // f_multiple))
        df_fut['time'] = df.loc[
            (df['Symbol'] == sym) & (df['Expiry'] == exp) & (df['Opttype'] == 'CE') & (df['Strike'] == ffstrike_value_calc), 'Time']

# ----------------------------------------------------------------------------------------------
    df_fut.reset_index()
    # ----------------------------------------------------------------
    df_fut['minute_elapsed'] = [i + 1 for i in range(375)]
    # ----------------------------------------------------------------
    val = df.loc[
        (df['Symbol'] == sym) & (df['Expiry'] == fut_expiry) & (df['Opttype'] == 'XX') & (
                    df['Time'] == '09:19:59'), 'Close'].values[0]
    df_fut['fut'] = val
    # ----------------------------------------------------------------
    row_index = df_fut.loc[df_fut['time'] == '09:19:59'].index[0]
    starting_index = row_index
    # ----------------------------------------------------------------
    f_strike = df_fut.loc[row_index, 'fut']
    f_multiple = float(multiple[sym]['fstrike'])
    fut_strike = int(f_multiple * round(f_strike // f_multiple))

# ----------------------------------------------------------------------------------------------
    #checking if the length of the CE and PE is same or not, cause if not then the df_fut would not be made
    condition = True
    while condition:
        check_df1 = df.loc[
            (df['Symbol'] == sym) & (df['Expiry'] == exp) & (df['Opttype'] == 'CE') & (
                        df['Strike'] == fut_strike), 'Close'].values
        check_df2 = df.loc[
            (df['Symbol'] == sym) & (df['Expiry'] == exp) & (df['Opttype'] == 'PE') & (
                        df['Strike'] == fut_strike), 'Close'].values
        if len(check_df1) == 375 and len(check_df2) == 375:
            condition = False
        else:
            fut_strike += multiple[sym]['fstrike']
            condition = True

# ----------------------------------------------------------------------------------------------

    df_fut['fstrike'] = fut_strike
    # ----------------------------------------------------------------
    #     BANKNIFTY29MAY2449400CE.NFO
    type_list = ['CE', 'PE']
    for each in type_list:
        ticker.append((sym + pd.to_datetime(exp).strftime('%d%b%y') + str(
            fut_strike) + each + '.NFO').upper())

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
    for j in range(371):
        # ----------------------------------------------------------------
        if chk:
            chk_row_list.append(row_index)
            df_fut.loc[row_index, 'use_strike'] = df_fut.loc[row_index, 'round_off']
        # ----------------------------------------------------------------
        chk_index = chk_row_list[-1]
        # ----------------------------------------------------------------
        df_fut.loc[row_index, 'ce'] = (sym + pd.to_datetime(exp).strftime('%d%b%y') + str(round(
            df_fut.loc[chk_index, 'use_strike'])) + 'CE.NFO').upper()
        df_fut.loc[row_index, 'ce_price'] = get_ce_pe_price(row_index, opt_type='CE')
        # ----------------------------------------------------------------
        df_fut.loc[row_index, 'pe'] = (sym + pd.to_datetime(exp).strftime('%d%b%y') + str(
            round(df_fut.loc[chk_index, 'use_strike'])) + 'PE.NFO').upper()
        df_fut.loc[row_index, 'pe_price'] = get_ce_pe_price(row_index, opt_type='PE')
        # ----------------------------------------------------------------
        df_fut.loc[row_index, 'straddle_price'] = df_fut.loc[row_index, 'ce_price'] + df_fut.loc[row_index, 'pe_price']
        # ----------------------------------------------------------------
        now = datetime.datetime.now()
        today_date = now.date() #use this
        # today_date = datetime.datetime.strptime('07-jun-24', '%d-%b-%y').date()  # fixing 05-jun for testing
        exp_date = datetime.datetime.strptime(exp, '%d-%b-%y').date()
        business_days_left = calc_business_days(today_date, exp_date)
        tte = business_days_left + (1 - (df_fut.loc[row_index, 'minute_elapsed']) / 375)
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
        if (row_index == starting_index) or chk:
            df_fut.loc[row_index, 'option_pnl'] = 0
        else:
            df_fut.loc[row_index, 'option_pnl'] = round((df_fut.loc[row_index, 'straddle_qty'] * (
                        df_fut.loc[row_index,'straddle_price'] - df_fut.loc[row_index - 1,'straddle_price'])), 2)
        # ----------------------------------------------------------------
        if chk or row_index == starting_index:
            deltatrade_calc = 0
            deltatrade_calc = multiple[sym]['delta'] * round(
                df_fut.loc[row_index, 'strd_delta'] / multiple[sym]['delta'])
            we = df_fut.loc[row_index, 'strd_delta']
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
        # a, b = 0, 0
        # for i in chk_row_list:
        #     a += (df_fut.loc[i, 'delta_trade'] * df_fut.loc[i, 'forward'])
        #     b += df_fut.loc[i, 'delta_trade']

        def sumproduct(chk_row_list, col1, col2):
            sumproduct = 0
            for chk_index in chk_row_list:
                sumproduct += df_fut.loc[chk_index, col1] * df_fut.loc[chk_index, col2]
            return sumproduct

        if (row_index == starting_index):
            df_fut.loc[row_index, 'fut_pnl'] = 0
        else:
            # df_fut.loc[row_index, 'fut_pnl'] = (df_fut.loc[row_index, 'forward'] - (a / b)) * b
            # df_fut.loc[row_index, 'cum_pnl'] = df_fut['option_pnl'].sum() + df_fut.loc[row_index, 'fut_pnl']
            sp_result = sumproduct(chk_row_list, col1='delta_trade', col2='forward')
            df_fut.loc[row_index, 'fut_pnl'] = ((df_fut.loc[row_index, 'forward'] - (sp_result/sum_delta_trade)) * df_fut.loc[row_index, 'net_fut'])
        # ----------------------------------------------------------------
        x = starting_index
        y = row_index
        cum_sum = 0
        while x <= y:
            cum_sum += df_fut.loc[x, 'option_pnl']
            x += 1
        df_fut.loc[row_index, 'cum_pnl'] = (cum_sum + df_fut.loc[row_index, 'fut_pnl'])
        # ----------------------------------------------------------------
        df_fut.loc[row_index, 'final_pnl'] = (df_fut.loc[row_index, 'cum_pnl'] / abs(df_fut.loc[row_index, 'straddle_qty']))
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
    df_fut = df_fut.round(decimals=3)
    # print(f'rounded df_fut is \n {df_fut}')
    df_fut.to_csv(f'test_intraday_{sym}_{today_date}.csv')
    print(f'CSV file name for {sym} - {today_date}')
    df_fut = df_fut.empty