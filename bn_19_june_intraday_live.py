import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd
import numpy as np
import datetime
import os
import glob
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from openpyxl import Workbook
import io
from openpyxl.drawing.image import Image
from openpyxl.utils.dataframe import dataframe_to_rows

from assets import ceiling_xcl, get_greeks, calc_business_days, sumproduct, change_format
from common import root_dir, logs_dir, logger, today_date, yesterday, tomorrow
from remote_db_ops import from_master
from assets_xts import get_fut_price, get_option_price

ticker = sym_list = exp_list = plotted_symbols = []
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
sym_list = ['NIFTY']
exp_list = ['20-Jun-24']
multiple = {
        'BANKNIFTY': {'fstrike': 100, 'round_off':100, 'delta': 15},
        'NIFTY': {'fstrike':100, 'round_off': 50, 'delta': 25},
        'FINNIFTY': {'fstrike':50, 'round_off': 50, 'delta': 40},
        'MIDCPNIFTY': {'fstrike':50, 'round_off': 25, 'delta': 75}
}
# ================================================================================================================================
def save_to_sheet(df, sheet_name, wb, plot_graph = False):
    # if sheet_name == 'intraday':
    ws = wb.create_sheet(title=sheet_name)
    for each_line in dataframe_to_rows(df, index=False, header=True):
        print(each_line)
        ws.append(each_line)
    if plot_graph:
        #using matplotlib
        # Convert 'time' column to datetime for filtering
        # df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S')
        # df['time'] = df['time'].dt.time
        # # Filter the dataframe based on the given time range
        # start_time = pd.to_datetime('09:19:59', format='%H:%M:%S').time()
        # end_time = pd.to_datetime('15:19:59', format='%H:%M:%S').time()
        # df_filtered = df[(df['time'] >= start_time) & (df['time'] <= end_time)]
        stt = '09:19:59'
        ett = '15:19:59'
        df_filtered = df[(df['time'] >= stt) & (df['time'] <= ett)]

        # Plotting
        fig, ax1 = plt.subplots(figsize=(15, 8))  # Increase the size of the graph

        # Plot forward vs time
        ax1.plot(df_filtered['time'], df_filtered['forward'], color='#FFA07A', label='Forward')  # light orange

        # Create a second y-axis for final_pnl
        ax2 = ax1.twinx()
        ax2.plot(df_filtered['time'], df_filtered['final_pnl'], color='#ADD8E6', label='Final PnL')  # light blue

        # Plot use_strike values as points and annotate
        use_strike_points = df_filtered.dropna(subset=['use_strike'])
        ax1.scatter(use_strike_points['time'], use_strike_points['use_strike'], color='#D3D3D3', label='Use Strike',
                    zorder=5)  # light gray

        # Annotate each use_strike point with its value
        for i, row in use_strike_points.iterrows():
            ax1.annotate(f"{row['use_strike']}", (row['time'], row['use_strike']),
                         textcoords="offset points", xytext=(0, 10), ha='center', fontsize=10)

        # Formatting
        ax1.set_xlabel('Time', color='black', fontsize=10)
        ax1.set_ylabel('Forward', color='black', fontsize=10)
        ax2.set_ylabel('Final PnL', color='black', fontsize=10)
        ax1.tick_params(axis='both', which='major', labelsize=8, labelcolor='black')  # Adjust tick label size for ax1
        ax2.tick_params(axis='both', which='major', labelsize=8, labelcolor='black')  # Adjust tick label size for ax2

        # settign x-axis at origin of final_pnl
        ax2.spines['bottom'].set_position(('data', 0))
        ax2.spines['bottom'].set_color('black')
        ax2.spines['bottom'].set_linewidth(1)

        plt.title(f'{sym.upper()} Straddle ({exp.upper()} Expiry)')

        by_buffer = io.BytesIO()
        plt.savefig(by_buffer, format='png')
        plt.close()

        img = Image(by_buffer)
        img.anchor = 'A1'
        ws.add_image(img)
# ================================================================================================================================
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
initial = True
multiple = {
        'BANKNIFTY': {'fstrike': 100, 'round_off':100, 'delta': 15},
        'NIFTY': {'fstrike':100, 'round_off': 50, 'delta': 25},
        'FINNIFTY': {'fstrike':50, 'round_off': 50, 'delta': 40},
        'MIDCPNIFTY': {'fstrike':50, 'round_off': 25, 'delta': 75}
}
prev_day_data = [
    {'FINNIFTY': {'use_strike': 22400, 'strd_price': 352, 'strd_theta':   1600000}}
]
sheet_list = ['intraday', 'overnight']

while(comp_time <= end_time):
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
        df_fut.loc[row_index, 'ce_iv'], df_fut.loc[row_index, 'ce_delta'], df_fut.loc[row_index, 'ce_gamma'],df_fut.loc[row_index, 'ce_theta'], df_fut.loc[row_index, 'ce_vega'] = get_greeks(list_for_greeks,opt_type='CE')
        df_fut.loc[row_index, 'pe_iv'], df_fut.loc[row_index, 'pe_delta'], df_fut.loc[row_index, 'pe_gamma'], df_fut.loc[row_index, 'pe_theta'], df_fut.loc[row_index, 'pe_vega'] = get_greeks(list_for_greeks, opt_type='PE')
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
        # plot_dynamic_graph(df_fut, sym)
        if sym not in plotted_symbols:
            fig = plot_dynamic_graph(df, sym)
            plotted_symbols.append(sym)
        else:
            fig = update_graph(fig, df, sym)
        # display the graph
        fig.show()
    time.sleep(60)
    initial = False
    comp_time += datetime.timedelta(minutes=1)