# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# from datetime import datetime, timedelta
#
# #try1
# # 1. Create the DataFrame
# start_time = datetime.strptime('09:15:59', '%H:%M:%S')
# end_time = datetime.strptime('15:29:59', '%H:%M:%S')
# time_range = pd.date_range(start=start_time, end=end_time, freq='T')
# df = pd.DataFrame(time_range, columns=['time'])
# df['final_pnl'] = np.nan
# df['use_strike'] = np.nan
#
# # Function to simulate calculation of final_pnl and use_strike
# def calculate_values(current_time):
#     # Placeholder for actual calculations
#     final_pnl = np.random.randn()  # Example calculation
#     use_strike = np.random.randn()  # Example calculation
#     return final_pnl, use_strike
#
# # 2. Update the DataFrame Row by Row
# for i, row in df.iterrows():
#     current_time = row['time']
#     final_pnl, use_strike = calculate_values(current_time)
#     df.loc[i, 'final_pnl'] = final_pnl
#     df.loc[i, 'use_strike'] = use_strike
#
#     # 3. Plot the Data
#     if i % 10 == 0:  # Update the plot every 10 minutes for example
#         plt.figure(figsize=(12, 6))
#         plt.plot(df['time'][:i+1], df['final_pnl'][:i+1], label='final_pnl')
#         plt.plot(df['time'][:i+1], df['use_strike'][:i+1], label='use_strike')
#         plt.xlabel('Time')
#         plt.ylabel('Values')
#         plt.legend()
#         plt.title('Final PnL and Use Strike vs Time')
#         plt.grid(True)
#         plt.show()
#         plt.pause(0.1)

# #try2
# import pandas as pd
# import numpy as np
# from datetime import datetime, timedelta, time
# import json
# from string import Template
#
# # 1. Create the DataFrame
# # start_time = datetime.strptime('09:15:59', '%H:%M:%S')
# # end_time = datetime.strptime('15:29:59', '%H:%M:%S')
# start_time = time(hour=9, minute=15, second=59)
# end_time = time(hour=15, minute=29, second=59)
# # time_range = pd.date_range(start=start_time, end=end_time, freq='T')
# time_range = pd.date_range(start=datetime.combine(datetime.today(), start_time),
#                            end=datetime.combine(datetime.today(), end_time),
#                            freq='T')
# # df = pd.DataFrame(time_range, columns=['time'])
# # df['time'] = df['time'].dt.strftime('%H:%M:%S')
# df = pd.DataFrame({'time': time_range.time})
# print(df)
# df['final_pnl'] = np.nan
# df['use_strike'] = np.nan
#
# # Function to simulate calculation of final_pnl and use_strike
# def calculate_values(current_time):
#     final_pnl = np.random.randn()
#     use_strike = np.random.randn()
#     return final_pnl, use_strike
#
# # Update the DataFrame with calculated values
# for i in range(len(df)):
#     current_time = df.loc[i, 'time']
#     final_pnl, use_strike = calculate_values(current_time)
#     df.loc[i, 'final_pnl'] = final_pnl
#     df.loc[i, 'use_strike'] = use_strike
#
# # Prepare the data for Highcharts
# data = [
#     [int(df.loc[i, 'time'].timestamp() * 1000), df.loc[i, 'final_pnl'], df.loc[i, 'use_strike']]
#     for i in range(len(df))
# ]
#
# # Create the initial HTML template for Highcharts using string.Template
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
#                             setInterval(addPoint, 1000); // Update every second
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
#                     name: 'Use Strike',
#                     data: []
#                 }]
#             });
#         });
#     </script>
# </body>
# </html>
# """)
#
# # Generate the final HTML content
# html_content = html_template.substitute(data=json.dumps(data))
#
# # Write the HTML content to a file
# with open('dynamic_plot.html', 'w') as file:
#     file.write(html_content)
#
# print("HTML file 'dynamic_plot.html' created successfully.")

#try3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
import json
from string import Template

# # 1. Create the DataFrame
# start_time = time(hour=9, minute=15, second=59)
# end_time = time(hour=15, minute=29, second=59)
# time_range = pd.date_range(start=datetime.combine(datetime.today(), start_time),
#                            end=datetime.combine(datetime.today(), end_time),
#                            freq='T')
# time_range = time_range - time_range[0]
# df = pd.DataFrame({'time': time_range.time})
# print(df)
# df['final_pnl'] = np.nan
# df['use_strike'] = np.nan
#
# # Function to simulate calculation of final_pnl and use_strike
# def calculate_values(current_time):
#     final_pnl = np.random.randn()
#     use_strike = np.random.randn()
#     return final_pnl, use_strike
#
# # Update the DataFrame with calculated values
# for i in range(len(df)):
#     current_time = df.loc[i, 'time']
#     final_pnl, use_strike = calculate_values(current_time)
#     df.loc[i, 'final_pnl'] = final_pnl
#     df.loc[i, 'use_strike'] = use_strike
#
# # Prepare the data for Highcharts
# data = [
#     [int(df.loc[i, 'time'].total_seconds() * 1000), df.loc[i, 'final_pnl'], df.loc[i, 'use_strike']]
#     for i in range(len(df))
# ]
#
# # Create the initial HTML template for Highcharts using string.Template
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
#                             setInterval(addPoint, 1000); // Update every second
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
#                     name: 'Use Strike',
#                     data: []
#                 }]
#             });
#         });
#     </script>
# </body>
# </html>
# """)
#
# # Generate the final HTML content
# html_content = html_template.substitute(data=json.dumps(data))
#
# # Write the HTML content to a file
# with open('dynamic_plot.html', 'w') as file:
#     file.write(html_content)
#
# print("HTML file 'dynamic_plot.html' created successfully.")

#try4
# import pandas as pd
# import numpy as np
# from datetime import datetime, timedelta, time
# import json
# from string import Template
#
# # 1. Create the DataFrame
# start_time = time(hour=9, minute=15, second=59)
# end_time = time(hour=15, minute=29, second=59)
# time_range = pd.date_range(start=datetime.combine(datetime.today(), start_time),
#                            end=datetime.combine(datetime.today(), end_time),
#                            freq='T')
# df = pd.DataFrame({'time': time_range.strftime('%H:%M:%S')})
# print(df)
# df['final_pnl'] = np.nan
# df['use_strike'] = np.nan
#
# # Function to simulate calculation of final_pnl and use_strike
# def calculate_values(current_time):
#     final_pnl = np.random.randn()
#     use_strike = np.random.randn()
#     return final_pnl, use_strike
#
# # Update the DataFrame with calculated values
# for i in range(len(df)):
#     current_time = df.loc[i, 'time']
#     final_pnl, use_strike = calculate_values(current_time)
#     df.loc[i, 'final_pnl'] = final_pnl
#     df.loc[i, 'use_strike'] = use_strike
#
# # Prepare the data for Highcharts
# data = [
#     [pd.to_datetime(df.loc[i, 'time']).timestamp() * 1000, df.loc[i, 'final_pnl'], df.loc[i, 'use_strike']]
#     for i in range(len(df))
# ]
#
# # Create the initial HTML template for Highcharts using string.Template
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
#                             setInterval(addPoint, 1000); // Update every second
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
#                     name: 'Use Strike',
#                     data: []
#                 }]
#             });
#         });
#     </script>
# </body>
# </html>
# """)
#
# # Generate the final HTML content
# html_content = html_template.substitute(data=json.dumps(data))
#
# # Write the HTML content to a file
# with open('dynamic_plot.html', 'w') as file:
#     file.write(html_content)
#
# print("HTML file 'dynamic_plot.html' created successfully.")

# #try5
# import pandas as pd
# import numpy as np
# from datetime import datetime, timedelta, time
# import json
# from string import Template
#
# # 1. Create the DataFrame
# start_time = time(hour=9, minute=15, second=59)
# end_time = time(hour=15, minute=29, second=59)
# time_range = pd.date_range(start=datetime.combine(datetime.today(), start_time),
#                            end=datetime.combine(datetime.today(), end_time),
#                            freq='T')
# df = pd.DataFrame({'time': time_range.strftime('%H:%M:%S')})
# df['final_pnl'] = np.nan
# df['use_strike'] = np.nan
#
# # Function to simulate calculation of final_pnl and use_strike
# def calculate_values(current_time):
#     final_pnl = np.random.randn()
#     use_strike = np.random.randn()
#     return final_pnl, use_strike
#
# # Update the DataFrame with calculated values
# for i in range(len(df)):
#     current_time = df.loc[i, 'time']
#     final_pnl, use_strike = calculate_values(current_time)
#     df.loc[i, 'final_pnl'] = final_pnl
#     df.loc[i, 'use_strike'] = use_strike
#
# # Prepare the data for Highcharts
# data = [
#     [pd.to_datetime(df.loc[i, 'time']).timestamp() * 1000, df.loc[i, 'final_pnl'], df.loc[i, 'use_strike']]
#     for i in range(len(df))
# ]
#
# # Create the initial HTML template for Highcharts using string.Template
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
#                             setInterval(addPoint, 1000); // Update every second
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
#                     name: 'Use Strike',
#                     data: []
#                 }]
#             });
#         });
#     </script>
# </body>
# </html>
# """)
#
# # Generate the final HTML content
# html_content = html_template.substitute(data=json.dumps(data))
#
# # Write the HTML content to a file
# with open('dynamic_plot.html', 'w') as file:
#     file.write(html_content)
#
# print("HTML file 'dynamic_plot.html' created successfully.")

# #try6
# import pandas as pd
# import numpy as np
# from datetime import datetime, timedelta, time
# import json
# from string import Template
# import time
#
# from datetime import datetime, timedelta, time
# import time as t
# import json
# from string import Template
#
# # 1. Create the DataFrame
# start_time = time(hour=9, minute=15, second=59)
# end_time = time(hour=15, minute=29, second=59)
# time_range = pd.date_range(start=datetime.combine(datetime.today(), start_time),
#                            end=datetime.combine(datetime.today(), end_time),
#                            freq='T')
# df = pd.DataFrame({'time': time_range.strftime('%H:%M:%S')})
# df['final_pnl'] = np.nan
# df['use_strike'] = np.nan
#
# # Function to simulate calculation of final_pnl and use_strike
# def calculate_values(current_time):
#     final_pnl = np.random.randn()
#     use_strike = np.random.randn()
#     return final_pnl, use_strike
#
# # Update the DataFrame with calculated values
# for i in range(len(df)):
#     current_time = df.loc[i, 'time']
#     final_pnl, use_strike = calculate_values(current_time)
#     df.loc[i, 'final_pnl'] = final_pnl
#     df.loc[i, 'use_strike'] = use_strike
#
#     # Delay of 1 minute before calling calculate_values again
#     # t.sleep(5)
#
# # Prepare the data for Highcharts
# data = [
#     [pd.to_datetime(df.loc[i, 'time']).timestamp() * 1000, df.loc[i, 'final_pnl'], df.loc[i, 'use_strike']]
#     for i in range(len(df))
# ]
#
# # Create the initial HTML template for Highcharts using string.Template
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
#                             setInterval(addPoint, 1000); // Update every second
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
#                     name: 'Use Strike',
#                     data: []
#                 }]
#             });
#         });
#     </script>
# </body>
# </html>
# """)
#
# # Generate the final HTML content
# html_content = html_template.substitute(data=json.dumps(data))
#
# # Write the HTML content to a file
# with open('dynamic_plot1.html', 'w') as file:
#     file.write(html_content)
#
# print("HTML file 'dynamic_plot1.html' created successfully.")