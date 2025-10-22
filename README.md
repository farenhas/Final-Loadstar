# Prediksi Arus PLN

## Setup Project

1. **Buat dan aktifkan virtual environment**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
# .\.venv\Scripts\activate.bat  # Windows CMD
# source .venv/bin/activate     # Linux/macOS
```

2. **Install dependencies**
```powershell
pip install -r requirements.txt
```

3. **Buat folder models dan masukkan file .pkl**

    disini masukin model_labang dan model_Tragah.pkl

2. **Run**
```powershell
streamlit run app_modern.py
```

