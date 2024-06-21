import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd
import numpy as np
import datetime
from assets import ceiling_xcl, get_greeks, calc_business_days, sumproduct, change_format
from common import root_dir, logs_dir, logger, today_date, yesterday, tomorrow
from remote_db_ops import from_master
from assets_xts import get_fut_price, get_option_price
# from highcharts_core.chart import Highchart
# from highcharts_core.options.series.line import LineSeries
# from highcharts_core.options.series.scatter import ScatterSeries
# from highcharts_core.utility_classes.javascript_functions import JSFunction
# from highcharts_core.chart import Chart
# from highcharts_core.options.series.line import LineSeries
# from highcharts_core.options.series.scatter import ScatterSeries
## from highcharts_stock.chart import Chart
## from highcharts_stock.options.series.line import LineSeries
## from highcharts_stock.options.series.scatter import ScatterSeries
import highcharts_stock as hs
# import highcharts
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
sym_list = ['NIFTY']
exp_list = ['20-Jun-24']
multiple = {
        'BANKNIFTY': {'fstrike': 100, 'round_off':100, 'delta': 15},
        'NIFTY': {'fstrike':100, 'round_off': 50, 'delta': 25},
        'FINNIFTY': {'fstrike':50, 'round_off': 50, 'delta': 40},
        'MIDCPNIFTY': {'fstrike':50, 'round_off': 25, 'delta': 75}
}
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

def update_chart(num):
    ax1.clear()
    ax2.clear()
    ax1.plot(df_fut['time'], df_fut['forward'], color='#FFC080', label='Forward')
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Forward', color='#FFC080')
    ax1.tick_params(axis='y', labelcolor='#FFC080')
    ax2.plot(df_fut['time'], df_fut['final_pnl'], color='#ADD8E6', label='Final PnL')
    ax2.set_ylabel('Final PnL', color='#ADD8E6')
    ax2.tick_params(axis='y', labelcolor='#ADD8E6')
    ax1.scatter(df_fut['time'], df_fut['use_strike'], color='#C0C0C0', label='Use Strike')
    plt.title('Forward, Final PnL, and Use Strike vs Time')
    plt.legend()
# def plot_dynamic_graph(df, sym):
#     chart = Chart()
#     chart.options.title.text = f'{sym} Analysis'
#     chart.options.xAxis.categories = df['time'].astype(str).tolist()
#     chart.options.xAxis.title.text = 'Time'
#     chart.options.yAxis = [{
#         'title': {'text': 'Forward'},
#         'opposite': False
#     }, {
#         'title': {'text': 'Final PnL'},
#         'opposite': True
#     }]
#     # Forward vs Time
#     forward_series = LineSeries()
#     forward_series.name = 'Forward'
#     forward_series.data = df['forward'].tolist()
#     forward_series.yAxis = 0
#     forward_series.color = '#FFA500'
#     chart.add_series(forward_series)
#     # Final PnL vs Time
#     final_pnl_series = LineSeries()
#     final_pnl_series.name = 'Final PnL'
#     final_pnl_series.data = df['final_pnl'].tolist()
#     final_pnl_series.yAxis = 1
#     final_pnl_series.color = '#ADD8E6'
#     chart.add_series(final_pnl_series)
#     # Use Strike points
#     use_strike_series = ScatterSeries()
#     use_strike_series.name = 'Use Strike'
#     use_strike_series.data = [{'x': idx, 'y': row['forward'], 'name': row['use_strike']} for idx, row in df.iterrows()
#                               if not pd.isna(row['use_strike'])]
#     use_strike_series.color = '#D3D3D3'
#     chart.add_series(use_strike_series)
#     chart.save_file(f'{sym}_dynamic_chart.html')

## def plot_dynamic_graph(df, sym):
#     chart = Chart()
#     chart.options.title.text = f'{sym} Analysis'
#     chart.options.xAxis.categories = df['time'].astype(str).tolist()
#     chart.options.xAxis.title.text = 'Time'
#     chart.options.yAxis = [{
#         'title': {'text': 'Forward'},
#         'opposite': False
#     }, {
#         'title': {'text': 'Final PnL'},
#         'opposite': True
#     }]
#     # Forward vs Time
#     forward_series = LineSeries()
#     forward_series.name = 'Forward'
#     forward_series.data = df['forward'].tolist()
#     forward_series.yAxis = 0
#     forward_series.color = '#FFA500'
#     chart.add_series(forward_series)
#     # Final PnL vs Time
#     final_pnl_series = LineSeries()
#     final_pnl_series.name = 'Final PnL'
#     final_pnl_series.data = df['final_pnl'].tolist()
#     final_pnl_series.yAxis = 1
#     final_pnl_series.color = '#ADD8E6'
#     chart.add_series(final_pnl_series)
#     # Use Strike points
#     use_strike_series = ScatterSeries()
#     use_strike_series.name = 'Use Strike'
#     use_strike_series.data = [{'x': idx, 'y': row['forward'], 'name': row['use_strike']} for idx, row in df.iterrows() if not pd.isna(row['use_strike'])]
#     use_strike_series.color = '#D3D3D3'
#     chart.add_series(use_strike_series)
#     chart.save_file(f'{sym}_dynamic_chart.html')

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
        # Plot the graph(working but making new plot on each iteration
        fig, ax1 = plt.subplots()
        ax1.plot(df_fut['time'], df_fut['forward'], color='#FFC080', label='Forward')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Forward', color='#FFC080')
        ax1.tick_params(axis='y', labelcolor='#FFC080')

        ax2 = ax1.twinx()
        ax2.plot(df_fut['time'], df_fut['final_pnl'], color='#ADD8E6', label='Final PnL')
        ax2.set_ylabel('Final PnL', color='#ADD8E6')
        ax2.tick_params(axis='y', labelcolor='#ADD8E6')

        ax1.scatter(df_fut['time'], df_fut['use_strike'], color='#C0C0C0', label='Use Strike')

        plt.title('Forward, Final PnL, and Use Strike vs Time')
        plt.legend()

        plt.show(block=False)  # show the plot without blocking

        # Update the plot every 30 seconds
        plt.pause(5)

        # Clear the plot for the next iteration
        plt.clf()

    time.sleep(60)
    initial = False
    comp_time += datetime.timedelta(minutes=1)