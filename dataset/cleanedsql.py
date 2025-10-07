import re
import os

# --- PATH ---
BASE_DIR = r"D:\Magang\Forecast Arus"
INPUT_FILE = os.path.join(BASE_DIR, "data_new.sql")
OUTPUT_FILE = os.path.join(BASE_DIR, "fixed_data.sql")

DB_NAME = "forecast_db"
TABLE_NAME = "data_bebanrst"

def fix_sql_file():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        sql_text = f.read()

    # 1. Perbaiki nama kolom ganda ``00_15`` -> `00_15`
    sql_text = re.sub(r"``(\d+_\d+)``", r"`\1`", sql_text)

    # 2. Cari kolom dari INSERT
    match = re.search(r"INSERT INTO\s+`?\w+`?\s*\((.*?)\)\s*VALUES", sql_text, re.S | re.I)
    if not match:
        raise ValueError("Kolom INSERT tidak ditemukan!")

    columns_raw = match.group(1)
    columns = [c.strip(" `") for c in columns_raw.split(",")]
    num_cols = len(columns)
    print(f"✅ Jumlah kolom terdeteksi: {num_cols}")

    # 3. Ambil semua VALUES
    values_blocks = re.findall(r"\((.*?)\)", sql_text.split("VALUES", 1)[1], re.S)

    fixed_values = []
    for i, block in enumerate(values_blocks, start=1):
        parts = re.split(r",(?![^']*'\s*,)", block)  # split by koma yg bukan di dalam string
        parts = [p.strip() for p in parts]
        if len(parts) != num_cols:
            print(f"⚠️ Baris {i}: Jumlah values {len(parts)} ≠ {num_cols} kolom")
        fixed_values.append("(" + ", ".join(parts) + ")")

    # 4. Header SQL (DB, Table, Charset)
    header = f"""
-- Auto-generated SQL (UTF-8)
CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `{DB_NAME}`;

DROP TABLE IF EXISTS `{TABLE_NAME}`;
CREATE TABLE `{TABLE_NAME}` (
  `id` INT PRIMARY KEY,
  `feeder_pkey` VARCHAR(50),
  `gardu_induk` VARCHAR(100),
  `t_no` VARCHAR(10),
  `t_primary` VARCHAR(10),
  `t_secondary` VARCHAR(10),
  `t_daya` VARCHAR(20),
  `kms` VARCHAR(20),
  `feeder` VARCHAR(100),
  `mvcell` VARCHAR(100),
  `pelanggan` VARCHAR(100),
  `kelas` VARCHAR(10),
  `l/r` VARCHAR(10),
  `inom` VARCHAR(50),
  `iset` VARCHAR(50),
  `up3` VARCHAR(50),
  `name` VARCHAR(50),
  `tanggal` DATE,
"""
    # tambahkan semua jam
    for h in range(0, 24):
        for m in ["00","15","30","45"]:
            col = f"{h:02d}_{m}"
            header += f"  `{col}` FLOAT,\n"
    header += "  `23_59` FLOAT,\n"
    header += """  `max_siang` FLOAT,
  `avg_siang` FLOAT,
  `max_malam` FLOAT,
  `avg_malam` FLOAT,
  `bp_koinsiden` FLOAT,
  `bp_diversity_s` FLOAT,
  `bp_diversity_m` FLOAT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

    # 5. Rekonstruksi INSERT
    insert_header = f"INSERT INTO `{TABLE_NAME}` ({', '.join('`'+c+'`' for c in columns)}) VALUES\n"
    new_sql = header + "\n" + insert_header + ",\n".join(fixed_values) + ";"

    # 6. Simpan hasil
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(new_sql)

    print(f"✅ File SQL sudah diperbaiki → {OUTPUT_FILE}")

if __name__ == "__main__":
    fix_sql_file()
