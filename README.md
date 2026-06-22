# SISRU: Sistem Pakar Evaluasi Kualitas Tidur (Hybrid CF + RF)

**Sisru** (*Sistem Pakar Evaluasi Kualitas Tidur*) adalah aplikasi penunjang keputusan medis berbasis desktop yang menggunakan pendekatan **Hibrida** (*Hybrid*). Aplikasi ini menggabungkan penalaran pakar medis (*Rule-Based* Certainty Factor) dan pola statistik historis (*Data-Driven* Random Forest) untuk mengklasifikasikan kualitas tidur pengguna ke dalam tiga kategori: **BAIK**, **CUKUP**, atau **BURUK**.

Aplikasi ini dikembangkan dalam arsitektur **Client-Server** modular:
* **Frontend (Client)**: Aplikasi antarmuka desktop modern menggunakan pustaka `CustomTkinter` (Python).
* **Backend (Server)**: Layanan REST API menggunakan kerangka kerja `Flask` yang terhubung dengan basis data relasional `SQLite`.

---

## 🌟 Fitur Utama

* 🧠 **Diagnosis Hibrida (Late Fusion)**: Menggabungkan bobot tingkat kepastian Certainty Factor (bobot 0,4) dan probabilitas Random Forest (bobot 0,6) untuk hasil evaluasi yang presisi.
* ⚙️ **Explainable AI (Keterjelasan Logika)**: Menampilkan secara transparan aturan medis pakar yang terpicu (*fired rules*) saat proses inferensi Certainty Factor berlangsung.
* 📊 **Dashboard Hasil Interaktif**: Menampilkan visualisasi persentase kecenderungan hasil diagnosis menggunakan bilah kemajuan (*progress bar*) berwarna dinamis (hijau, kuning, merah).
* 📋 **Manajemen Riwayat Pasien**: Menyimpan setiap sesi konsultasi pasien secara persisten. Dilengkapi fitur untuk memuat riwayat lama, menghapus riwayat, serta **Ekspor CSV** (⭳) sebagai berkas laporan.
* ⚡ **Ringan & Efisien**: Berjalan secara lokal di komputer tanpa memerlukan spesifikasi perangkat keras yang tinggi (*laptop-friendly*).

---

## 📁 Struktur Proyek

```text
sisru/
├── backend/
│   ├── app.py             # Server Flask API utama (Port 5000)
│   ├── cf_engine.py       # Mesin inferensi Certainty Factor (16 Aturan Pakar)
│   ├── rf_model.py        # Modul pemanggil model Random Forest
│   ├── train_model.py     # Skrip pelatihan model Random Forest
│   ├── evaluate_hybrid.py # Skrip pengujian akurasi sistem komparatif
│   ├── requirements.txt   # Dependensi pustaka untuk Backend
│   └── rf_model.pkl       # Berkas model Random Forest hasil pelatihan
├── frontend/
│   ├── main_gui.py        # Antarmuka utama CustomTkinter (Desktop GUI)
│   └── requirements.txt   # Dependensi pustaka untuk Frontend
├── dataset/
│   └── Sleep_health_and_lifestyle_dataset.csv # Dataset latih (374 data)
├── data/
│   └── database.db        # Basis data SQLite (dibuat otomatis)
├── venv/                  # Virtual Environment Python (dibuat lokal)
└── README.md              # Dokumentasi ini
```

---

## 🛠️ Panduan Instalasi & Menjalankan Sistem

Ikuti panduan berikut langkah demi langkah menggunakan terminal **PowerShell** Anda di direktori utama proyek (`c:\Users\naufa\.gemini\antigravity-ide\scratch\sisru`):

### Langkah 1: Membuat Virtual Environment
Isolasi dependensi proyek agar tidak bentrok dengan Python global Anda:
```powershell
python -m venv venv
```

### Langkah 2: Menginstal Dependensi Pustaka
Instal semua pustaka pihak ketiga yang dibutuhkan oleh backend dan frontend:
```powershell
.\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\venv\Scripts\python.exe -m pip install -r frontend\requirements.txt
```

### Langkah 3: Melatih Model Machine Learning
Latih model Random Forest menggunakan dataset klinis yang tersedia sebelum menjalankan server:
```powershell
.\venv\Scripts\python.exe backend\train_model.py
```
*(Proses ini membaca berkas dataset di folder `dataset/` dan menghasilkan berkas model `backend/rf_model.pkl`)*

### Langkah 4: Menjalankan Aplikasi
Anda perlu membuka **dua** jendela terminal secara bersamaan (keduanya berada pada direktori utama proyek):

1. **Terminal 1: Jalankan Server Backend API**
   ```powershell
   .\venv\Scripts\python.exe backend\app.py
   ```
   *(Biarkan terminal ini berjalan. Server Flask akan aktif melayani REST API di `http://127.0.0.1:5000`)*

2. **Terminal 2: Jalankan Aplikasi Desktop GUI**
   ```powershell
   .\venv\Scripts\python.exe frontend\main_gui.py
   ```
   *(Jendela dashboard desktop Sisru akan terbuka dan siap untuk digunakan)*

---

## 📐 Prinsip Komputasi Hibrida
Skor diagnosis hibrida ditentukan melalui persamaan penggabungan berikut:
$$\text{Skor Gabungan}(k) = 0.4 \times CF_{score}(k) + 0.6 \times RF_{prob}(k)$$

Di mana:
* $k$ melambangkan kelas kualitas tidur (**BAIK**, **CUKUP**, atau **BURUK**).
* $CF_{score}(k)$ diperoleh dari hasil akumulasi Certainty Factor 16 aturan logika medis pakar.
* $RF_{prob}(k)$ merupakan probabilitas kelas dari model Random Forest yang diekstrak melalui fungsi `predict_proba`.
* Kelas dengan **skor gabungan tertinggi** dipilih sebagai hasil klasifikasi final.
