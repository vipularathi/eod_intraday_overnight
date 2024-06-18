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

# Function to simulate calculation of final_pnl and use_strike
def calculate_values(current_time):
    # Placeholder for actual calculations
    final_pnl = np.random.randn()  # Example calculation
    use_strike = np.random.randn()  # Example calculation
    return final_pnl, use_strike

# 2. Update the DataFrame Row by Row
for i, row in df.iterrows():
    current_time = row['time']
    final_pnl, use_strike = calculate_values(current_time)
    df.loc[i, 'final_pnl'] = final_pnl
    df.loc[i, 'use_strike'] = use_strike

    # 3. Save the plot as an image file
    plt.figure(figsize=(12, 6))
    plt.plot(df['time'][:i+1], df['final_pnl'][:i+1], label='final_pnl')
    plt.plot(df['time'][:i+1], df['use_strike'][:i+1], label='use_strike')
    plt.xlabel('Time')
    plt.ylabel('Values')
    plt.legend()
    plt.title('Final PnL and Use Strike vs Time')
    plt.grid(False)
    plt.savefig('plot.png')
    plt.close()

    # 4. Wait for 1 second before updating the plot again
    time.sleep(1)