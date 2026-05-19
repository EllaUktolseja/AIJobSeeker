import os
import joblib
import pandas as pd
import kagglehub
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# 1. DOWNLOAD DATASET SECARA OTOMATIS LEWAT LIBRARY KAGGLEHUB
print("Sedang mengunduh dataset IT/Tech langsung dari Kaggle...")
path_folder = kagglehub.dataset_download("PromptCloudHQ/us-technology-jobs-on-dicecom")

# Menemukan lokasi file .csv di dalam folder unduhan
file_csv = [os.path.join(path_folder, f) for f in os.listdir(path_folder) if f.endswith('.csv')][0]
df = pd.read_csv(file_csv)

# 2. SELEKSI DATA (Ambil sampel kolom Skills lowongan kerja)
df_clean = df[['skills']].dropna().head(4000)
X_train = df_clean['skills']

# Membuat label simulasi otomatis: 0 = Bidang Software/Data, 1 = Bidang Infrastructure/Hardware
kata_kunci_it = ['developer', 'java', 'python', 'react', 'sql', 'data', 'web', 'php']
y_train = X_train.apply(lambda x: 0 if any(kata in str(x).lower() for kata in kata_kunci_it) else 1)

print(f"Berhasil memproses {len(X_train)} baris data lowongan kerja.")

# 3. PIPELINE TRAINING MODEL MACHINE LEARNING
print("Memulai proses training model...")
model_pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(stop_words='english', min_df=2)),
    ('clf', MultinomialNB(alpha=0.1))
])

# Melatih otak AI
model_pipeline.fit(X_train, y_train)
print("Training Sukses!")

# 4. SIMPAN MODEL JADI (.PKL)
os.makedirs('model', exist_ok=True)
joblib.dump(model_pipeline, 'model/model_rekomendasi.pkl')
print("File 'model/model_rekomendasi.pkl' berhasil dibuat dan siap dipakai Flask!")
