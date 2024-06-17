import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import time

# 1. Create the DataFrame
start_time = datetime.strptime('09:15:59', '%H:%M:%S')
end_time = datetime.strptime('15:29:59', '%H:%M:%S')
time_range = pd.date_range(start=start_time, end=end_time, freq='T')
df = pd.DataFrame(time_range, columns=['time'])
df['final_pnl'] = np.nan
df['use_strike'] = np.nan
df['nifty'] = np.nan
df['banknifty'] = np.nan
df['finnifty'] = np.nan
df['midcapnifty'] = np.nan

# Function to simulate calculation of final_pnl and use_strike
def calculate_values(current_time):
    # Placeholder for actual calculations
    final_pnl = np.random.randn()  # Example calculation
    use_strike = np.random.randn()  # Example calculation
    nifty = np.random.randn()  # Example calculation
    banknifty = np.random.randn()  # Example calculation
    finnifty = np.random.randn()  # Example calculation
    midcapnifty = np.random.randn()  # Example calculation
    return final_pnl, use_strike, nifty, banknifty, finnifty, midcapnifty

# 2. Update the DataFrame Row by Row
for i, row in df.iterrows():
    current_time = row['time']
    final_pnl, use_strike, nifty, banknifty, finnifty, midcapnifty = calculate_values(current_time)
    df.loc[i, 'final_pnl'] = final_pnl
    df.loc[i, 'use_strike'] = use_strike
    df.loc[i, 'nifty'] = nifty
    df.loc[i, 'banknifty'] = banknifty
    df.loc[i, 'finnifty'] = finnifty
    df.loc[i, 'midcapnifty'] = midcapnifty

    # 3. Save the plots as image files
    plt.figure(figsize=(6, 4))
    plt.subplot(221)
    plt.plot(df['time'][:i+1], df['nifty'][:i+1], label='Nifty')
    plt.xlabel('Time')
    plt.ylabel('Values')
    plt.legend()
    plt.title('Nifty')

    plt.subplot(222)
    plt.plot(df['time'][:i+1], df['banknifty'][:i+1], label='Banknifty')
    plt.xlabel('Time')
    plt.ylabel('Values')
    plt.legend()
    plt.title('Banknifty')

    plt.subplot(223)
    plt.plot(df['time'][:i+1], df['finnifty'][:i+1], label='Finnifty')
    plt.xlabel('Time')
    plt.ylabel('Values')
    plt.legend()
    plt.title('Finnifty')

    plt.subplot(224)
    plt.plot(df['time'][:i+1], df['midcapnifty'][:i+1], label='Midcapnifty')
    plt.xlabel('Time')
    plt.ylabel('Values')
    plt.legend()
    plt.title('Midcapnifty')

    plt.savefig('plots.png')
    plt.close()

    # 4. Wait for 1 second before updating the plots again
    time.sleep(1)