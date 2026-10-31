# Indonesian Data Job Market Intelligence - Streamlit Dashboard

Dashboard interaktif untuk memvisualisasikan dinamika pasar kerja talenta data di Indonesia (*Data Analyst*, *Data Engineer*, *Data Scientist*, dan *Machine Learning & AI*) yang dikumpulkan dari **Glints** dan **JobStreet**.

Aplikasi ini dibangun berdasarkan pedoman **[panduan_komprehensif_dashboard.md](../markdown/panduan_komprehensif_dashboard.md)** dengan menerapkan prinsip *Visual Hierarchy*, *Grid Alignment*, *Cognitive Load Reduction*, serta *WCAG Accessibility*.

---

## 🚀 Cara Menjalankan Dashboard

Pastikan environment Python aktif, lalu jalankan perintah berikut dari direktori utama proyek:

```bash
streamlit run dashboard/app.py
```

Dashboard akan otomatis terbuka di browser pada alamat default: `http://localhost:8501`.

---

## 📊 Struktur & Fitur Dashboard

Dashboard terdiri dari 5 modul navigasi tab utama yang memadukan pola **Executive Overview** dan **Analytical Deep-Dive**:

### 1. 📊 Ringkasan Eksekutif (Executive Overview)
- **Kartu Metrik KPI Tingkat 1:** Total Lowongan, Median Gaji Nasional, Rasio Transparansi Gaji, dan Total Keahlian Teknis Terpetakan.
- **Komposisi Profesi & Platform:** Sebaran lowongan per kelompok profesi berdasarkan platform sumber (Glints vs JobStreet).
- **Penyerapan Industri:** Peringkat sektor industri yang paling aktif merekrut talenta data.
- **Mode Kerja & Pengalaman:** Proporsi *On-site*, *Hybrid*, dan *Remote* serta distribusi jenjang pengalaman.

### 2. 💰 Analisis Gaji & Kompensasi (Salary Intelligence)
- **Ringkasan Kompensasi:** Nilai minimum, median, rata-rata, dan maksimum gaji bulanan yang dinormalisasi ke Rupiah.
- **Distribusi Gaji per Profesi:** Box plot interaktif dengan sebaran kuartil dan deteksi outlier.
- **Median Gaji per Jenjang:** Komparasi kompensasi dari *Entry-Level* hingga *Senior-Level*.
- **Tabel Sektor Industri:** Rerata dan rentang penawaran gaji per sektor industri nasional.

### 3. 🛠️ Kebutuhan Keahlian & Teknologi (Skills Intelligence)
- **Filter Kategori Keahlian:** *Programming Languages, BI & Visualization, Databases & Warehousing, Big Data & Cloud, Data Science & ML*.
- **Top 15 Keahlian Teknis:** Grafik penetrasi pasar (%) keahlian yang paling banyak dituntut perusahaan.
- **Komposisi Kategori:** Donut chart proporsi jenis keahlian teknis.
- **Matriks Keahlian per Profesi:** Heatmap relasi silang antara keahlian teknis teratas dan kelompok profesi data.

### 4. 🗺️ Sebaran Geografis & Industri (Regional Intelligence)
- **Konsentrasi Provinsi & Kota:** Peringkat wilayah penempatan lowongan kerja di Indonesia.
- **Matriks Industri vs Mode Kerja:** Komparasi adopsi kerja remote/hybrid di berbagai sektor industri.

### 5. 🔍 Eksplorasi Data Lowongan (Data Explorer & Export)
- **Pencarian Real-Time:** Filter lowongan berdasarkan kata kunci posisi, nama perusahaan, atau kota.
- **Tabel Interaktif:** Tautan langsung ke halaman asli lowongan (`job_url`) dan format Rupiah yang rapi.
- **Detail Keahlian Teknis:** Panel interaktif (*expander*) untuk memeriksa daftar lengkap keahlian teknis per lowongan terpilih.
- **Ekspor CSV:** Tombol unduh dataset hasil filter ke format `.csv`.

---

## ⚙️ Sumber Data & Ketahanan (Resilience)
Dashboard dilengkapi mekanisme **Dual Data-Source**:
1. **Prioritas Utama:** Membaca langsung dari basis data relasional **PostgreSQL** (`loker_data`).
2. **Fallback Otomatis:** Jika koneksi database offline atau tidak tersedia, aplikasi secara mulus memuat data dari file lokal terstandarisasi (`data/processed/jobs_master.parquet` atau `.csv` dan `skills_master.parquet` atau `.csv`).
