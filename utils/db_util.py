import mysql.connector
import pandas as pd
from config import DB_CONFIG

def get_connection():
    """Buat koneksi MySQL menggunakan config.py"""
    return mysql.connector.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        port=DB_CONFIG['port'],
        charset=DB_CONFIG['charset']
    )

def get_unique_feeders():
    """Ambil list feeder unik dari tabel data_bebanrst"""
    conn = get_connection()
    query = "SELECT DISTINCT feeder FROM data_bebanrst ORDER BY feeder"
    df = pd.read_sql(query, conn)
    conn.close()
    return df['feeder'].tolist()

def get_historical_data(feeder, start_date, end_date):
    """Ambil data historis feeder dalam format long dengan jam HH:00"""
    conn = get_connection()
    
    # Ambil semua jam 00-23
    jam_cols = [f"{str(h).zfill(2)}_00" for h in range(0,24)]

    if feeder == "All Feeders":
        query = f"""
        SELECT tanggal, feeder, {', '.join([f'`{c}`' for c in jam_cols])}
        FROM data_bebanrst
        WHERE tanggal BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY tanggal, feeder
        """
    else:
        query = f"""
        SELECT tanggal, feeder, {', '.join([f'`{c}`' for c in jam_cols])}
        FROM data_bebanrst
        WHERE feeder = '{feeder}' AND tanggal BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY tanggal
        """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    # ubah dari wide ke long supaya setiap jam jadi row
    df_long = df.melt(
        id_vars=['tanggal', 'feeder'], 
        value_vars=jam_cols,
        var_name='jam', value_name='arus'
    )
    
    # Sorting: tanggal dulu, baru jam
    df_long['jam_order'] = df_long['jam'].apply(lambda x: int(x.split('_')[0])*60)
    df_long = df_long.sort_values(by=['tanggal', 'jam_order']).drop(columns=['jam_order'])
    
    # Buat datetime gabungan tanggal + jam (selalu menit 00)
    df_long['datetime'] = pd.to_datetime(
        df_long['tanggal'].astype(str) + ' ' +
        df_long['jam'].str.replace('_', ':')
    )
    
    return df_long
