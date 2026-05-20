# 1. Gunakan base image Python resmi yang ringan
FROM python:3.10-slim

# 2. Tentukan folder kerja di dalam container
WORKDIR /app

# 3. Copy file requirements terlebih dahulu (biar proses build lebih cepat lewat caching)
COPY requirements.txt .

# 4. Install semua library Python yang dibutuhkan
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy seluruh file proyek kamu ke dalam container
COPY . .

# 6. Informasikan bahwa container akan menggunakan port 5000
EXPOSE 5000

# 7. Perintah untuk menjalankan aplikasi Flask saat container dinyalakan
CMD ["python", "app.py"]