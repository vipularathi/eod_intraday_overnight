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

from concurrent.futures import ProcessPoolExecutor
from functools import partial
from multiprocessing import Manager, get_context, Queue

import requests

from assets import ceiling_xcl, get_greeks, calc_business_days, sumproduct, change_format
from common import root_dir, logs_dir, logger, today_date, yesterday, tomorrow
from remote_db_ops import from_master

from assets_xts import get_fut_close_price

ticker, sym_list, exp_list = [], [], []
csv_file = None
df_fut = pd.DataFrame()
fut_val = 0
row_index_nifty, row_index_banknifty, row_index_finnifty, row_index_midcpnifty = 0,0,0,0
df_nifty, df_banknifty, df_finnifty, df_midcpnifty = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
df1 = pd.DataFrame()

def get_ce_pe_price(row_index, opt_type):
    # ce_ticker = row['CE']
    if opt_type == 'CE':
        ticker = df_fut.loc[row_index, 'ce']
    if opt_type == 'PE':
        ticker = df_fut.loc[row_index, 'pe']
    time = df_fut.loc[row_index, 'time']
    price = df.loc[(df['Ticker'] == ticker) & (df['Time'] == time), 'Close'].values[0]
    return price

#----------------------------------------------------------------
#take user's i/p
# sym_list = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']
# exp_list = ['20-Jun-24', '19-Jun-24', '18-Jun-24', '14-Jun-24']
sym_list = ['NIFTY']
exp_list = ['20-Jun-24']
#----------------------------------------------------------------
multiple = {
        'BANKNIFTY': {'fstrike': 100, 'round_off':100, 'delta': 15},
        'NIFTY': {'fstrike':100, 'round_off': 50, 'delta': 25},
        'FINNIFTY': {'fstrike':50, 'round_off': 50, 'delta': 40},
        'MIDCPNIFTY': {'fstrike':50, 'round_off': 25, 'delta': 75}
}
#----------------------------------------------------------------
chk = True
#implement check for sym list and exp_list

start_time = datetime.strptime('09:19:59', '%H:%M:%S')
end_time = datetime.strptime('15:19:59', '%H:%M:%S')
time_range = pd.date_range(start=start_time, end=end_time, freq='T').strftime('%H:%M:%S')
min_range = [i for i in range(5,366)]
for sym in sym_list:
    dfn = f'df_{sym.lower()}'
    # df1 = pd.DataFrame(time_range, columns=['time'])
    df1['time'] = time_range
    df1['min_elapsed'] = min_range
    exec(f'{dfn} = df1.copy()')


for i in range(len(sym_list)):
    break_process = False
    df_intraday = pd.DataFrame()
    df_overnight = pd.DataFrame()
    df_summary = pd.DataFrame()
    sym = sym_list[i]
    exp = exp_list[i]
    yf_tick = tick_list[i]
    num = i

    df_fut = pd.DataFrame()
    fut_expiry = from_master(sym)
    df_fut.reset_index()
    # ----------------------------------------------------------------
    df_fut['minute_elapsed'] = [i + 1 for i in range(375)]
    val = get_fut_close_price(sym)
    df_fut['fut'] = val
    # ----------------------------------------------------------------
    if sheet == 'intraday':
        row_index = df_fut.loc[df_fut['time'] == '09:19:59'].index[0]
    else:
        row_index = df_fut.loc[df_fut['time'] == '09:15:59'].index[0]
    starting_index = row_index
    # ----------------------------------------------------------------
    f_strike = df_fut.loc[row_index, 'fut']
    f_multiple = float(multiple[sym]['fstrike'])
    fut_strike = int(f_multiple * round(f_strike // f_multiple))
    condition = True
    count = 0
    while condition:
        count += 1
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

        # check to see if the src data is faulty i.e no ce pe column of any strike has 375 rows
        if count > 375:
            print(f'Cannot create table for symbol - {sym} with expiry - {exp} as src data is faulty hence skipping to next symbol')
            break_process = True
            # sys.exit()
            break
    if break_process:
        break
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
    if sheet == 'intraday':
        range_till = 361
    else:
        range_till = 365
    for j in range(range_till):
        # ----------------------------------------------------------------
        if sheet == 'intraday':
            if chk:
                chk_row_list.append(row_index)
                df_fut.loc[row_index, 'use_strike'] = df_fut.loc[row_index, 'round_off']
        else:
            if chk:
                chk_row_list.append(row_index)
                df_fut.loc[row_index, 'use_strike'] = df_fut.loc[row_index, 'round_off']
            if row_index == starting_index:
                df_fut.loc[row_index, 'use_strike'] = prev_day_data[num][sym]['use_strike']
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
          # fixing 05-jun for testing
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
        if sheet == 'overnight':
            if row_index == starting_index:
                df_fut.loc[row_index, 'check'] = ''
        # ----------------------------------------------------------------
        # if (row_index == starting_index) or (str(df_fut.loc[row_index-1, 'check']) == 'CHK'):
        #     df_fut.loc[row_index, 'option_pnl'] = 0
        # else:
        #     df_fut.loc[row_index, 'option_pnl'] = df_fut.loc[row_index, 'straddle_qty'] * (
        #             df_fut.loc[row_index, 'straddle_price'] - df_fut.loc[row_index - 1, 'straddle_price'])
        if sheet == 'intraday':
            if (row_index == starting_index) or chk:
                    df_fut.loc[row_index, 'option_pnl'] = 0
            else:
                df_fut.loc[row_index, 'option_pnl'] = round((df_fut.loc[row_index, 'straddle_qty'] * (
                            df_fut.loc[row_index,'straddle_price'] - df_fut.loc[row_index - 1,'straddle_price'])), 2)
        else:
            if (row_index == starting_index):
                df_fut.loc[row_index, 'option_pnl'] = round((df_fut.loc[row_index, 'straddle_qty'] * (
                        df_fut.loc[row_index, 'straddle_price'] - prev_day_data[num][sym]['strd_price'])), 2)
            elif chk:
                df_fut.loc[row_index, 'option_pnl'] = 0
            else:
                df_fut.loc[row_index, 'option_pnl'] = round((df_fut.loc[row_index, 'straddle_qty'] * (
                        df_fut.loc[row_index, 'straddle_price'] - df_fut.loc[row_index - 1, 'straddle_price'])), 2)
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

        if (row_index == starting_index):
            df_fut.loc[row_index, 'fut_pnl'] = 0
        else:
            # df_fut.loc[row_index, 'fut_pnl'] = (df_fut.loc[row_index, 'forward'] - (a / b)) * b
            # df_fut.loc[row_index, 'cum_pnl'] = df_fut['option_pnl'].sum() + df_fut.loc[row_index, 'fut_pnl']
            sp_result = sumproduct(df_fut, chk_row_list, col1='delta_trade', col2='forward')
            df_fut.loc[row_index, 'fut_pnl'] = ((df_fut.loc[row_index, 'forward'] - (sp_result/sum_delta_trade)) * df_fut.loc[row_index, 'net_fut'])
        # ----------------------------------------------------------------
        x = starting_index
        y = row_index
        cum_sum = 0
        if sheet == 'intraday':
            while x <= y:
                cum_sum += df_fut.loc[x, 'option_pnl']
                x += 1
            df_fut.loc[row_index, 'cum_pnl'] = (cum_sum + df_fut.loc[row_index, 'fut_pnl'])
        else:
            if row_index == starting_index:
                df_fut.loc[row_index, 'cum_pnl'] = 0
            else:
                while x <= y:
                    cum_sum += df_fut.loc[x, 'option_pnl']
                    x += 1
                df_fut.loc[row_index, 'cum_pnl'] = (cum_sum + df_fut.loc[row_index, 'fut_pnl'])
        # ----------------------------------------------------------------
        if sheet == 'intraday':
            df_fut.loc[row_index, 'final_pnl'] = (df_fut.loc[row_index, 'cum_pnl'] / abs(df_fut.loc[row_index, 'straddle_qty']))
        else:
            if row_index == starting_index:
                df_fut.loc[row_index, 'final_pnl'] = 0
            else:
                df_fut.loc[row_index, 'final_pnl'] = (
                            df_fut.loc[row_index, 'cum_pnl'] / abs(df_fut.loc[row_index, 'straddle_qty']))
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
    #
    # def save_to_sheet(df, sheet_name, wb):
    #     ws = wb.create_sheet(title = sheet_name)
    #     for each_line in dataframe_to_rows(df, index = False, header = True):
    #         ws.append(each_line)
    #
    #     stt = '09:19:59'
    #     ett = '15:19:59'
    #     filtered_df = df_fut[(df_fut['time'] >= stt) & (df_fut['time'] <= ett)]
    #
    #     sns.set(style='whitegrid')
    #     sns.set_context('talk')
    #
    #     # fig, ax1 = plt.subplot(figsize=(12,6))
    #     fig, ax1 = plt.subplots(figsize=(15, 7.5))
    #
    #     sns.lineplot(x='time', y='final_pnl', data=filtered_df, ax=ax1, color='blue', label='Final PnL')
    #     ax1.set_ylabel('Final PnL', color='blue', fontsize=5)
    #     ax1.tick_params(axis='y', labelcolor='blue')
    #
    #     ax2 = ax1.twinx()
    #
    #     sns.lineplot(x='time', y='forward', data=filtered_df, ax=ax2, color='orange', label='Forward')
    #     ax2.set_ylabel('Forward', color='orange', fontsize=5)
    #     ax2.tick_params(axis='y', labelcolor='orange')
    #
    #     ax1.axhline(0, color='black', linewidth=1, linestyle='--')
    #
    #     plt.title(f'{sym} Straddle ({exp})')
    #     ax1.set_xlabel('Time', fontsize=5)
    #
    #     time_interval = 15
    #     # time_labels = [f'{i * time_interval // 60}:{(i * time_interval) % 60}' for i in range(int(375/time_interval))]
    #     time_labels = df_fut['time'].iloc[::time_interval].tolist()
    #     ax1.set_xticks(range(0, len(filtered_df['time']), time_interval))
    #     ax1.set_xticklabels(time_labels, fontsize=8)
    #
    #     plt.setp(ax1.xaxis.get_majorticklabels(), rotation=90, ha='right')
    #     ax1.grid(False)
    #
    #     ax1.tick_params(axis='x', labelsize=8)
    #     by_buffer = io.BytesIO()
    #     plt.savefig(by_buffer, format='png')
    #     plt.close()
    #
    #     img = Image(by_buffer)
    #     img.anchor = 'A1'
    #     ws.add_image(img)

    df_fut = df_fut.round(decimals=3)
    # df_fut_copied = df_fut.copy()
    if sheet == 'intraday':
        df_intraday= df_fut.copy()
    else:
        df_overnight = df_fut.copy()
# ----------------------------------------------------------------------------------------------
    int_starting_index = df_intraday.loc[df_intraday['time'] == '09:19:59'].index[0]
    int_ending_index = df_intraday.loc[df_intraday['time'] == '15:19:59'].index[0]

    ov_starting_index = df_overnight.loc[df_overnight['time'] == '09:19:59'].index[0]
    ov_ending_index = df_overnight.loc[df_overnight['time'] == '15:19:59'].index[0]

    bod = round(df_intraday.loc[int_starting_index, 'TTE'])
    # df_summary['BoD'] = bod
    # df_summary['EoD'] = bod-1
    df1 = yf.download(yf_tick, start=yesterday, end=today_date)
    df2 = yf.download(yf_tick, start=today_date, end=tomorrow)
    # df_summary['Spot_Close_Yesterday'] = round(df1['Close'].values[0], 2)
    # df_summary['Spot_Close_Today'] = round(df2['Close'].values[0], 2)

    overnight_pts = df_overnight.loc[ov_ending_index, 'final_pnl']
    # df_summary['Overnight_Pts'] = overnight_pts
    # df_summary['Overnight_theta_retn'] = overnight_pts / (prev_day_data[num][sym]['strd_theta'] / 50000)

    intraday_pts = df_intraday.loc[int_ending_index, 'final_pnl']
    # df_summary['Intraday_Pts'] = intraday_pts
    # df_summary['Intraday_theta_retn'] = intraday_pts / (df_intraday.loc[starting_index, 'strd_theta'] / 50000)
    # df_summary['Strd_Initiation_price'] = df_intraday.loc[starting_index, 'straddle_price']
    # df_summary['Strd_Exit_price'] = df_intraday.loc[ending_index, 'straddle_price']
    eod_bod = df_overnight.loc[ov_ending_index, 'final_pnl']

    summary_data = {
        'Today': [today_date],
        'Expiry': [exp],
        'BoD': [bod],
        'EoD': [bod - 1],
        'Spot_Close_Yesterday': [round(df1['Close'].values[0], 2)],
        'Spot_Close_Today': [round(df2['Close'].values[0], 2)],
        'Overnight_Pts': [overnight_pts],
        'Overnight_theta_retn': [overnight_pts / (prev_day_data[num][sym]['strd_theta'] / 50000)],
        'Intraday_Pts': [intraday_pts],
        'Intraday_theta_retn': [intraday_pts / (df_intraday.loc[int_starting_index, 'strd_theta'] / 50000)],
        'Strd_Initiation_price': [df_intraday.loc[int_starting_index, 'straddle_price']],
        'Strd_Exit_price': [df_intraday.loc[int_ending_index, 'straddle_price']],
        'EoD-BoD PnL': [eod_bod],
        'EoD-BoD+Intraday': [intraday_pts + eod_bod]
    }
    df_summary = df_summary.from_dict(summary_data, orient='columns')

    wb = Workbook()
    wb.remove(wb.active)
    save_to_sheet(df_intraday, 'Intraday', wb)
    save_to_sheet(df_overnight, 'Overnight', wb)
    save_to_sheet(df_summary, 'Summary', wb)
    filename = f'test_intraday_overnight_with_chart_{sym}_{today_date}.xlsx'
    wb.save(filename)
    print(f'Excel file created for {sym} - {today_date}')
    df_fut = df_fut.empty