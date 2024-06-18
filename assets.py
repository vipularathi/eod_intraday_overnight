import pandas as pd
import numpy as np
import datetime
import mibian
import os
import glob
from common import root_dir, logger, today_date
import re
import datetime
import seaborn as sns
import matplotlib.dates as mdates
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from openpyxl.utils.dataframe import dataframe_to_rows
import matplotlib.pyplot as plt
import io
import sys
import yfinance as yf
import plotly.graph_objects as go

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
    pattern = r'([A-Z]+)(\d{2})([A-Z]{3})(\d{2})(\d{4,5})([A-Z]{2})\.NFO'
    match = re.match(pattern, ticker)
    # print('Extracting the GFD data to DATA')
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
    data_file_path = os.path.join(root_dir, f'Data_NSEFO_{today_date}.csv')
    new_df.to_csv(data_file_path, index=False)
    logger.info('GFD file format changed to Data_NSEFO')
    return True

# today_date = datetime.datetime.strptime('05-jun-24', '%d-%b-%y').date()
# exp_time = datetime.datetime.strptime('12-jun-24', '%d-%b-%y').date()
# bus = calc_business_days(today_date, exp_time)
# print(bus)

# def save_to_sheet(df, sheet_name, wb, plot_graph = False):
#     # if sheet_name == 'intraday':
#     ws = wb.create_sheet(title=sheet_name)
#     for each_line in dataframe_to_rows(df, index=False, header=True):
#         print(each_line)
#         ws.append(each_line)
# # ----------------------------------------------------------------
#     if plot_graph:
#         # stt = '09:19:59'
#         # ett = '15:19:59'
#         # filtered_df = df[(df['time'] >= stt) & (df['time'] <= ett)]
#         #
#         # sns.set(style='whitegrid')
#         # sns.set_context('talk')
#         #
#         # # fig, ax1 = plt.subplot(figsize=(12,6))
#         # fig, ax1 = plt.subplots(figsize=(15, 7.5))
#         #
#         # sns.lineplot(x='time', y='final_pnl', data=filtered_df, ax=ax1, color='blue', label='Final PnL')
#         # ax1.set_ylabel('Final PnL', color='blue', fontsize=8)
#         # ax1.tick_params(axis='y', labelcolor='blue')
#         #
#         # ax2 = ax1.twinx()
#         #
#         # sns.lineplot(x='time', y='forward', data=filtered_df, ax=ax2, color='orange', label='Forward')
#         # ax2.set_ylabel('Forward', color='orange', fontsize=5)
#         # ax2.tick_params(axis='y', labelcolor='orange')
#         #
#         # ax1.axhline(0, color='black', linewidth=1, linestyle='--')
#         #
#         # #for use_strike
#         # use_strike_pts = df.dropna(subset=['use_strike'])
#         # plt.scatter(use_strike_pts['time'], use_strike_pts['use_strike'], color='red', label='USE StRIKE')
#         #
#         # plt.title(f'{sym} Straddle ({exp})')
#         # ax1.set_xlabel('Time', fontsize=5)
#         #
#         # time_interval = 15
#         # # time_labels = [f'{i * time_interval // 60}:{(i * time_interval) % 60}' for i in range(int(375/time_interval))]
#         # time_labels = df['time'].iloc[::time_interval].tolist()
#         # ax1.set_xticks(range(0, len(filtered_df['time']), time_interval))
#         # ax1.set_xticklabels(time_labels, fontsize=8)
#         #
#         # plt.setp(ax1.xaxis.get_majorticklabels(), rotation=90, ha='right')
#         # ax1.grid(False)
#         #
#         # ax1.tick_params(axis='x', labelsize=8)
#         # by_buffer = io.BytesIO()
#         # plt.savefig(by_buffer, format='png')
#         # plt.close()
#         #
#         # img = Image(by_buffer)
#         # img.anchor = 'A1'
#         # ws.add_image(img)
#     # ----------------------------------------------------------------
#         #using matplotlib
#         # Convert 'time' column to datetime for filtering
#         df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S')
#
#         # Filter the dataframe based on the given time range
#         start_time = pd.to_datetime('09:19:59', format='%H:%M:%S').time()
#         end_time = pd.to_datetime('15:19:59', format='%H:%M:%S').time()
#         df_filtered = df[(df['time'].dt.time >= start_time) & (df['time'].dt.time <= end_time)]
#         df_filtered['time'] = df_filtered['time'].dt.time
#         # stt = '09:19:59'
#         # ett = '15:19:59'
#         # df_filtered = df[(df['time'] >= stt) & (df['time'] <= ett)]
#
#         # Plotting
#         fig, ax1 = plt.subplots(figsize=(15, 8))  # Increase the size of the graph
#
#         # Plot forward vs time
#         ax1.plot(df_filtered['time'], df_filtered['forward'], color='#FFA07A', label='Forward')  # light orange
#
#         # Create a second y-axis for final_pnl
#         ax2 = ax1.twinx()
#         ax2.plot(df_filtered['time'], df_filtered['final_pnl'], color='#ADD8E6', label='Final PnL')  # light blue
#
#         # Plot use_strike values as points and annotate
#         use_strike_points = df_filtered.dropna(subset=['use_strike'])
#         ax1.scatter(use_strike_points['time'], use_strike_points['use_strike'], color='#D3D3D3', label='Use Strike',
#                     zorder=5)  # light gray
#
#         # Annotate each use_strike point with its value
#         for i, row in use_strike_points.iterrows():
#             ax1.annotate(f"{row['use_strike']}", (row['time'], row['use_strike']),
#                          textcoords="offset points", xytext=(0, 10), ha='center', fontsize=10)
#
#         # Formatting
#         ax1.set_xlabel('Time', color='black', fontsize=10)
#         ax1.set_ylabel('Forward', color='black', fontsize=10)
#         ax2.set_ylabel('Final PnL', color='black', fontsize=10)
#         ax1.tick_params(axis='both', which='major', labelsize=5, labelcolor='black')  # Adjust tick label size for ax1
#         ax2.tick_params(axis='both', which='major', labelsize=5, labelcolor='black')  # Adjust tick label size for ax2
#
#         plt.title('Forward and Final PnL Over Time')
#
#         # Adjust layout to make space for the legend
#         plt.tight_layout()
#
#         by_buffer = io.BytesIO()
#         plt.savefig(by_buffer, format='png')
#         plt.close()
#
#         img = Image(by_buffer)
#         img.anchor = 'A1'
#         ws.add_image(img)
#     # ----------------------------------------------------------------
#         #using plotly
#         #try1
#         # # Convert 'time' column to datetime for filtering
#         # df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S')
#         #
#         # # Filter the dataframe based on the given time range
#         # start_time = pd.to_datetime('09:19:59', format='%H:%M:%S').time()
#         # end_time = pd.to_datetime('15:19:59', format='%H:%M:%S').time()
#         # filtered_df = df[(df['time'].dt.time >= start_time) & (df['time'].dt.time <= end_time)]
#         # # filtered_df = df[(df['time'] >= stt) & (df['time'] <= ett)]
#         #
#         # # Create the figure with Plotly
#         # fig = go.Figure()
#         #
#         # # Add forward line plot
#         # fig.add_trace(go.Scatter(x=filtered_df['time'], y=filtered_df['forward'],
#         #                          mode='lines', name='Forward',
#         #                          line=dict(color='orange')))
#         #
#         # # Add final_pnl line plot
#         # fig.add_trace(go.Scatter(x=filtered_df['time'], y=filtered_df['final_pnl'],
#         #                          mode='lines', name='Final PnL',
#         #                          line=dict(color='lightblue'), yaxis='y2'))
#         #
#         # # Add use_strike points
#         # use_strike_points = filtered_df.dropna(subset=['use_strike'])
#         # fig.add_trace(go.Scatter(x=use_strike_points['time'], y=use_strike_points['use_strike'],
#         #                          mode='markers+text', name='Use Strike',
#         #                          text=use_strike_points['use_strike'],
#         #                          textposition='top center',
#         #                          marker=dict(color='gray', size=10)))
#         #
#         # # Update layout for secondary y-axis
#         # fig.update_layout(
#         #     title='Forward and Final PnL Over Time',
#         #     xaxis=dict(title='Time', tickfont=dict(size=15)),
#         #     yaxis=dict(title='Forward', tickfont=dict(size=15), titlefont=dict(color='black')),
#         #     yaxis2=dict(title='Final PnL', overlaying='y', side='right', tickfont=dict(size=5),
#         #                 titlefont=dict(color='black')),
#         #     font=dict(size=10, color='black'),
#         #     width=800,  # Adjust width
#         #     height=500,  # Adjust height
#         #     showlegend=False
#         # )
#         #
#         # # Save the figure as a static image (png)
#         # by_buffer = io.BytesIO()
#         # fig.write_image(by_buffer, format='png')
#         # by_buffer.seek(0)  # Reset buffer position to the start
#         #
#         # # Insert image into Excel
#         # img = Image(by_buffer)
#         # img.anchor = 'A1'
#         # ws.add_image(img)
#
#         # #try2
#         # df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S')
#         # start_time = pd.to_datetime('09:19:59', format='%H:%M:%S').time()
#         # end_time = pd.to_datetime('15:19:59', format='%H:%M:%S').time()
#         # filtered_df = df[(df['time'].dt.time >= start_time) & (df['time'].dt.time <= end_time)]
#         #
#         # fig = go.Figure()
#         #
#         # fig.add_trace(go.Scatter(x=filtered_df['time'], y=filtered_df['forward'],
#         #                          mode='lines', name='Forward',
#         #                          line=dict(color='orange')))
#         # fig.add_trace(go.Scatter(x=filtered_df['time'], y=filtered_df['final_pnl'],
#         #                          mode='lines', name='Final PnL',
#         #                          line=dict(color='lightblue'), yaxis='y2'))
#         # use_strike_points = filtered_df.dropna(subset=['use_strike'])
#         # fig.add_trace(go.Scatter(x=use_strike_points['time'], y=use_strike_points['use_strike'],
#         #                          mode='markers+text', name='Use Strike',
#         #                          text=use_strike_points['use_strike'],
#         #                          textposition='top center',
#         #                          marker=dict(color='gray', size=10)))
#         #
#         # fig.update_layout(
#         #     title='Forward and Final PnL Over Time',
#         #     xaxis=dict(title='Time', tickfont=dict(size=15)),
#         #     yaxis=dict(title='Forward', tickfont=dict(size=15), titlefont=dict(color='black')),
#         #     yaxis2=dict(title='Final PnL', overlaying='y', side='right', tickfont=dict(size=15),
#         #                 titlefont=dict(color='black')),
#         #     font=dict(size=10, color='black'),
#         #     width=800,
#         #     height=500,
#         #     showlegend=False
#         # )
#         #
#         # by_buffer = io.BytesIO()
#         # fig.write_image(by_buffer, format='png')
#         # by_buffer.seek(0)
#         #
#         # img = Image(by_buffer)
#         # img.anchor = 'A1'
#         # ws.add_image(img)
#     # ----------------------------------------------------------------
#     # #     using seaborn
#     #     # Convert 'time' column to datetime for filtering
#     #     # df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S')
#     #     #
#     #     # # Filter the dataframe based on the given time range
#     #     # start_time = pd.to_datetime('09:19:59', format='%H:%M:%S').time()
#     #     # end_time = pd.to_datetime('15:19:59', format='%H:%M:%S').time()
#     #     # df_filtered = df[(df['time'].dt.time >= start_time) & (df['time'].dt.time <= end_time)]
#     #
#     #     stt = '09:19:59'
#     #     ett = '15:19:59'
#     #     df_filtered = df[(df['time'] >= stt) & (df['time'] <= ett)]
#     #
#     #     # Plotting
#     #     fig, ax1 = plt.subplots(figsize=(10, 6))  # Adjust size as needed
#     #
#     #     # Plot forward vs time using Seaborn
#     #     sns.lineplot(x='time', y='forward', data=df_filtered, ax=ax1, color='orange', label='Forward')
#     #
#     #     # Create a second y-axis for final_pnl
#     #     ax2 = ax1.twinx()
#     #     sns.lineplot(x='time', y='final_pnl', data=df_filtered, ax=ax2, color='lightblue', label='Final PnL')
#     #
#     #     # Plot use_strike values as points and annotate
#     #     use_strike_points = df_filtered.dropna(subset=['use_strike'])
#     #     sns.scatterplot(x='time', y='use_strike', data=use_strike_points, ax=ax1, color='gray', s=100, label='Use Strike')
#     #
#     #     # Annotate each use_strike point with its value
#     #     for i, row in use_strike_points.iterrows():
#     #         ax1.annotate(f"{row['use_strike']}", (row['time'], row['use_strike']),
#     #                      textcoords="offset points", xytext=(0, 10), ha='center', fontsize=10)
#     #
#     #     # Formatting
#     #     ax1.set_xlabel('Time', color='black', fontsize=10)
#     #     ax1.set_ylabel('Forward', color='black', fontsize=10)
#     #     ax2.set_ylabel('Final PnL', color='black', fontsize=10)
#     #     ax1.tick_params(axis='both', which='major', labelsize=5, labelcolor='black')  # Adjust tick label size for ax1
#     #     ax2.tick_params(axis='both', which='major', labelsize=5, labelcolor='black')  # Adjust tick label size for ax2
#     #
#     #     plt.title('Forward and Final PnL Over Time')
#     #
#     #     # Remove legends
#     #     ax1.get_legend().remove()
#     #     ax2.get_legend().remove()
#     #
#     #     by_buffer = io.BytesIO()
#     #     plt.savefig(by_buffer, format='png')
#     #     plt.close()
#     #
#     #     img = Image(by_buffer)
#     #     img.anchor = 'A1'
#     #     ws.add_image(img)