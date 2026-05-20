import os
import joblib
import pandas as pd
import kagglehub
import re  # Untuk kebutuhan regex custom tokenizer
from flask import Flask, jsonify, render_template, request
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# =====================================================================
# 1. DEKLARASI CUSTOM TOKENIZER (WAJIB SAMA PERSIS DENGAN DI TRAIN.PY)
# =====================================================================
def custom_tokenizer(text):
    if not text:
        return []
    # Ubah ke huruf kecil dan ganti koma/titik koma/garis miring menjadi spasi
    text = re.sub(r'[\,\;\/]', ' ', text.lower())
    # Ambil kata, pertahankan tanda spesial IT penting seperti C++, C#, .JS
    tokens = re.findall(r'\b[a-zA-Z0-9_\-\.]+\b|\b[a-zA-Z]\+\+|\b[a-zA-Z]#', text)
    # Bersihkan token kosong atau karakter titik tunggal
    return [t.strip() for t in tokens if t.strip() and t.strip() != '.']


# =====================================================================
# 2. LOAD MODEL & DATASET KAGGLE SAAT SERVER FLASK MENYALA
# =====================================================================
try:
    # Fungsi custom_tokenizer wajib dideklarasikan sebelum baris ini
    model_ai = joblib.load('model/model_rekomendasi.pkl')
    print("Model AI Rekomendasi Kerja berhasil diaktifkan!")
except FileNotFoundError:
    print("ERROR: File 'model_rekomendasi.pkl' tidak ada. Jalankan 'python train.py' dulu!")
    exit()

try:
    print("Memuat database lowongan kerja dari Kaggle...")
    path_folder = kagglehub.dataset_download("PromptCloudHQ/us-technology-jobs-on-dicecom")
    file_csv = [os.path.join(path_folder, f) for f in os.listdir(path_folder) if f.endswith('.csv')][0]
    
    # Ambil kolom esensial dan bersihkan data kosong
    df_kaggle = pd.read_csv(file_csv)[['jobtitle', 'company', 'joblocation_address', 'skills']].dropna()
    df_kaggle['skills_lower'] = df_kaggle['skills'].str.lower()
    print(f"Database siap! Menampung {len(df_kaggle)} lowongan kerja riil.")
except Exception as e:
    print(f"Gagal memuat dataset Kaggle: {e}")
    exit()


# =====================================================================
# 3. ROUTING WEB & API
# =====================================================================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/rekomendasi', methods=['POST'])
def rekomendasi_kerja():
    try:
        data_input = request.get_json()
        user_skills = data_input.get('user_skills', '')
        
        if not user_skills or not user_skills.strip():
            return jsonify({'error': 'Input keahlian tidak boleh kosong!'}), 400

        user_skills_clean = user_skills.lower()

        # A. Prediksi Rumpun Kerja Menggunakan Model AI .pkl
        prediksi_label = model_ai.predict([user_skills_clean])[0]
        probabilitas = model_ai.predict_proba([user_skills_clean])[0]
        skor_keyakinan_ai = float(probabilitas[prediksi_label])

        # B. Gunakan seluruh dataset Kaggle (Bukan cuma 50 teratas) untuk akurasi nyata
        df_sampel = df_kaggle.copy()
        
        # C. Hitung Kedekatan Kata Kunci Menggunakan Cosine Similarity
        tfidf_vectorizer = model_ai.named_steps['tfidf']
        matrix_jobs = tfidf_vectorizer.transform(df_sampel['skills_lower'])
        matrix_user = tfidf_vectorizer.transform([user_skills_clean])
        
        skor_kemiripan_teks = cosine_similarity(matrix_user, matrix_jobs).flatten()
        
        # D. Perhitungan Bonus Rumpun Kerja
        bonus_prediksi = []
        kata_kunci_it = ['developer', 'java', 'python', 'react', 'sql', 'data', 'web', 'php']
        
        for _, row in df_sampel.iterrows():
            is_it_job = any(kata in str(row['skills_lower']) for kata in kata_kunci_it)
            
            if (prediksi_label == 0 and is_it_job) or (prediksi_label == 1 and not is_it_job):
                bonus_prediksi.append(0.2)  # Bonus 20%
            else:
                bonus_prediksi.append(0.0)

        # E. Kombinasi Bobot Nilai Akhir (Hybrid Score)
        df_sampel['Final_Score'] = (skor_kemiripan_teks * 0.5) + \
                                   (skor_keyakinan_ai * 0.3) + \
                                   (pd.Series(bonus_prediksi, index=df_sampel.index) * 0.2)

        # F. Urutkan Nilai Tertinggi dan Ambil 5 Rekomendasi Teratas
        rekomendasi_teratas = df_sampel.sort_values(by='Final_Score', ascending=False).head(5)

        respons_json = []
        for _, row in rekomendasi_teratas.iterrows():
            persentase_match = max(45.0, min(99.0, float(row['Final_Score']) * 100))
            
            # Ekstrak token skill unik
            raw_skills = str(row['skills'])
            tokens = custom_tokenizer(raw_skills)
            unique_skills = list(dict.fromkeys(tokens))
            clean_skills = ", ".join(unique_skills[:6]).upper() # Batasi maksimal 6 skill teratas agar rapi di UI
            
            skills_display = clean_skills if clean_skills else raw_skills

            respons_json.append({
                'job_title': row['jobtitle'],
                'company': row['company'],
                'location': row['joblocation_address'],
                'skills_required': skills_display,
                'match_score': f"{persentase_match:.1f}%"
            })

        return jsonify(respons_json)

    except Exception as e:
        print(f"Internal Server Error: {e}")
        return jsonify({'error': f'Terjadi kesalahan internal di server: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)