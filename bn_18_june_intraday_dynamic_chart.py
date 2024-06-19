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
import json
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from multiprocessing import Manager, get_context, Queue
from string import Template
import requests
from matplotlib.animation import FuncAnimation

from assets import ceiling_xcl, get_greeks, calc_business_days, sumproduct, change_format
from common import root_dir, logs_dir, logger, today_date, yesterday, tomorrow
from remote_db_ops import from_master
from assets_xts import get_fut_price, get_option_price

ticker, sym_list, exp_list = [], [], []
csv_file = None
df_fut = pd.DataFrame()
fut_val = 0
row_index_nifty = row_index_banknifty = row_index_finnifty = row_index_midcpnifty = 0
starting_index_nifty = starting_index_midcpnifty = starting_index_finnifty = starting_index_banknifty = 0
df_nifty, df_banknifty, df_finnifty, df_midcpnifty = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
df1 = pd.DataFrame()
comp_time = None
chk_row_list_n = chk_row_list_bn = chk_row_list_fn = chk_row_list_mcn = []
val = stt = ett = 0

# def get_ce_pe_price(row_index, opt_type):
#     # ce_ticker = row['CE']
#     if opt_type == 'CE':
#         ticker = df_fut.loc[row_index, 'ce']
#     if opt_type == 'PE':
#         ticker = df_fut.loc[row_index, 'pe']
#     time = df_fut.loc[row_index, 'time']
#     price = df.loc[(df['Ticker'] == ticker) & (df['Time'] == time), 'Close'].values[0]
#     return price
# def plot_graph(df, symbol):
#     fig, ax1 = plt.subplots()
#
#     # Plot forward vs time on left y-axis
#     color = 'tab:orange'
#     ax1.set_xlabel('Time')
#     ax1.set_ylabel('Forward', color=color)
#     ax1.plot(df['time'], df['forward'], color=color)
#     ax1.tick_params(axis='y', labelcolor=color)
#
#     # Plot final_pnl vs time on right y-axis
#     ax2 = ax1.twinx()
#     color = 'tab:blue'
#     ax2.set_ylabel('Final PNL', color=color)
#     ax2.plot(df['time'], df['final_pnl'], color=color)
#     ax2.tick_params(axis='y', labelcolor=color)
#
#     # Plot use_strike points
#     ax1.scatter(df['time'], df['use_strike'], color='lightgray')
#     for i, txt in enumerate(df['use_strike']):
#         ax1.annotate(txt, (df['time'][i], df['use_strike'][i]), fontsize=8, color='lightgray')
#
#     fig.tight_layout()
#     plt.title(f'{symbol} Data Over Time')
#     plt.show()
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

# start_time = datetime.datetime.strptime('09:19:59', '%H:%M:%S')
# end_time = datetime.datetime.strptime('15:19:59', '%H:%M:%S')
start_time = pd.to_datetime('09:19:59')
end_time = pd.to_datetime('15:19:59')
time_range = pd.date_range(start=start_time, end=end_time, freq='T')
min_range = [i for i in range(5,366)]
for sym in sym_list:
    df_name = f'df_{sym.lower()}'
    df1['time'] = time_range
    df1['minute_elapsed'] = min_range
    exec(f'{df_name} = df1.copy()')

if comp_time is None:
    comp_time = pd.to_datetime('09:19:59')

# Initialize plot
fig, ax1 = plt.subplots()
color_forward = 'tab:orange'
color_final_pnl = 'tab:blue'
color_use_strike = 'lightgray'

ax2 = ax1.twinx()
line_forward, = ax1.plot([], [], color=color_forward, label='Forward')
line_final_pnl, = ax2.plot([], [], color=color_final_pnl, label='Final PNL')
scat_use_strike = ax1.scatter([], [], color=color_use_strike)

# Customizing the plot
ax1.set_xlabel('Time')
ax1.set_ylabel('Forward', color=color_forward)
ax2.set_ylabel('Final PNL', color=color_final_pnl)
ax1.tick_params(axis='y', labelcolor=color_forward)
ax2.tick_params(axis='y', labelcolor=color_final_pnl)
ax1.axhline(0, color='black')  # x-axis at origin of final_pnl y-axis
fig.tight_layout()
plt.title('Data Over Time')


def update_plot(frame):
    global df_nifty
    ax1.clear()
    ax2.clear()
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Forward', color=color_forward)
    ax2.set_ylabel('Final PNL', color=color_final_pnl)
    ax1.tick_params(axis='y', labelcolor=color_forward)
    ax2.tick_params(axis='y', labelcolor=color_final_pnl)
    ax1.axhline(0, color='black')  # x-axis at origin of final_pnl y-axis

    ax1.plot(df_nifty['time'], df_nifty['forward'], color=color_forward, label='Forward')
    ax2.plot(df_nifty['time'], df_nifty['final_pnl'], color=color_final_pnl, label='Final PNL')
    ax1.scatter(df_nifty['time'], df_nifty['use_strike'], color=color_use_strike)

    for i, txt in enumerate(df_nifty['use_strike']):
        ax1.annotate(txt, (df_nifty['time'][i], df_nifty['use_strike'][i]), fontsize=8, color=color_use_strike)

ani = FuncAnimation(fig, update_plot, interval=1000)
plt.show(block=False)

# chk = True
initial = True
while(comp_time < end_time):
    for i in range(len(sym_list)):
        sym = sym_list[i]
        exp = exp_list[i]
        if initial:
            chk = True

        if sym == 'NIFTY':
            df_fut = df_nifty.copy()
            row_index = row_index_nifty
            chk_row_list = chk_row_list_n
            starting_index = starting_index_nifty
            if initial:
                chk = chk_condition_n = True
            else:
                chk = chk_condition_n
        elif sym == 'BANKNIFTY':
            df_fut = df_banknifty.copy()
            row_index = row_index_banknifty
            chk_row_list = chk_row_list_bn
            starting_index = starting_index_banknifty
            if initial:
                chk = chk_condition_bn = True
            else:
                chk = chk_condition_bn
        elif sym == 'FINNIFTY':
            df_fut = df_finnifty.copy()
            row_index = row_index_finnifty
            chk_row_list = chk_row_list_fn
            starting_index = starting_index_finnifty
            if initial:
                chk = chk_condition_fn = True
            else:
                chk = chk_condition_fn
        else:
            df_fut = df_midcpnifty.copy()
            row_index = row_index_midcpnifty
            chk_row_list = chk_row_list_mcn
            starting_index = starting_index_midcpnifty
            if initial:
                chk = chk_condition_mcn = True
            else:
                chk = chk_condition_mcn

        if (comp_time == pd.to_datetime('09:19:59')):
            val = get_fut_price(sym) # at 09:19:59

        df_fut['fut'] = val
        f_strike = df_fut.loc[row_index, 'fut']
        f_multiple = float(multiple[sym]['fstrike'])
        fut_strike = int(f_multiple * round(f_strike // f_multiple))
        df_fut.loc[row_index, 'fstrike'] = fut_strike
        type_list = ['CE', 'PE']
        # for each in type_list:
        #     ticker.append((sym + pd.to_datetime(exp).strftime('%d%b%y') + str(
        #         fut_strike) + each + '.NFO').upper())
        ce_ticker = sym + pd.to_datetime(exp).strftime('%d%b%y').upper() + str(
            fut_strike) + type_list[0] + '.NFO'
        pe_ticker = sym + pd.to_datetime(exp).strftime('%d%b%y').upper() + str(
            fut_strike) + type_list[1] + '.NFO'
        if row_index == starting_index:
            stt = pd.to_datetime('09:18:59')
            ett = pd.to_datetime('09:19:59')
        else:
            stt = df_fut.loc[row_index - 1, 'time']
            ett = df_fut.loc[row_index, 'time']
        df_fut.loc[row_index, ce_ticker] = get_option_price(ce_ticker, stt, ett)
        df_fut.loc[row_index, pe_ticker] = get_option_price(pe_ticker, stt, ett)
        df_fut.loc[row_index, 'forward'] = df_fut.loc[row_index, 'fstrike'] + df_fut.loc[row_index, ce_ticker] - df_fut.loc[row_index, pe_ticker]
        df_fut.loc[row_index, 'round_off'] = ceiling_xcl(df_fut.loc[row_index, 'forward'], multiple[sym]['round_off'])
        df_fut.loc[row_index, 'straddle_qty'] = -50000

        if chk:
            chk_row_list.append(row_index)
            df_fut.loc[row_index, 'use_strike'] = df_fut.loc[row_index, 'round_off']

        chk_index = chk_row_list[-1]
        df_fut.loc[row_index, 'ce'] = (sym + pd.to_datetime(exp).strftime('%d%b%y') + str(round(
            df_fut.loc[chk_index, 'use_strike'])) + 'CE.NFO').upper()
        df_fut.loc[row_index, 'ce_price'] = get_option_price(df_fut.loc[row_index, 'ce'], stt, ett)
        df_fut.loc[row_index, 'pe'] = (sym + pd.to_datetime(exp).strftime('%d%b%y') + str(
            round(df_fut.loc[chk_index, 'use_strike'])) + 'PE.NFO').upper()
        df_fut.loc[row_index, 'pe_price'] = get_option_price(df_fut.loc[row_index, 'pe'], stt, ett)

        df_fut.loc[row_index, 'straddle_price'] = df_fut.loc[row_index, 'ce_price'] + df_fut.loc[row_index, 'pe_price']

        exp_date = datetime.datetime.strptime(exp, '%d-%b-%y').date()
        business_days_left = calc_business_days(today_date, exp_date)
        tte = business_days_left + (1 - (df_fut.loc[row_index, 'minute_elapsed']) / 375)
        df_fut.loc[row_index, 'TTE'] = (business_days_left + (1 - (df_fut.loc[row_index, 'minute_elapsed']) / 375))

        list_for_greeks = [df_fut.loc[row_index, 'forward'], df_fut.loc[chk_row_list[-1], 'use_strike'],
                           df_fut.loc[row_index, 'TTE'], df_fut.loc[row_index, 'ce_price'],
                           df_fut.loc[row_index, 'pe_price']]
        df_fut.loc[row_index, 'ce_iv'], df_fut.loc[row_index, 'ce_delta'], df_fut.loc[row_index, 'ce_gamma'], \
            df_fut.loc[row_index, 'ce_theta'], df_fut.loc[row_index, 'ce_vega'] = get_greeks(list_for_greeks,
                                                                                             opt_type='CE')
        df_fut.loc[row_index, 'pe_iv'], df_fut.loc[row_index, 'pe_delta'], df_fut.loc[row_index, 'pe_gamma'], \
            df_fut.loc[row_index, 'pe_theta'], df_fut.loc[row_index, 'pe_vega'] = get_greeks(list_for_greeks,
                                                                                             opt_type='PE')
        straddle_delta_calc = df_fut.loc[row_index, 'straddle_qty'] * (
                    df_fut.loc[row_index, 'ce_delta'] + df_fut.loc[row_index, 'pe_delta'])

        if row_index == starting_index:
            df_fut.loc[row_index, 'strd_delta'] = straddle_delta_calc
        else:
            df_fut.loc[row_index, 'strd_delta'] = straddle_delta_calc + df_fut.loc[row_index - 1, 'net_fut']

        df_fut.loc[row_index, 'strd_gamma'] = (
                    (df_fut.loc[row_index, 'straddle_qty'] * df_fut.loc[row_index, 'ce_gamma']) + (
                    df_fut.loc[row_index, 'straddle_qty'] * df_fut.loc[row_index, 'pe_gamma']))
        df_fut.loc[row_index, 'strd_theta'] = (
                    (df_fut.loc[row_index, 'straddle_qty'] * df_fut.loc[row_index, 'ce_theta']) + (
                    df_fut.loc[row_index, 'straddle_qty'] * df_fut.loc[row_index, 'pe_theta']))
        df_fut.loc[row_index, 'strd_vega'] = (
                    (df_fut.loc[row_index, 'straddle_qty'] * df_fut.loc[row_index, 'ce_vega']) + (
                    df_fut.loc[row_index, 'straddle_qty'] * df_fut.loc[row_index, 'pe_vega']))

        df_fut.loc[row_index, 'hedge_pt'] = (np.sqrt(
            df_fut.loc[chk_row_list[0], 'strd_theta'] / (2 * abs(df_fut.loc[chk_row_list[0], 'strd_gamma']))))

        df_fut.loc[row_index, 'D/G'] = (df_fut.loc[row_index, 'strd_delta'] / df_fut.loc[row_index, 'strd_gamma'])

        condition = abs(df_fut.loc[row_index, 'D/G']) > abs(df_fut.loc[row_index, 'hedge_pt'])
        if condition:
            df_fut.loc[row_index, 'check'] = 'CHK'
        else:
            df_fut.loc[row_index, 'check'] = ''

        if (row_index == starting_index) or chk:
            df_fut.loc[row_index, 'option_pnl'] = 0
        else:
            df_fut.loc[row_index, 'option_pnl'] = round((df_fut.loc[row_index, 'straddle_qty'] * (
                    df_fut.loc[row_index, 'straddle_price'] - df_fut.loc[row_index - 1, 'straddle_price'])), 2)

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

        sum_delta_trade = 0
        for ri in chk_row_list:
            sum_delta_trade += df_fut.loc[ri, 'delta_trade']
        df_fut.loc[row_index, 'net_fut'] = sum_delta_trade

        if (row_index == starting_index):
            df_fut.loc[row_index, 'fut_pnl'] = 0
        else:
            sp_result = sumproduct(df_fut, chk_row_list, col1='delta_trade', col2='forward')
            df_fut.loc[row_index, 'fut_pnl'] = (
                        (df_fut.loc[row_index, 'forward'] - (sp_result / sum_delta_trade)) * df_fut.loc[
                    row_index, 'net_fut'])

        x = starting_index
        y = row_index
        cum_sum = 0
        while x <= y:
            cum_sum += df_fut.loc[x, 'option_pnl']
            x += 1
        df_fut.loc[row_index, 'cum_pnl'] = (cum_sum + df_fut.loc[row_index, 'fut_pnl'])

        df_fut.loc[row_index, 'final_pnl'] = (
                    df_fut.loc[row_index, 'cum_pnl'] / abs(df_fut.loc[row_index, 'straddle_qty']))

        if str(df_fut.loc[row_index, 'check']) == 'CHK':
            chk = True
            chk_row_list.append(row_index)
        else:
            chk = False

        # for i, row in df_fut.iterrows():
        # for i in range(0,row_index):
        #     current_time = df_fut.loc[i, 'time']
        #     # current_time = df_fut.loc[row_index, 'time']
        #     # final_pnl, use_strike = calculate_values(current_time)
        #     # df_fut.loc[row_index, 'final_pnl'] = final_pnl
        #     # df_fut.loc[row_index, 'forward'] = forward
        #
        #     # 3. Save the plot as an image file
        #     plt.figure(figsize=(12, 6))
        #     plt.plot(df_fut.loc[i, 'time'][:i + 1], row['final_pnl'][:i + 1], label='final_pnl')
        #     plt.plot(int(row['time'].timestamp()*1000[:i + 1]), row['final_pnl'][:i + 1], label='final_pnl')
        #     # plt.plot(row['time'][:i + 1], row['forward'][:i + 1], label='forward')
        #     plt.xlabel('Time')
        #     plt.ylabel('Values')
        #     plt.legend()
        #     plt.title('Final PnL and Use Strike vs Time')
        #     plt.grid(False)
        #     plt.savefig('plot.png')
        #     print('plot finished')
        #     plt.close()

        # data = [
        #     [int(df_fut.loc[i, 'time'].timestamp() * 1000), df_fut.loc[i, 'final_pnl'], df_fut.loc[i, 'forward']]
        #     for i in range(0,row_index)
        # ]
        #
        # html_template = Template("""
        # <!DOCTYPE html>
        # <html>
        # <head>
        #     <title>Dynamic Plot</title>
        #     <script src="https://code.highcharts.com/highcharts.js"></script>
        #     <script src="https://code.highcharts.com/modules/exporting.js"></script>
        #     <script src="https://code.highcharts.com/modules/export-data.js"></script>
        #     <script src="https://code.highcharts.com/modules/accessibility.js"></script>
        #     <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        # </head>
        # <body>
        #     <div id="container" style="width:100%; height:400px;"></div>
        #     <script>
        #         document.addEventListener('DOMContentLoaded', function () {
        #             var chart = Highcharts.chart('container', {
        #                 chart: {
        #                     type: 'line',
        #                     events: {
        #                         load: function () {
        #                             var series1 = this.series[0];
        #                             var series2 = this.series[1];
        #                             var data = $data;
        #                             var index = 0;
        #                             function addPoint() {
        #                                 if (index < data.length) {
        #                                     var point = data[index];
        #                                     series1.addPoint([point[0], point[1]], true, false);
        #                                     series2.addPoint([point[0], point[2]], true, false);
        #                                     index++;
        #                                 }
        #                             }
        #                             setInterval(addPoint, 30000); // Update every 30 second
        #                         }
        #                     }
        #                 },
        #                 title: {
        #                     text: 'Dynamic Final PnL and Use Strike'
        #                 },
        #                 xAxis: {
        #                     type: 'datetime',
        #                     title: {
        #                         text: 'Time'
        #                     }
        #                 },
        #                 yAxis: {
        #                     title: {
        #                         text: 'Values'
        #                     }
        #                 },
        #                 series: [{
        #                     name: 'Final PnL',
        #                     data: []
        #                 }, {
        #                     name: 'Forward',
        #                     data: []
        #                 }]
        #             });
        #         });
        #     </script>
        # </body>
        # </html>
        # """)
        #
        # html_content = html_template.substitute(data=json.dumps(data))
        #
        # # Write the HTML content to a file
        # with open('dynamic_plot.html', 'w') as file:
        #     file.write(html_content)
        #
        # print("HTML file 'dynamic_plot.html' created successfully.")
        plot_graph(df_fut, sym)
        row_index += 1

        if (sym == 'NIFTY'):
            df_nifty = df_fut.copy()
            row_index_nifty = row_index
            chk_condition_n = chk
            chk_row_list_n = chk_row_list

        elif sym == 'BANKNIFTY':
            df_banknifty = df_fut.copy()
            row_index_banknifty = row_index
            chk_condition_bn = chk
            chk_row_list_bn = chk_row_list
        elif sym == 'FINNIFTY':
            df_finnifty = df_fut.copy()
            row_index_finnifty = row_index
            chk_condition_fn = chk
            chk_row_list_fn = chk_row_list
        else:
            df_midcpnifty = df_fut.copy()
            row_index_midcpnifty = row_index
            chk_condition_mcn = chk
            chk_row_list_mcn = chk_row_list
        print(row_index)
    # 4. Wait for 30 second before updating the plot again
    time.sleep(5)
    initial = False
    comp_time += datetime.timedelta(minutes=1)
plt.show()
# ================================================================================================================================
# for i in range(len(sym_list)):
#     break_process = False
#     df_intraday = pd.DataFrame()
#     df_overnight = pd.DataFrame()
#     df_summary = pd.DataFrame()
#     sym = sym_list[i]
#     exp = exp_list[i]
#     yf_tick = tick_list[i]
#     num = i
#
#     df_fut = pd.DataFrame()
#     fut_expiry = from_master(sym)
#     df_fut.reset_index()
#     # ----------------------------------------------------------------
#     df_fut['minute_elapsed'] = [i + 1 for i in range(375)]
#     val = get_fut_close_price(sym)
#     df_fut['fut'] = val
#     # ----------------------------------------------------------------
#     if sheet == 'intraday':
#         row_index = df_fut.loc[df_fut['time'] == '09:19:59'].index[0]
#     else:
#         row_index = df_fut.loc[df_fut['time'] == '09:15:59'].index[0]
#     starting_index = row_index
#     # ----------------------------------------------------------------
#     f_strike = df_fut.loc[row_index, 'fut']
#     f_multiple = float(multiple[sym]['fstrike'])
#     fut_strike = int(f_multiple * round(f_strike // f_multiple))
#     condition = True
#     count = 0
#     while condition:
#         count += 1
#         check_df1 = df.loc[
#             (df['Symbol'] == sym) & (df['Expiry'] == exp) & (df['Opttype'] == 'CE') & (
#                         df['Strike'] == fut_strike), 'Close'].values
#         check_df2 = df.loc[
#             (df['Symbol'] == sym) & (df['Expiry'] == exp) & (df['Opttype'] == 'PE') & (
#                         df['Strike'] == fut_strike), 'Close'].values
#         if len(check_df1) == 375 and len(check_df2) == 375:
#             condition = False
#         else:
#             fut_strike += multiple[sym]['fstrike']
#             condition = True
#
#         # check to see if the src data is faulty i.e no ce pe column of any strike has 375 rows
#         if count > 375:
#             print(f'Cannot create table for symbol - {sym} with expiry - {exp} as src data is faulty hence skipping to next symbol')
#             break_process = True
#             # sys.exit()
#             break
#     if break_process:
#         break
# # ----------------------------------------------------------------------------------------------
#     df_fut['fstrike'] = fut_strike
#     # ----------------------------------------------------------------
#     #     BANKNIFTY29MAY2449400CE.NFO
#     type_list = ['CE', 'PE']
#     for each in type_list:
#         ticker.append((sym + pd.to_datetime(exp).strftime('%d%b%y') + str(
#             fut_strike) + each + '.NFO').upper())
#
#     df_fut[ticker[0]] = df.loc[
#         (df['Symbol'] == sym) & (df['Expiry'] == exp) & (df['Opttype'] == 'CE') & (
#                     df['Strike'] == fut_strike), 'Close'].values
#     df_fut[ticker[1]] = df.loc[
#         (df['Symbol'] == sym) & (df['Expiry'] == exp) & (df['Opttype'] == 'PE') & (
#                     df['Strike'] == fut_strike), 'Close'].values
#     # ----------------------------------------------------------------
#     df_fut['forward'] = df_fut['fstrike'] + df_fut[ticker[0]] - df_fut[ticker[1]]
#     # ----------------------------------------------------------------
#     df_fut['round_off'] = df_fut['forward'].apply(lambda x: ceiling_xcl(x, multiple[sym]['round_off']))  # this will have all the strikes
#     # ----------------------------------------------------------------
#     df_fut['straddle_qty'] = -50000
#     # ----------------------------------------------------------------
#     chk = True
#     chk_row_list = []
#     if sheet == 'intraday':
#         range_till = 361
#     else:
#         range_till = 365
#     for j in range(range_till):
#         # ----------------------------------------------------------------
#         if sheet == 'intraday':
#             if chk:
#                 chk_row_list.append(row_index)
#                 df_fut.loc[row_index, 'use_strike'] = df_fut.loc[row_index, 'round_off']
#         else:
#             if chk:
#                 chk_row_list.append(row_index)
#                 df_fut.loc[row_index, 'use_strike'] = df_fut.loc[row_index, 'round_off']
#             if row_index == starting_index:
#                 df_fut.loc[row_index, 'use_strike'] = prev_day_data[num][sym]['use_strike']
#         # ----------------------------------------------------------------
#         chk_index = chk_row_list[-1]
#         # ----------------------------------------------------------------
#         df_fut.loc[row_index, 'ce'] = (sym + pd.to_datetime(exp).strftime('%d%b%y') + str(round(
#             df_fut.loc[chk_index, 'use_strike'])) + 'CE.NFO').upper()
#         df_fut.loc[row_index, 'ce_price'] = get_ce_pe_price(row_index, opt_type='CE')
#         # ----------------------------------------------------------------
#         df_fut.loc[row_index, 'pe'] = (sym + pd.to_datetime(exp).strftime('%d%b%y') + str(
#             round(df_fut.loc[chk_index, 'use_strike'])) + 'PE.NFO').upper()
#         df_fut.loc[row_index, 'pe_price'] = get_ce_pe_price(row_index, opt_type='PE')
#         # ----------------------------------------------------------------
#         df_fut.loc[row_index, 'straddle_price'] = df_fut.loc[row_index, 'ce_price'] + df_fut.loc[row_index, 'pe_price']
#         # ----------------------------------------------------------------
#           # fixing 05-jun for testing
#         exp_date = datetime.datetime.strptime(exp, '%d-%b-%y').date()
#         business_days_left = calc_business_days(today_date, exp_date)
#         tte = business_days_left + (1 - (df_fut.loc[row_index, 'minute_elapsed']) / 375)
#         df_fut.loc[row_index, 'TTE'] = (business_days_left + (1 - (df_fut.loc[row_index, 'minute_elapsed']) / 375))
#         # ----------------------------------------------------------------
#         # calculating option greeks
#         start_time = datetime.datetime.now()
#         list_for_greeks = [df_fut.loc[row_index, 'forward'], df_fut.loc[chk_row_list[-1], 'use_strike'],
#                            df_fut.loc[row_index, 'TTE'], df_fut.loc[row_index, 'ce_price'],
#                            df_fut.loc[row_index, 'pe_price']]
#         df_fut.loc[row_index, 'ce_iv'], df_fut.loc[row_index, 'ce_delta'], df_fut.loc[row_index, 'ce_gamma'], \
#         df_fut.loc[row_index, 'ce_theta'], df_fut.loc[row_index, 'ce_vega'] = get_greeks(list_for_greeks, opt_type='CE')
#         # ----------------------------------------------------------------
#         df_fut.loc[row_index, 'pe_iv'], df_fut.loc[row_index, 'pe_delta'], df_fut.loc[row_index, 'pe_gamma'], \
#         df_fut.loc[row_index, 'pe_theta'], df_fut.loc[row_index, 'pe_vega'] = get_greeks(list_for_greeks, opt_type='PE')
#         #------------------------------------------------------------------------------------------
#         straddle_delta_calc = df_fut.loc[row_index, 'straddle_qty'] * (df_fut.loc[row_index, 'ce_delta'] + df_fut.loc[row_index, 'pe_delta'])
#         if row_index == starting_index:
#             df_fut.loc[row_index, 'strd_delta'] = straddle_delta_calc
#         else:
#             df_fut.loc[row_index,'strd_delta'] = straddle_delta_calc + df_fut.loc[row_index - 1,'net_fut']
#         # sum_delta_trade = 0
#         # if chk == True:
#         #     if len(chk_row_list)>1:
#         #         if row_index == (chk_row_list[-2] + 1):
#         #             for index in chk_row_list[:-2]:
#         #                 sum_delta_trade += df_fut.loc[index, 'delta_trade']
#         #             df_fut.loc[row_index, 'strd_delta'] = straddle_delta_calc + sum_delta_trade
#         #     for index in chk_row_list[:-1]:
#         #         sum_delta_trade += df_fut.loc[index, 'delta_trade']
#         #     df_fut.loc[row_index, 'strd_delta'] = straddle_delta_calc + sum_delta_trade
#         # else:
#         #     for index in chk_row_list:
#         #         sum_delta_trade += df_fut.loc[index, 'delta_trade']
#         #     df_fut.loc[row_index, 'strd_delta'] = straddle_delta_calc + sum_delta_trade
#
#         # ------------------------------------------------------------------------------------------
#         df_fut.loc[row_index, 'strd_gamma'] = ((df_fut.loc[row_index, 'straddle_qty'] * df_fut.loc[row_index, 'ce_gamma']) + (
#                     df_fut.loc[row_index, 'straddle_qty'] * df_fut.loc[row_index, 'pe_gamma']))
#         df_fut.loc[row_index, 'strd_theta'] = ((df_fut.loc[row_index, 'straddle_qty'] * df_fut.loc[row_index, 'ce_theta']) + (
#                     df_fut.loc[row_index, 'straddle_qty'] * df_fut.loc[row_index, 'pe_theta']))
#         df_fut.loc[row_index, 'strd_vega'] = ((df_fut.loc[row_index, 'straddle_qty'] * df_fut.loc[row_index, 'ce_vega']) + (
#                     df_fut.loc[row_index, 'straddle_qty'] * df_fut.loc[row_index, 'pe_vega']))
#         # ----------------------------------------------------------------
#         #         if chk:
#         #             df_fut.loc[row_index, 'hedge_pt'] = np.sqrt(df_fut.loc[row_index, 'theta'] / (2 * abs(df_fut.loc[row_index, 'gamma'])))
#
#         df_fut.loc[row_index, 'hedge_pt'] = (np.sqrt(
#             df_fut.loc[chk_row_list[0], 'strd_theta'] / (2 * abs(df_fut.loc[chk_row_list[0], 'strd_gamma']))))
#         # ----------------------------------------------------------------
#         df_fut.loc[row_index, 'D/G'] = (df_fut.loc[row_index, 'strd_delta'] / df_fut.loc[row_index, 'strd_gamma'])
#         # ----------------------------------------------------------------
#         condition = abs(df_fut.loc[row_index, 'D/G']) > abs(df_fut.loc[row_index, 'hedge_pt'])
#         if condition:
#             df_fut.loc[row_index, 'check'] = 'CHK'
#         else:
#             df_fut.loc[row_index, 'check'] = ''
#         if sheet == 'overnight':
#             if row_index == starting_index:
#                 df_fut.loc[row_index, 'check'] = ''
#         # ----------------------------------------------------------------
#         # if (row_index == starting_index) or (str(df_fut.loc[row_index-1, 'check']) == 'CHK'):
#         #     df_fut.loc[row_index, 'option_pnl'] = 0
#         # else:
#         #     df_fut.loc[row_index, 'option_pnl'] = df_fut.loc[row_index, 'straddle_qty'] * (
#         #             df_fut.loc[row_index, 'straddle_price'] - df_fut.loc[row_index - 1, 'straddle_price'])
#         if sheet == 'intraday':
#             if (row_index == starting_index) or chk:
#                     df_fut.loc[row_index, 'option_pnl'] = 0
#             else:
#                 df_fut.loc[row_index, 'option_pnl'] = round((df_fut.loc[row_index, 'straddle_qty'] * (
#                             df_fut.loc[row_index,'straddle_price'] - df_fut.loc[row_index - 1,'straddle_price'])), 2)
#         else:
#             if (row_index == starting_index):
#                 df_fut.loc[row_index, 'option_pnl'] = round((df_fut.loc[row_index, 'straddle_qty'] * (
#                         df_fut.loc[row_index, 'straddle_price'] - prev_day_data[num][sym]['strd_price'])), 2)
#             elif chk:
#                 df_fut.loc[row_index, 'option_pnl'] = 0
#             else:
#                 df_fut.loc[row_index, 'option_pnl'] = round((df_fut.loc[row_index, 'straddle_qty'] * (
#                         df_fut.loc[row_index, 'straddle_price'] - df_fut.loc[row_index - 1, 'straddle_price'])), 2)
#         # ----------------------------------------------------------------
#         if chk or row_index == starting_index:
#             deltatrade_calc = 0
#             deltatrade_calc = multiple[sym]['delta'] * round(
#                 df_fut.loc[row_index, 'strd_delta'] / multiple[sym]['delta'])
#             we = df_fut.loc[row_index, 'strd_delta']
#             if df_fut.loc[row_index, 'strd_delta'] > 0:
#                 use_multiple = -1
#             else:
#                 use_multiple = 1
#             df_fut.loc[row_index, 'delta_trade'] = use_multiple * abs(deltatrade_calc)
#         # ----------------------------------------------------------------
#         sum_delta_trade = 0
#         for ri in chk_row_list:
#             sum_delta_trade += df_fut.loc[ri, 'delta_trade']
#         df_fut.loc[row_index, 'net_fut'] = sum_delta_trade
#         # ----------------------------------------------------------------
#         # a, b = 0, 0
#         # for i in chk_row_list:
#         #     a += (df_fut.loc[i, 'delta_trade'] * df_fut.loc[i, 'forward'])
#         #     b += df_fut.loc[i, 'delta_trade']
#
#         if (row_index == starting_index):
#             df_fut.loc[row_index, 'fut_pnl'] = 0
#         else:
#             # df_fut.loc[row_index, 'fut_pnl'] = (df_fut.loc[row_index, 'forward'] - (a / b)) * b
#             # df_fut.loc[row_index, 'cum_pnl'] = df_fut['option_pnl'].sum() + df_fut.loc[row_index, 'fut_pnl']
#             sp_result = sumproduct(df_fut, chk_row_list, col1='delta_trade', col2='forward')
#             df_fut.loc[row_index, 'fut_pnl'] = ((df_fut.loc[row_index, 'forward'] - (sp_result/sum_delta_trade)) * df_fut.loc[row_index, 'net_fut'])
#         # ----------------------------------------------------------------
#         x = starting_index
#         y = row_index
#         cum_sum = 0
#         if sheet == 'intraday':
#             while x <= y:
#                 cum_sum += df_fut.loc[x, 'option_pnl']
#                 x += 1
#             df_fut.loc[row_index, 'cum_pnl'] = (cum_sum + df_fut.loc[row_index, 'fut_pnl'])
#         else:
#             if row_index == starting_index:
#                 df_fut.loc[row_index, 'cum_pnl'] = 0
#             else:
#                 while x <= y:
#                     cum_sum += df_fut.loc[x, 'option_pnl']
#                     x += 1
#                 df_fut.loc[row_index, 'cum_pnl'] = (cum_sum + df_fut.loc[row_index, 'fut_pnl'])
#         # ----------------------------------------------------------------
#         if sheet == 'intraday':
#             df_fut.loc[row_index, 'final_pnl'] = (df_fut.loc[row_index, 'cum_pnl'] / abs(df_fut.loc[row_index, 'straddle_qty']))
#         else:
#             if row_index == starting_index:
#                 df_fut.loc[row_index, 'final_pnl'] = 0
#             else:
#                 df_fut.loc[row_index, 'final_pnl'] = (
#                             df_fut.loc[row_index, 'cum_pnl'] / abs(df_fut.loc[row_index, 'straddle_qty']))
#         # ----------------------------------------------------------------
#         if str(df_fut.loc[row_index, 'check']) == 'CHK':
#             chk = True
#         else:
#             chk = False
#         row_index += 1
#
#     # df_fut.loc[chk_row_list[0], 'option_pnl'], df_fut.loc[chk_row_list[0], 'fut_pnl'], df_fut.loc[
#     #     chk_row_list[0], 'cum_pnl'] = 0, 0, 0
#     # for each in chk_row_list:
#     #     df_fut.loc[each, 'option_pnl'] = 0
#     #
#     # def save_to_sheet(df, sheet_name, wb):
#     #     ws = wb.create_sheet(title = sheet_name)
#     #     for each_line in dataframe_to_rows(df, index = False, header = True):
#     #         ws.append(each_line)
#     #
#     #     stt = '09:19:59'
#     #     ett = '15:19:59'
#     #     filtered_df = df_fut[(df_fut['time'] >= stt) & (df_fut['time'] <= ett)]
#     #
#     #     sns.set(style='whitegrid')
#     #     sns.set_context('talk')
#     #
#     #     # fig, ax1 = plt.subplot(figsize=(12,6))
#     #     fig, ax1 = plt.subplots(figsize=(15, 7.5))
#     #
#     #     sns.lineplot(x='time', y='final_pnl', data=filtered_df, ax=ax1, color='blue', label='Final PnL')
#     #     ax1.set_ylabel('Final PnL', color='blue', fontsize=5)
#     #     ax1.tick_params(axis='y', labelcolor='blue')
#     #
#     #     ax2 = ax1.twinx()
#     #
#     #     sns.lineplot(x='time', y='forward', data=filtered_df, ax=ax2, color='orange', label='Forward')
#     #     ax2.set_ylabel('Forward', color='orange', fontsize=5)
#     #     ax2.tick_params(axis='y', labelcolor='orange')
#     #
#     #     ax1.axhline(0, color='black', linewidth=1, linestyle='--')
#     #
#     #     plt.title(f'{sym} Straddle ({exp})')
#     #     ax1.set_xlabel('Time', fontsize=5)
#     #
#     #     time_interval = 15
#     #     # time_labels = [f'{i * time_interval // 60}:{(i * time_interval) % 60}' for i in range(int(375/time_interval))]
#     #     time_labels = df_fut['time'].iloc[::time_interval].tolist()
#     #     ax1.set_xticks(range(0, len(filtered_df['time']), time_interval))
#     #     ax1.set_xticklabels(time_labels, fontsize=8)
#     #
#     #     plt.setp(ax1.xaxis.get_majorticklabels(), rotation=90, ha='right')
#     #     ax1.grid(False)
#     #
#     #     ax1.tick_params(axis='x', labelsize=8)
#     #     by_buffer = io.BytesIO()
#     #     plt.savefig(by_buffer, format='png')
#     #     plt.close()
#     #
#     #     img = Image(by_buffer)
#     #     img.anchor = 'A1'
#     #     ws.add_image(img)
#
#     df_fut = df_fut.round(decimals=3)
#     # df_fut_copied = df_fut.copy()
#     if sheet == 'intraday':
#         df_intraday= df_fut.copy()
#     else:
#         df_overnight = df_fut.copy()
# # ----------------------------------------------------------------------------------------------
#     int_starting_index = df_intraday.loc[df_intraday['time'] == '09:19:59'].index[0]
#     int_ending_index = df_intraday.loc[df_intraday['time'] == '15:19:59'].index[0]
#
#     ov_starting_index = df_overnight.loc[df_overnight['time'] == '09:19:59'].index[0]
#     ov_ending_index = df_overnight.loc[df_overnight['time'] == '15:19:59'].index[0]
#
#     bod = round(df_intraday.loc[int_starting_index, 'TTE'])
#     # df_summary['BoD'] = bod
#     # df_summary['EoD'] = bod-1
#     df1 = yf.download(yf_tick, start=yesterday, end=today_date)
#     df2 = yf.download(yf_tick, start=today_date, end=tomorrow)
#     # df_summary['Spot_Close_Yesterday'] = round(df1['Close'].values[0], 2)
#     # df_summary['Spot_Close_Today'] = round(df2['Close'].values[0], 2)
#
#     overnight_pts = df_overnight.loc[ov_ending_index, 'final_pnl']
#     # df_summary['Overnight_Pts'] = overnight_pts
#     # df_summary['Overnight_theta_retn'] = overnight_pts / (prev_day_data[num][sym]['strd_theta'] / 50000)
#
#     intraday_pts = df_intraday.loc[int_ending_index, 'final_pnl']
#     # df_summary['Intraday_Pts'] = intraday_pts
#     # df_summary['Intraday_theta_retn'] = intraday_pts / (df_intraday.loc[starting_index, 'strd_theta'] / 50000)
#     # df_summary['Strd_Initiation_price'] = df_intraday.loc[starting_index, 'straddle_price']
#     # df_summary['Strd_Exit_price'] = df_intraday.loc[ending_index, 'straddle_price']
#     eod_bod = df_overnight.loc[ov_ending_index, 'final_pnl']
#
#     summary_data = {
#         'Today': [today_date],
#         'Expiry': [exp],
#         'BoD': [bod],
#         'EoD': [bod - 1],
#         'Spot_Close_Yesterday': [round(df1['Close'].values[0], 2)],
#         'Spot_Close_Today': [round(df2['Close'].values[0], 2)],
#         'Overnight_Pts': [overnight_pts],
#         'Overnight_theta_retn': [overnight_pts / (prev_day_data[num][sym]['strd_theta'] / 50000)],
#         'Intraday_Pts': [intraday_pts],
#         'Intraday_theta_retn': [intraday_pts / (df_intraday.loc[int_starting_index, 'strd_theta'] / 50000)],
#         'Strd_Initiation_price': [df_intraday.loc[int_starting_index, 'straddle_price']],
#         'Strd_Exit_price': [df_intraday.loc[int_ending_index, 'straddle_price']],
#         'EoD-BoD PnL': [eod_bod],
#         'EoD-BoD+Intraday': [intraday_pts + eod_bod]
#     }
#     df_summary = df_summary.from_dict(summary_data, orient='columns')
#
#     wb = Workbook()
#     wb.remove(wb.active)
#     save_to_sheet(df_intraday, 'Intraday', wb)
#     save_to_sheet(df_overnight, 'Overnight', wb)
#     save_to_sheet(df_summary, 'Summary', wb)
#     filename = f'test_intraday_overnight_with_chart_{sym}_{today_date}.xlsx'
#     wb.save(filename)
#     print(f'Excel file created for {sym} - {today_date}')
#     df_fut = df_fut.empty