# Blueprint -- IHSG Predictor (Django + Prophet)

## 1. Visi & Tujuan

Platform prediksi IHSG berbasis web yang memadukan analisis data historis dan machine learning (Prophet) untuk memberikan proyeksi indeks saham secara real-time dengan visualisasi yang informatif.

---

## 2. Arsitektur Sistem

```
[Browser] --> [Django] --> [PostgreSQL] 
                │
                ├── Prophet Model (.joblib)
                └── Celery + Redis (retrain task)
```

### Stack Utama
| Layer        | Teknologi                |
|------------- |--------------------------|
| Backend      | Django 5.x               |
| DB           | PostgreSQL               |
| Cache/Queue  | Redis + Celery            |
| ML Model     | Prophet (joblib)          |
| Frontend     | Django Templates + HTMX + Tailwind CSS |
| API          | Django REST Framework (opsional)       |
| Chart        | Chart.js / ApexCharts                  |


### Struktur Direktori
```
ihsg_project/
├── config/                  # settings, urls, wsgi
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── dashboard/           # halaman utama & visualisasi
│   ├── prediction/          # logika loading model, prediksi
│   ├── historical/          # data historis IHSG & upload CSV
│   └── training/            # retrain pipeline & model versioning
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── templates/
│   ├── base.html
│   ├── dashboard/
│   ├── prediction/
│   └── historical/
├── media/
│   └── models/              # lokasi .joblib
├── docker-compose.yml
├── Dockerfile
└── Makefile
```

---

## 3. Entity Relationship

```
HistoricalData
  ├── id, date (ds), close (y)
  ├── source (manual/csv)
  └── unique: date

PredictionResult
  ├── id, date, yhat, yhat_lower, yhat_upper
  ├── model_version, created_at
  └── unique (date, model_version)

UploadedCSV
  ├── id, file, uploaded_at
  └── status (pending/done/error)
```

---

## 4. Alur Data

1. **Manual / CSV Upload** --> HistoricalData table (validated)
2. **Trigger Prediksi** --> load `ihsg_prophet_model.joblib`
3. **Model** --> `make_future_dataframe(periods=N)` --> `predict()`
4. **Hasil** --> simpan ke PredictionResult
5. **Dashboard** --> query DB --> render chart & tabel
6. **Retrain Pipeline** (periodik) --> fetch Yahoo Finance --> preprocess --> train Prophet --> save `.joblib` baru

---

## 5. Halaman / Route

| URL                        | View               | Deskripsi                            |
|----------------------------|--------------------|--------------------------------------|
| `/`                        | DashboardIndex     | Grafik IHSG + prediksi + indikator   |
| `/prediction/`             | PredictionView     | Trigger & lihat hasil prediksi       |
| `/historical/`             | HistoricalView     | Tabel data historis + upload CSV     |
| `/historical/upload/`      | UploadCSVView      | Form upload CSV                      |
| `/about/`                  | AboutView          | Info model & metodologi              |
| `/training/`               | TrainingView       | Trigger retrain & lihat riwayat model |

---

## 6. Design System (UI/UX)

**Tema**: Financial dark (dark navy background, aksen emas/hijau)
**Font**: Inter (headline) + JetBrains Mono (data/tabel)
**Warna**:
- Background: `#0f172a` (slate-900)
- Card: `#1e293b` (slate-800)
- Aksen naik (bullish): `#22c55e` (green-500)
- Aksen turun (bearish): `#ef4444` (red-500)
- Aksen emas/neutral: `#f59e0b` (amber-500)
- Text primary: `#f8fafc` (slate-50)
- Text secondary: `#94a3b8` (slate-400)

**Komponen**:
- Navbar sticky dengan glassmorphism
- Card metrics (IHSG saat ini, perubahan, prediksi)
- Area chart interaktif (zoom, crosshair)
- Data table responsif & searchable
- Loading skeleton untuk prediksi

---

## 7. Constraints & Asumsi

- Model Prophet di-retrain secara berkala via pipeline offline batch learning (incremental)
- Data historis minimal 2 tahun untuk prediksi akurat, di-fresh dari Yahoo Finance tiap retrain
- Prediksi bersifat indikatif, bukan rekomendasi investasi
- Deployment target: Cloudflare Workers (Django app di-adjust untuk Workers runtime) | *saat ini masih Django standalone*

---

## 8. Risk & Mitigation

| Risk                          | Mitigation                          |
|-------------------------------|-------------------------------------|
| Model Prophet lambat load     | Cache model di Redis setelah load pertama |
| CSV upload gagal format       | Validasi ketat + preview sebelum insert   |
| Data historis kosong          | Seed data dari Yahoo Finance via script   |
| Prediksi tidak akurat         | Disclaimer jelas di setiap halaman        |
| Migrasi ke Cloudflare Workers | Arsitektur Django dipisah per-modul sejak awal agar mudah diporting |
