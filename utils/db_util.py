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

def get_historical_data(feeder=None):
    """
    Ambil 32 baris terakhir per feeder dari tabel data_bebanrst,
    lalu ubah ke format long (jam menjadi row).
    Jika feeder diberikan, ambil hanya feeder tersebut.
    """
    conn = get_connection()
    jam_cols = [f"{str(h).zfill(2)}_00" for h in range(24)]

    if feeder and feeder != "All Feeders":
        query = f"""
        SELECT tanggal, feeder, {', '.join([f'`{c}`' for c in jam_cols])}
        FROM (
            SELECT * FROM data_bebanrst
            WHERE feeder = '{feeder}'
            ORDER BY tanggal DESC
            LIMIT 32
        ) AS sub
        ORDER BY tanggal ASC
        """
    else:
        query = f"""
        SELECT tanggal, feeder, {', '.join([f'`{c}`' for c in jam_cols])}
        FROM (
            SELECT * ,
                   ROW_NUMBER() OVER (PARTITION BY feeder ORDER BY tanggal DESC) AS rn
            FROM data_bebanrst
        ) ranked
        WHERE rn <= 32
        ORDER BY feeder, tanggal ASC
        """

    df = pd.read_sql(query, conn)
    conn.close()

    df_long = df.melt(
        id_vars=['tanggal', 'feeder'],
        value_vars=jam_cols,
        var_name='jam', value_name='arus'
    )

    df_long['jam_order'] = df_long['jam'].apply(lambda x: int(x.split('_')[0]) * 60)
    df_long = df_long.sort_values(by=['feeder', 'tanggal', 'jam_order']).drop(columns=['jam_order'])

    df_long['timestamp'] = pd.to_datetime(
        df_long['tanggal'].astype(str) + ' ' + df_long['jam'].str.replace('_', ':')
    )

    # Rename agar seragam dengan app.py
    df_long = df_long.rename(columns={'datetime': 'timestamp'})

    return df_long

def load_data_from_db(feeder_name: str) -> pd.DataFrame:
    """
    Wrapper sederhana agar app.py bisa langsung memanggil data feeder
    tanpa mengubah struktur lama. 
    """
    df = get_historical_data(feeder_name)
    
    # pastikan kolom urut dan bersih
    df = df[['timestamp', 'arus']].dropna().sort_values('timestamp')
    df.reset_index(drop=True, inplace=True)
    return df
