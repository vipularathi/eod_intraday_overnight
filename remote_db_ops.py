import pandas as pd
import sqlalchemy as sql
from assets import extract_ticker_info

execute_retry = True
db_name = 'algo_backend'
pg_user = 'postgres'
pg_password = 'Vivek001'
pg_host = '172.16.47.54'
pg_port = '5432'

engine_str = f'postgresql+psycopg2://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{db_name}'
pool = sql.create_engine(engine_str, pool_size = 100, max_overflow = 5, pool_recycle = 67, pool_timeout = 30, echo = None)
conn = pool.connect()

def from_master(sym):
    query = f'''
        select expiry from fnomaster
            where symbol = %(symbol)s
            and opt_type = 'XX'
            and extract(month from to_date(expiry, 'ddmonyyyy')) = extract(month from current_date)
    '''

    df =pd.read_sql_query(query, conn, params={'symbol': sym})
    return pd.to_datetime(df['expiry'][0]).strftime('%d-%b-%y')

def get_option_inst_id(ticker):
    sym, exp, strike, opt_type = extract_ticker_info(ticker)
    symb = sym.upper()
    expy = pd.to_datetime(exp).strftime('%d%b%Y').upper()
    # # a = strike
    # # b = opt_type
    query = f'''
        select * from fnomaster
        where symbol = %(symbol)s
        and exchange = 2
        and expiry = %(expiry)s
        and strike = %(strike)s
        and opt_type = %(opt_type)s
    '''
    df =pd.read_sql_query(query, conn, params={'symbol': symb, 'expiry': expy, 'strike':str(strike), 'opt_type': opt_type})
    inst_id = df['scripcode'].values[0]
    # print(inst_id)
    # print(type(inst_id))
    return inst_id

# sym = 'BANKNIFTY'
# fut_exp = from_master(sym)
# print(f'exp df is \n {fut_exp}, {type(fut_exp)}')

# todf = pd.to_datetime(exp_df['expiry'][0]).strftime('%Y-%m-%d')
# # todf = exp_df['expiry'][0].strptime('%Y-%m-%d')
# print(todf)
# get_inst_id_from_master('nifty', '20-jun-24', 20500, opt_type='CE')
# print(fg)
# res = get_option_inst_id('NIFTY20JUN2423450PE.NFO')
# print(res)