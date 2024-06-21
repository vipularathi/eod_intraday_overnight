import logging
import os
import sys
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler

import pandas as pd
import pytz
from dateutil.relativedelta import relativedelta

root_dir = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(root_dir, 'logs/')
dirs = [logs_dir]
status = [os.makedirs(_dir, exist_ok=True) for _dir in dirs if not os.path.exists(_dir)]

now = datetime.now()
# today_date = now.date() #use this
today_date = datetime.strptime('21-jun-24', '%d-%b-%y').date()
print('today date is', today_date)
yesterday = today_date - timedelta(days=1)
print('yesterday date is', yesterday)
tomorrow = today_date + timedelta(days=1)
print('tomrw date is', tomorrow)

def define_logger():
    # Logging Definitions
    log_lvl = logging.DEBUG
    console_log_lvl = logging.INFO
    _logger = logging.getLogger('arathi')
    # logger.setLevel(log_lvl)
    _logger.setLevel(console_log_lvl)
    log_file = os.path.join(logs_dir, f'logs_arathi_{datetime.now().strftime("%Y%m%d")}.log')
    handler = TimedRotatingFileHandler(log_file, when='D', delay=True)
    handler.setLevel(log_lvl)
    console = logging.StreamHandler(stream=sys.stdout)
    console.setLevel(console_log_lvl)
    # formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')  #NOSONAR
    # formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(funcName)s %(message)s')
    formatter = logging.Formatter('%(asctime)s %(levelname)s <%(funcName)s> %(message)s')
    handler.setFormatter(formatter)
    console.setFormatter(formatter)
    _logger.addHandler(handler)  # Comment to disable file logs
    _logger.addHandler(console)
    # logger.propagate = False  # Removes AWS Level Logging as it tracks root propagation as well
    return _logger


logger = define_logger()