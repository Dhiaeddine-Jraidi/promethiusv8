import mysql.connector
import pandas as pd
import numpy as np


db_config = {
    'host': 'mysql-63c7a58-jraididhiaeddine-6de9.a.aivencloud.com',
    'port': 20743,
    'user': 'avnadmin',
    'password': 'AVNS_2KsvbgR146fFQOsDE8m',
    'database': 'defaultdb',
    'ssl_ca': 'files/ca.pem',
    'use_pure': True
}

table_name1 = 'tradeswithfeatures_table'
table_name2 = 'probability_table'


def extract_trade_from_sql(table_name):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    select_query = f"SELECT * FROM {table_name}"
    cursor.execute(select_query)
    result_last_n_days = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(result_last_n_days, columns=columns)
    cursor.close()
    connection.close()
    return df


def create_table1():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name1} (
        trade_id VARCHAR(255),
        symbol VARCHAR(255),
        entry_time_str VARCHAR(255),
        side VARCHAR(255),
        entry_price FLOAT,
        last_price FLOAT,
        take_profit_percent FLOAT,
        stop_loss_percent FLOAT,
        exit_price_TP FLOAT,
        exit_price_SL FLOAT,
        timeframe VARCHAR(255),
        strategy VARCHAR(255),
        pnl FLOAT,
        period_hours FLOAT,
        entry_day_of_week VARCHAR(255),
        entry_hour INT,
        aroon_up FLOAT,
        aroon_down FLOAT,
        ema_short FLOAT,
        ema_middle FLOAT,
        ema_long FLOAT,
        rsi FLOAT,
        macd FLOAT,
        24h_volume FLOAT,
        current_price FLOAT,
        exit_time_str VARCHAR(255),
        trade_result VARCHAR(255),
        formated_exit_time VARCHAR(255),
        pct_decrease_6hours FLOAT,
        pct_increase_6hours FLOAT,
        pct_decrease_12hours FLOAT,
        pct_increase_12hours FLOAT,
        pct_decrease_24hours FLOAT,
        pct_increase_24hours FLOAT,
        pct_decrease_36hours FLOAT,
        pct_increase_36hours FLOAT,
        PRIMARY KEY (trade_id, symbol, entry_time_str)
    );
    """
    cursor.execute(create_table_query)
    connection.commit()
    connection.close()

def create_table2():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name2} (
        trade_id VARCHAR(255) PRIMARY KEY,
        probability FLOAT
    );
    """
    cursor.execute(create_table_query)
    connection.commit()
    connection.close()


def write_to_mysql(table_name, sql_columns, data):
    data = [float(item) if isinstance(item, np.float64) else item for item in data]
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    insert_query = f"""
    INSERT INTO {table_name} ({', '.join(sql_columns)}) VALUES ({', '.join(['%s' for _ in range(len(sql_columns))])})
    """
    try:
        cursor.execute(insert_query, tuple(data))
   
    except mysql.connector.errors.IntegrityError:
        print("integrity error !, passing", data[0])
        pass
    
    except Exception as e:
        print("another problem then integrity in writing data to sql !", e)
        
    connection.commit()
    connection.close()