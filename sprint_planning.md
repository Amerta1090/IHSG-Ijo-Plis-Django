# Sprint Planning -- IHSG Predictor

**Total estimasi**: 6 sprint x 2 minggu = 12 minggu
**Tim**: 1-2 developer

---

## Sprint 1: Foundation & Project Scaffolding

**Goal**: Django running, database connected, model loadable.

### Task List

| # | Task | Estimasi | Ketergantungan |
|---|------|----------|----------------|
| 1.1 | Init Django project `config/`, struktur `apps/` | 2h | - |
| 1.2 | Setup PostgreSQL + Docker Compose | 2h | - |
| 1.3 | Config `settings/base.py`, `dev.py`, `prod.py` | 3h | 1.1 |
| 1.4 | Setup Tailwind CSS + Flowbite/Preline | 2h | 1.1 |
| 1.5 | Buat `base.html` (navbar, sidebar, footer) | 3h | 1.4 |
| 1.6 | Copy `ihsg_prophet_model.joblib` ke `media/models/` | 0.5h | - |
| 1.7 | Buat `PredictionService` (load model dengan joblib) | 3h | 1.2, 1.6 |
| 1.8 | Test load model di management command | 1h | 1.7 |
| 1.9 | Setup linting & git hooks (ruff, mypy) | 1h | 1.1 |

**Definition of Done**:
- `python manage.py runserver` berjalan tanpa error
- Model Prophet berhasil di-load via shell
- Tailwind menghasilkan CSS kustom
- Halaman `base.html` tampil dengan navbar responsif

---

## Sprint 2: Historical Data & Database Layer

**Goal**: Data historis IHSG bisa diinput manual & via CSV upload.

### Task List

| # | Task | Estimasi | Ketergantungan |
|---|------|----------|----------------|
| 2.1 | Model `HistoricalData` (date, close) + migrasi | 1h | 1.2 |
| 2.2 | Model `UploadedCSV` + migrasi | 1h | 1.2 |
| 2.3 | Form + View upload CSV (validasi kolom ds/y) | 4h | 2.2 |
| 2.4 | CSV parser dengan pandas (preview sebelum insert) | 3h | 2.1 |
| 2.5 | Halaman daftar data historis (tabel responsif) | 3h | 2.1, 1.5 |
| 2.6 | Fitur hapus data historis (single & bulk) | 2h | 2.5 |
| 2.7 | Seed script: ambil data IHSG dari Yahoo Finance | 3h | 2.1 |
| 2.8 | Unit test: model, upload flow | 2h | 2.1-2.3 |

**Definition of Done**:
- Bisa upload CSV dengan kolom `ds, y` dan preview sebelum save
- Data tampil dalam tabel dengan pagination & search
- Seed script jalan & mengisi 2-5 tahun data IHSG

---

## Sprint 3: Prediction Engine & Result Storage

**Goal**: Prediksi IHSG jalan end-to-end dan hasilnya tersimpan.

### Task List

| # | Task | Estimasi | Ketergantungan |
|---|------|----------|----------------|
| 3.1 | Model `PredictionResult` (date, yhat, yhat_lower, yhat_upper, model_version) | 1h | 1.2 |
| 3.2 | Refactor `PredictionService`: `predict(periods=30) -> list[dict]` | 3h | 1.7 |
| 3.3 | Management command `trigger_prediction` (periods=30 default) | 2h | 3.1, 3.2 |
| 3.4 | Simpan hasil prediksi ke `PredictionResult` | 2h | 3.1, 3.3 |
| 3.5 | Celery task `run_prediction_async` + Redis config | 4h | 3.3 |
| 3.6 | Cek duplikasi: skip jika tanggal sudah diprediksi | 1h | 3.4 |
| 3.7 | Error handling: data kurang, model corrupt | 2h | 3.2 |
| 3.8 | Unit test: prediction flow, edge cases | 3h | 3.1-3.5 |

**Definition of Done**:
- `python manage.py trigger_prediction --periods 30` menghasilkan data di DB
- Celery task berjalan async tanpa error
- Prediksi tidak duplicate untuk tanggal yang sama
- Error handling melaporkan pesan jelas jika data historis kosong

---

## Sprint 4: Dashboard & Visualisasi

**Goal**: Halaman utama menampilkan grafik IHSG + prediksi + key metrics.

### Task List

| # | Task | Estimasi | Ketergantungan |
|---|------|----------|----------------|
| 4.1 | DashboardIndex view: query data historis + prediksi | 3h | 2.5, 3.4 |
| 4.2 | Design system: dark theme CSS variables | 2h | 1.4 |
| 4.3 | Component: `MetricCard` (IHSG now, change, prediksi) | 2h | 4.2 |
| 4.4 | Component: `IHSGChart` (area chart hybrid: historical + prediction) | 6h | 4.1, 4.2 |
| 4.5 | Component: `ConfidenceBand` (yhat_lower - yhat_upper shading) | 2h | 4.4 |
| 4.6 | Component: `DataTable` historis (searchable, sortable) | 3h | 2.5 |
| 4.7 | Indicator: perubahan harian (hijau/merah) + arrow icon | 1h | 4.1 |
| 4.8 | Loading skeleton untuk chart saat data belum siap | 2h | 4.4 |
| 4.9 | Responsive: mobile-first layout dashboard | 2h | 4.2 |
| 4.10 | Integrasi AJAX refresh data prediksi tanpa reload | 3h | 4.1, 4.4 |

**Specs: IHSGChart**:
- Chart.js (line) dengan dua dataset: historical (solid) dan prediction (dashed)
- Area fill dengan opacity untuk confidence interval
- Sumbu Y format: ribuan (`,.0f`)
- Tooltip menampilkan: date, actual/predicted value, change %
- Range selector: 1M, 3M, 6M, 1Y, ALL
- Crosshair vertikal saat hover

**Definition of Done**:
- Dashboard menampilkan grafik gabungan data historis + prediksi
- Warna hijau/merah untuk perubahan positif/negatif
- Grafik responsif di desktop & mobile
- Loading state muncul saat prediksi belum tersedia

---

## Sprint 5: User Auth, Profile & API

**Goal**: User bisa login/register, punya profile, dan API publik tersedia.

### Task List

| # | Task | Estimasi | Ketergantungan |
|---|------|----------|----------------|
| 5.1 | Install & configure django-allauth | 2h | 1.1 |
| 5.2 | Custom User Model + Profile (role, company) | 3h | 5.1 |
| 5.3 | Halaman login / register (dark theme) | 3h | 5.1, 4.2 |
| 5.4 | Halaman profile (edit data, avatar) | 2h | 5.2 |
| 5.5 | DRF setup + API endpoint: `/api/v1/predictions/` | 3h | 3.4 |
| 5.6 | API endpoint: `/api/v1/historical/` (filter date range) | 2h | 2.1 |
| 5.7 | API pagination & throttling | 1h | 5.5 |
| 5.8 | API docs via drf-spectacular (Swagger) | 2h | 5.5 |
| 5.9 | Halaman About: info model, metodologi, disclaimer | 2h | - |
| 5.10 | Disclaimer investasi di footer & setiap halaman prediksi | 1h | 4.2 |

**Definition of Done**:
- User bisa register, login, logout, edit profile
- API `/api/v1/predictions/` mengembalikan JSON predictions
- Swagger UI bisa diakses di `/api/docs/`
- Disclaimer tampil di semua halaman yang menampilkan prediksi

---

## Sprint 6: Polish, Deployment & Production Readiness

**Goal**: Aplikasi siap production dengan error handling, logging, monitoring.

### Task List

| # | Task | Estimasi | Ketergantungan |
|---|------|----------|----------------|
| 6.1 | Sentry integration (error tracking) | 1h | 1.1 |
| 6.2 | Django LOGGING config (file + console) | 1h | 1.1 |
| 6.3 | Whitenoise + static file compression | 1h | 1.1 |
| 6.4 | Gunicorn + Daphne config di Dockerfile | 2h | 1.3 |
| 6.5 | Nginx reverse proxy config (prod) | 2h | 6.4 |
| 6.6 | Environment variable validation (`django-environ`) | 1h | 1.3 |
| 6.7 | Security checklist: CSRF, CSP, HTTPS redirect, HSTS | 2h | 1.3 |
| 6.8 | Database backup strategy (pg_dump cron) | 1h | 1.2 |
| 6.9 | Performance: indexed query, N+1 fix, Redis cache | 3h | 3.5, 4.1 |
| 6.10 | Load test dengan locust (simulasi 100 user) | 3h | 4.1, 5.5 |
| 6.11 | Error pages: 404, 500, 403 custom (dark theme) | 2h | 1.5 |
| 6.12 | Final integration test & manual QA | 4h | all |

**Definition of Done**:
- `docker-compose up` jalan di VPS dengan domain
- HTTPS aktif (Let's Encrypt via certbot)
- Sentry mencatat error di production
- Semua endpoint merespon dalam < 500ms (p95)
- Backup database berjalan otomatis tiap hari

---

## Backlog / Icebox

| # | Item | Priority | Notes |
|---|------|----------|-------|
| B1 | Export prediksi ke PDF | Low | - |
| B2 | Export chart sebagai PNG | Low | - |
| B3 | Bandingkan prediksi dengan aktual (accuracy %) | Medium | Butuh akumulasi data real |
| B4 | Dark/light mode toggle | Low | - |
| B5 | Multi-model support (LSTM, ARIMA) | High | Untuk iterasi berikutnya |
| B6 | Email notifikasi prediksi periodik | Medium | Celery beat + cron |
| B7 | Watchlist user (pantau saham tertentu) | Low | Butuh data saham individual |
| B8 | Retrain model via web interface | High | Sprint berikutnya |
| B9 | Multi-language (EN/ID) | Low | i18n dengan django-rosetta |

---

## Estimasi Total

| Sprint | Jam | Fokus |
|--------|-----|-------|
| S1 | 17.5h | Foundation |
| S2 | 19h | Data layer |
| S3 | 18h | Prediction engine |
| S4 | 26h | Dashboard & visualisasi |
| S5 | 21h | Auth, API, tentang |
| S6 | 24h | Deployment & polish |
| **Total** | **125.5h** | ~12 minggu (1 dev full-time) |
