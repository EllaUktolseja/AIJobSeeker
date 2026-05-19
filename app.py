import os
import joblib
import pandas as pd
import kagglehub
from flask import Flask, jsonify, render_template, request
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# =====================================================================
# 1. LOAD MODEL & DATASET KAGGLE SAAT SERVER FLASK MENYALA
# =====================================================================
try:
    model_ai = joblib.load('model/model_rekomendasi.pkl')
    print("Model AI Rekomendasi Kerja berhasil diaktifkan!")
except FileNotFoundError:
    print("ERROR: File 'model_rekomendasi.pkl' tidak ada. Jalankan 'python train.py' dulu!")
    exit()

try:
    print("Memuat database lowongan kerja dari Kaggle...")
    path_folder = kagglehub.dataset_download("PromptCloudHQ/us-technology-jobs-on-dicecom")
    file_csv = [os.path.join(path_folder, f) for f in os.listdir(path_folder) if f.endswith('.csv')][0]
    
    df_kaggle = pd.read_csv(file_csv)[['jobtitle', 'company', 'joblocation_address', 'skills']].dropna()
    df_kaggle['skills_lower'] = df_kaggle['skills'].str.lower()
    print(f"Database siap! Menampung {len(df_kaggle)} lowongan kerja riil.")
except Exception as e:
    print(f"Gagal memuat dataset Kaggle: {e}")
    exit()


# =====================================================================
# 2. ROUTING WEB & API
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

        # B. Prediksi Rumpun Kerja Menggunakan Model AI .pkl (0 = IT, 1 = Engineering)
        prediksi_label = model_ai.predict([user_skills_clean])[0]
        probabilitas = model_ai.predict_proba([user_skills_clean])[0]
        
        # PERBAIKAN FIXED: Ambil nilai probabilitas sebagai angka skalar (bukan array NumPy)
        skor_keyakinan_ai = float(probabilitas[prediksi_label])

        # C. Saring Data Kaggle Berdasarkan Prediksi Rumpun Ilmu
        kata_kunci_it = ['developer', 'java', 'python', 'react', 'sql', 'data', 'web', 'php']
        kondisi_it = df_kaggle['skills_lower'].apply(lambda x: any(kata in str(x) for kata in kata_kunci_it))
        
        if prediksi_label == 0:
            df_terfilter = df_kaggle[kondisi_it].copy()
        else:
            df_terfilter = df_kaggle[~kondisi_it].copy()

        if df_terfilter.empty:
            df_terfilter = df_kaggle.copy()

        # D. Hitung Persentase Kedekatan Kata Kunci (Cosine Similarity)
        df_sampel = df_terfilter.head(30).copy()
        tfidf_vectorizer = model_ai.named_steps['tfidf']
        
        matrix_jobs = tfidf_vectorizer.transform(df_sampel['skills_lower'])
        matrix_user = tfidf_vectorizer.transform([user_skills_clean])
        
        skor_kemiripan_teks = cosine_similarity(matrix_user, matrix_jobs).flatten()
        
        # Kombinasikan skor prediksi model (40%) dengan kecocokan kata kunci eksak (60%)
        df_sampel['Final_Score'] = (skor_keyakinan_ai * 0.4) + (skor_kemiripan_teks * 0.6)

        # E. Urutkan dan Ambil 5 Rekomendasi Lowongan Kerja Teratas
        rekomendasi_teratas = df_sampel.sort_values(by='Final_Score', ascending=False).head(5)

        respons_json = []
        for _, row in rekomendasi_teratas.iterrows():
            persentase_match = max(45.0, min(99.0, float(row['Final_Score']) * 100))
            
            respons_json.append({
                'job_title': row['jobtitle'],
                'company': row['company'],
                'location': row['joblocation_address'],
                'skills_required': row['skills'],
                'match_score': f"{persentase_match:.1f}%"
            })
            
        return jsonify(respons_json)

    except Exception as e:
        # Menangkap error back-end secara aman dan mengembalikannya sebagai JSON murni
        print(f"Internal Server Error: {e}")
        return jsonify({'error': f'Terjadi kesalahan internal di server: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True)
