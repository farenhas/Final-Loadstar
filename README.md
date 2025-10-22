# Prediksi Arus PLN
## Prasyarat

- Python 3.8 atau lebih tinggi
- XAMPP (untuk database MySQL)
- File model Machine Learning (.pkl)

## Setup Project

### 1. Clone atau Download Project

Download project ini dan ekstrak ke direktori pilihan Anda.

### 2. Buat Virtual Environment
```bash
python -m venv .venv
```

### 3. Aktifkan Virtual Environment

**Windows PowerShell:**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows CMD:**
```cmd
.\.venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Siapkan Folder Models

Buat folder `models` di root direktori project dan masukkan semua file model (.pkl) ke dalamnya.

**Struktur direktori:**
```
project/
│
├── app_modern.py
├── configure.py
├── requirements.txt
├── models/
│   ├── feeder1_model.pkl
│   ├── feeder2_model.pkl
│   └── ...
└── .venv/
```

### 6. Setup Database

1. Jalankan **XAMPP** dan start service **Apache** dan **MySQL**
2. Buka file `configure.py` dan sesuaikan konfigurasi database jika diperlukan:
```python
   # Contoh konfigurasi database
   DB_HOST = "localhost"
   DB_USER = "root"
   DB_PASSWORD = ""
   DB_NAME = "nama_database"
```

### 7. Jalankan Aplikasi
```bash
streamlit run app_modern.py
```

Dashboard akan terbuka otomatis di browser pada alamat `http://localhost:8501`

## Troubleshooting

- **Virtual environment tidak aktif:** Pastikan Anda menjalankan perintah aktivasi sesuai OS
- **Module tidak ditemukan:** Jalankan ulang `pip install -r requirements.txt`
- **Database error:** Cek apakah MySQL di XAMPP sudah berjalan dan konfigurasi di `configure.py` sudah benar
- **Model tidak ditemukan:** Pastikan semua file .pkl ada di folder `models/`

## Fitur

- 📊 Prediksi arus listrik real-time
- 📈 Visualisasi data historis
- 🔄 Multiple feeder support
- 💾 Database integration
