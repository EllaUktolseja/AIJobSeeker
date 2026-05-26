import os
import joblib
import pandas as pd
import kagglehub
import re
import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity

# =====================================================================
# 1. SETTING HALAMAN & MODAL CSS (TEMA GELAP / MODERN SIMILAR TO FLASK)
# =====================================================================
st.set_page_config(
    page_title="JobMatch AI — Rekomendasi Pekerjaan",
    page_icon="⚡",
    layout="centered"
)

# Custom Tokenizer (Wajib sama persis dengan yang di train.py)
def custom_tokenizer(text):
    if not text:
        return []
    text = re.sub(r'[\,\;\/]', ' ', text.lower())
    tokens = re.findall(r'\b[a-zA-Z0-9_\-\.]+\b|\b[a-zA-Z]\+\+|\b[a-zA-Z]#', text)
    return [t.strip() for t in tokens if t.strip() and t.strip() != '.']


# =====================================================================
# 2. LOAD MODEL & DATASET (MENGGUNAKAN CACHE AGAR TIDAK DOWNLOAD TERUS)
# =====================================================================
@st.cache_resource
def load_model_ai():
    try:
        model = joblib.load('model/model_rekomendasi.pkl')
        return model
    except FileNotFoundError:
        st.error("ERROR: File 'model_rekomendasi.pkl' tidak ditemukan di folder 'model/'. Jalankan 'train.py' dulu!")
        st.stop()

@st.cache_data
def load_kaggle_dataset():
    try:
        path_folder = kagglehub.dataset_download("PromptCloudHQ/us-technology-jobs-on-dicecom")
        file_csv = [os.path.join(path_folder, f) for f in os.listdir(path_folder) if f.endswith('.csv')][0]
        
        df = pd.read_csv(file_csv)[['jobtitle', 'company', 'joblocation_address', 'skills']].dropna()
        df['skills_lower'] = df['skills'].str.lower()
        return df
    except Exception as e:
        st.error(f"Gagal memuat dataset Kaggle: {e}")
        st.stop()

# Memuat resource
model_ai = load_model_ai()
df_kaggle = load_kaggle_dataset()


# =====================================================================
# 3. TAMPILAN ANTARMUKA (UI) STREAMLIT
# =====================================================================
st.title("⚡ JobMatch AI")
st.subheader("Temukan pekerjaan IT impianmu berdasarkan keahlianmu")
st.write("Tuliskan keahlian teknis kamu, dan biarkan AI mencocokkannya dengan ratusan lowongan riil dari perusahaan teknologi.")

st.markdown("---")

# Input Area
st.markdown("**Deskripsikan keahlianmu**")
st.caption("💡 Ketik dalam **Bahasa Inggris** untuk hasil pencocokan paling akurat (dataset berasal dari lowongan AS).")

# Contoh Cepat menggunakan tombol kolom jika dibutuhkan
col_ex1, col_ex2 = st.columns(2)
with col_ex1:
    if st.button("💡 Contoh Data / ML"):
        st.session_state.skills_input = "Python programmer with experience in machine learning and SQL pipelines"
with col_ex2:
    if st.button("💡 Contoh Frontend"):
        st.session_state.skills_input = "Frontend developer skilled in React, TypeScript, HTML, CSS, and Tailwind"

# Text area untuk input skill
user_skills = st.text_area(
    label="Input Skills",
    label_visibility="collapsed",
    placeholder="Example: I am a junior coder. I love building web apps with JavaScript, React, HTML, and managing data using SQL databases.",
    value=st.session_state.get('skills_input', ''),
    key="skills_text_area",
    height=150
)

# Tombol Eksekusi
if st.button("🚀 Rekomendasikan Pekerjaan", type="primary"):
    if not user_skills.strip():
        st.error("Input keahlian tidak boleh kosong!")
    else:
        with st.spinner("Menganalisis keahlianmu dan mencocokkan dengan database Kaggle..."):
            try:
                user_skills_clean = user_skills.lower()

                # A. Prediksi Rumpun Kerja Menggunakan Model AI .pkl
                prediksi_label = model_ai.predict([user_skills_clean])[0]
                probabilitas = model_ai.predict_proba([user_skills_clean])[0]
                skor_keyakinan_ai = float(probabilitas[prediksi_label])

                # B. Salin Dataset
                df_sampel = df_kaggle.copy()
                
                # C. Hitung Kedekatan Kata Kunci Menggunakan Cosine Similarity
                tfidf_vectorizer = model_ai.named_steps['tfidf']
                matrix_jobs = tfidf_vectorizer.transform(df_sampel['skills_lower'])
                matrix_user = tfidf_vectorizer.transform([user_skills_clean])
                
                skor_kemiripan_teks = cosine_similarity(matrix_user, matrix_jobs).flatten()
                
                # D. Perhitungan Bonus Rumpun Kerja (.apply() method)
                kata_kunci_it = ['developer', 'java', 'python', 'react', 'sql', 'data', 'web', 'php']
                
                def hitung_bonus(row):
                    is_it_job = any(kata in str(row['skills_lower']) for kata in kata_kunci_it)
                    if (prediksi_label == 0 and is_it_job) or (prediksi_label == 1 and not is_it_job):
                        return 0.2
                    return 0.0

                series_bonus = df_sampel.apply(hitung_bonus, axis=1)

                # E. Kombinasi Bobot Nilai Akhir (Hybrid Score)
                df_sampel['Final_Score'] = (skor_kemiripan_teks * 0.5) + \
                                           (skor_keyakinan_ai * 0.3) + \
                                           (series_bonus * 0.2)

                # F. Urutkan Nilai Tertinggi dan Ambil 5 Rekomendasi Teratas
                rekomendasi_teratas = df_sampel.sort_values(by='Final_Score', ascending=False).head(5)

                # DISPLAY HASIL REKOMENDASI
                st.markdown("### 🔍 Rekomendasi untukmu")
                st.success(f"Berhasil menemukan kecocokan lowongan pekerjaan!")

                for _, row in rekomendasi_teratas.iterrows():
                    persentase_match = max(45.0, min(99.0, float(row['Final_Score']) * 100))
                    
                    # Tokenisasi skill agar rapi
                    raw_skills = str(row['skills'])
                    tokens = custom_tokenizer(raw_skills)
                    unique_skills = list(dict.fromkeys(tokens))
                    clean_skills = ", ".join(unique_skills[:6]).upper()
                    skills_display = clean_skills if clean_skills else raw_skills

                    # Menampilkan per Card Lowongan Kerja
                    with st.container():
                        st.markdown(
                            f"""
                            <div style="padding:15px; border-radius:10px; background-color:#1E1E1E; margin-bottom:15px; border-left: 5px solid #2ECC71;">
                                <h4 style="margin:0; color:#FFFFFF;">{row['jobtitle']}</h4>
                                <p style="margin:5px 0; color:#B2B2B2;">🏢 <b>{row['company']}</b> | 📍 {row['joblocation_address']}</p>
                                <p style="margin:5px 0; font-size:0.85em; color:#E0E0E0;"><b>Required Skills:</b> {skills_display}</p>
                                <span style="background-color:#2ECC71; color:white; padding:2px 8px; border-radius:5px; font-size:0.8em; font-weight:bold;">{persentase_match:.1f}% Match</span>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
            except Exception as e:
                st.error(f"Terjadi kesalahan internal: {e}")

st.markdown("---")
st.caption("Dibuat dengan ❤ — Dataset: Dice.com Job Listings (Kaggle)")
