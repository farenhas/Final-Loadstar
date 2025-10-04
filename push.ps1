# === Clean Initial Push Script - New Repo ===

Write-Host "=== Clean Initial Push Script to New Repo ===" -ForegroundColor Cyan

# 1. Pastikan virtual environment dimatikan
if ($env:VIRTUAL_ENV) {
    Write-Host "Virtual environment masih aktif. Jalankan 'deactivate' dulu." -ForegroundColor Red
    exit
}

# 2. Hapus repo Git lama jika ada
if (Test-Path ".git") {
    Write-Host "Menghapus repo Git lama..."
    Remove-Item -Recurse -Force .git
}

# 3. Buat .gitignore standar
Write-Host "Membuat .gitignore..."
@"
# Virtual environment
.venv/
venv/
env/
ENV/

# Dataset
dataset/

# Python cache
__pycache__/
*.py[cod]
*.pyo

# Model artifacts
*.pkl
*.h5
*.sav

# Folder models
models/

# Streamlit
.streamlit/

# OS junk
.DS_Store
Thumbs.db
"@ | Out-File -Encoding UTF8 .gitignore

# 4. Inisialisasi repo baru
Write-Host "Inisialisasi repo Git baru..."
git init

# 5. Tambahkan file bersih
Write-Host "Menambahkan file penting..."
git add .

# 6. Commit awal
Write-Host "Membuat initial commit..."
git commit -m "Initial clean commit - exclude models and venv"

# 7. Set branch utama
git branch -M main

# 8. Set remote baru
git remote add origin https://github.com/farenhas/Prediksi-Arus.git

# 9. Push pertama
Write-Host "Push ke GitHub..."
git push -u origin main

Write-Host "`nSelesai! Repo baru telah dibuat, commit bersih, dan push ke remote baru." -ForegroundColor Green
