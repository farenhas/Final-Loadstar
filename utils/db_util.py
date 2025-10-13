
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
    hanya kolom jam 01_00–23_00 dan 23_59.
    Ubah ke format long (time series), lalu ubah jam 23_59 menjadi 00_00 hari berikutnya.
    """
    conn = get_connection()

    # Kolom jam dari 01_00–23_00 dan tambahan 23_59
    jam_cols = [f"{str(h).zfill(2)}_00" for h in range(1, 24)] + ["23_59"]

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
            SELECT *,
                   ROW_NUMBER() OVER (PARTITION BY feeder ORDER BY tanggal DESC) AS rn
            FROM data_bebanrst
        ) ranked
        WHERE rn <= 32
        ORDER BY feeder, tanggal ASC
        """

    df = pd.read_sql(query, conn)
    conn.close()

    # Ubah ke format long
    df_long = df.melt(
        id_vars=['tanggal', 'feeder'],
        value_vars=jam_cols,
        var_name='jam', value_name='arus'
    )

    # Ubah '23_59' jadi 00_00 hari berikutnya
    mask_2359 = df_long['jam'] == '23_59'
    df_long.loc[mask_2359, 'tanggal'] = pd.to_datetime(df_long.loc[mask_2359, 'tanggal']) + pd.Timedelta(days=1)
    df_long['tanggal'] = pd.to_datetime(df_long['tanggal'])
    df_long.loc[mask_2359, 'jam'] = '00_00'

    # Gabungkan tanggal + jam jadi timestamp
    df_long['timestamp'] = pd.to_datetime(
        df_long['tanggal'].dt.strftime("%Y-%m-%d") + ' ' + df_long['jam'].str.replace('_', ':')
    )

    # Urutkan berdasarkan feeder dan waktu
    df_long = df_long.sort_values(by=['feeder', 'timestamp'])

    # Bersihkan kolom
    df_long = df_long[['timestamp', 'feeder', 'arus']].dropna().reset_index(drop=True)

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
