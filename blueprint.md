# Blueprint — IHSG Predictor

## 1. Visi & Tujuan

Satu halaman web prediksi IHSG yang modern, cepat, dan _eye-catching_.
User datang, lihat grafik prediksi + indikator teknikal, dapat wawasan — selesai.
Prediksi tetap akurat berkat retrain model otomatis dari data Yahoo Finance.

---

## 2. Arsitektur Sistem

```
[Browser] --> [Django] --> [PostgreSQL]
                │
                ├── Prophet Model (.joblib)
                └── Celery + Redis (retrain scheduler)
```

### Stack Utama

| Layer        | Teknologi                       |
| ------------ | ------------------------------- |
| Backend      | Django 5.x                      |
| DB           | PostgreSQL                      |
| Cache/Queue  | Redis + Celery (scheduled retrain) |
| ML Model     | Prophet (joblib)                |
| Frontend     | Django Templates + Tailwind CSS |
| Chart        | Chart.js (line + area + bar)    |
| Deploy       | Docker + Gunicorn               |

### Struktur Direktori

```
ihsg_project/
├── config/                 # settings, urls, wsgi
├── apps/
│   └── predictor/          # satu app: semua logic di sini
│       ├── models.py
│       ├── views.py
│       ├── services.py     # PredictionService, TrainingService
│       ├── fetch_ihsg.py   # Yahoo Finance scraper
│       ├── train.py        # Prophet training pipeline
│       └── management/     # management commands
├── static/
│   ├── css/main.css
│   └── js/
│       ├── chart.js
│       ├── metrics.js
│       └── components.js
├── templates/
│   ├── base.html
│   ├── index.html
│   └── about.html
├── media/models/           # .joblib dengan versioning timestamp
├── manage.py
├── docker-compose.yml      # Django + PostgreSQL + Redis + Celery
├── Dockerfile
└── Makefile
```

---

## 3. Model Data

```python
HistoricalData
  ├── date (DateField, unique)
  └── close (FloatField)

PredictionResult
  ├── date (DateField)
  ├── yhat (FloatField)
  ├── yhat_lower (FloatField)
  ├── yhat_upper (FloatField)
  ├── model_version (CharField)    # timestamp-based
  └── unique: (date, model_version)

ModelVersion
  ├── version (CharField, unique)  # "20260530_143022"
  ├── trained_at (DateTimeField)
  ├── data_end_date (DateField)
  ├── metrics (JSONField)           # {'mae': ..., 'rmse': ...}
  └── is_active (BooleanField)
```

---

## 4. Alur Data & Training

### 4.1 Pipeline Retrain (Offline Batch Learning)

```
Cron / Celery Beat (mingguan)
       │
       ▼
┌─────────────────────────────┐
│ fetch_ihsg.py               │
│ → Yahoo Finance ^JKSE       │
│ → 10 tahun historis         │
│ → simpan ke HistoricalData  │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ train.py                    │
│ → Preprocessing (ds, y)     │
│ → Prophet fit (linear,      │
│   multiplicative season.)   │
│ → save .joblib (versioned)  │
│ → eval metrics → store      │
│   ke ModelVersion           │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ predict.py                  │
│ → load active model         │
│ → make_future_dataframe(90) │
│ → predict() → simpan ke     │
│   PredictionResult          │
└──────────┬──────────────────┘
           ▼
      Dashboard otomatis
      update (via AJAX)
```

Pipeline ini jalan otomatis via Celery Beat tiap minggu. Bisa juga di-trigger manual via `make retrain`.

### 4.2 Alur Tampilan

User buka `/` → DashboardView query `HistoricalData` (historis) + `PredictionResult` (prediksi) → render Chart.js hybrid + metric cards + indikator teknikal.

---

## 5. Fitur Premium

### 5.1 Dashboard Utama (`/`)

> **Catatan realitas**: IHSG hanya tutup 1x sehari (15:00 WIB). Data Yahoo Finance delay ~15 menit. Prediksi >30 hari confidence makin lebar — ini normal dan ditampilkan secara transparan via confidence band. RSI/MACD tidak disertakan karena tidak relevan untuk prediksi indeks harian (fokus: trend & seasonality).

| Fitur                   | Keterangan                                              |
| ----------------------- | ------------------------------------------------------- |
| **Multi Timeframe**     | Tab 7d / 30d / 90d — prediksi density berbeda           |
| **Hero Metrics**        | IHSG Now · Change (%) · Week Change · Prediksi 30d     |
| **Hybrid Chart**        | Area chart: historis (solid green) + prediksi (dashed gold) + confidence band |
| **Moving Average**      | SMA 20 & 50 overlay di chart — toggable                 |
| **Confidence Score**    | Circular gauge: seberapa yakin model berdasarkan uncertainty width |
| **Prediksi vs Aktual**  | Tabel: prediksi sebelumnya vs realisasi + akurasi % *(coming soon — butuh akumulasi data)* |
| **Export PNG**          | Tombol download chart sebagai PNG                       |
| **Refresh Manual**      | Tombol "Refresh Data" + last updated badge (IHSG tutup 1x/hari, tdk perlu auto-refresh) |
| **Component Decomposition** | Trend, weekly, yearly — Prophet decompose chart    |
| **Sentiment Badge**     | Bullish / Bearish / Neutral berdasar slope MA 30d       |
| **Volatility Indicator**| Standar deviasi return 20d terakhir                     |

### 5.2 Halaman About (`/about`)

| Fitur                  | Keterangan                                  |
| ---------------------- | ------------------------------------------- |
| Metodologi             | Penjelasan cara kerja Prophet + disclaimer  |
| Model Stats            | MAE, RMSE, data range, last training        |
| Accuracy Tracker       | Grafik akurasi prediksi antar versi model   |
| Riwayat Model          | Tabel versi model + tanggal train + metrik  |

### 5.3 Micro-interactions (Frontend)

- **Count-up animation** — angka metric naik dari 0 ke nilai real
- **Smooth fade-in** — komponen muncul bertahap saat scroll
- **Skeleton shimmer** — loading state premium
- **Glow effect** — aksen emas/hijau samar di card aktif
- **Tooltip premium** — Chart.js tooltip kustom dengan detail lengkap
- **Responsive** — mobile-first, grid otomatis menyesuaikan layar

---

## 6. Design System (UI/UX)

**Tema**: Financial dark — elegan, modern, maskulin.
**Font**: Inter (headline) + JetBrains Mono (angka/data)
**Palette**:

| Role              | Warna      |
| ----------------- | ---------- |
| Background        | `#0a0f1e`  |
| Card/Surface      | `#141b2d`  |
| Card hover        | `#1a2338`  |
| Bullish (naik)    | `#22c55e`  |
| Bearish (turun)   | `#ef4444`  |
| Aksen emas        | `#f59e0b`  |
| Aksen biru        | `#3b82f6`  |
| Text utama        | `#f1f5f9`  |
| Text second       | `#94a3b8`  |
| Garis/divider     | `#1e293b`  |

**Layout**:

```
┌──────────────────────────────────────────┐
│ Navbar (logo + About + status indicator) │
├──────────────────────────────────────────┤
│ Hero Metrics (3-4 card row)              │
├──────────────────────────────────────────┤
│ Tab: 7d │ 30d │ 90d                      │
├──────────────────────────────────────────┤
│ Hybrid Chart (histori + prediksi)        │
│ ├─ SMA 20/50 toggle                      │
│ └─ Range: 1M │ 3M │ 6M │ 1Y │ ALL      │
├──────────────────────────────────────────┤
│ Statistics Row:                          │
│ Confidence │ Sentiment │ Volatility      │
├──────────────────────────────────────────┤
│ Decomposition Chart (trend/weekly/yearly)│
├──────────────────────────────────────────┤
│ Prediction vs Actual Tracker (coming soon)│
├──────────────────────────────────────────┤
│ Footer (disclaimer besar)                │
└──────────────────────────────────────────┘
```

---

## 7. Halaman / Route

| URL      | View           | Deskripsi                                  |
| -------- | -------------- | ------------------------------------------ |
| `/`      | DashboardView  | Grafik IHSG + prediksi + indikator + metrik |
| `/about` | AboutView      | Info model, metodologi, accuracy tracker   |
| `/api/metrics.json` | MetricsAPI | JSON endpoint untuk auto-refresh chart    |

Hanya 2 halaman + 1 endpoint API ringan. Semua interaksi di satu halaman utama.

---

## 8. Incremental Learning (Offline Batch)

### Kenapa?

Model Prophet perlu data terbaru agar prediksi tetap relevan. Makin baru data training, makin akurat prediksi.

### Cara Kerja

1. **Fetch** — Ambil data IHSG 10 tahun dari Yahoo Finance (`^JKSE`) via `yfinance`
2. **Preprocess** — Flatten kolom, rename `Date → ds`, `Close → y`
3. **Train** — Prophet.fit() dengan Indonesian holidays + yearly/weekly seasonality
4. **Version** — Simpan `.joblib` dengan format `ihsg_v{timestamp}.joblib`
5. **Eval** — Hitung MAE, RMSE, simpan ke `ModelVersion.metrics`
6. **Predict** — Generate forecast 90 hari, simpan ke `PredictionResult`
7. **Schedule** — Celery Beat menjalankan pipeline ini tiap Minggu jam 00:00 WIB

### Versioning

Setiap retrain menghasilkan model baru. Model lama tetap disimpan (rollback possible). Model dengan MAE terendah otomatis jadi active. Dashboard menggunakan model active untuk prediksi.

---

## 9. Constraints

- Data IHSG dari Yahoo Finance (`^JKSE`) — butuh koneksi internet
- Model Prophet di-retrain via Celery Beat tiap minggu (bisa manual via `make retrain`)
- PostgreSQL untuk production (SQLite hanya untuk dev lokal)
- Prediksi bersifat indikatif — bukan saran investasi
- Deployment: Docker Compose (Django + PostgreSQL + Redis + Celery Worker)

---

## 10. Risks

| Risk                         | Mitigation                               |
| ---------------------------- | ---------------------------------------- |
| Yahoo Finance rate limit     | Cache data, jangan fetch tiap request    |
| Retrain gagal di tengah      | Model lama tetap aktif, error tercatat   |
| Redis/Celery down            | Retrain bisa di-trigger manual via CLI   |
| User misinterpretasi prediksi| Disclaimer besar + metode jelas di about |
| Model degradation            | Accuracy tracker detects drift → notifikasi |
