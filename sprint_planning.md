# Sprint Planning — IHSG & USD/IDR Predictor

**Total**: 9 sprint x 1 minggu = 9 minggu
**Tim**: 1 developer

---

## Sprint 1: Foundation & Scaffolding

**Goal**: Django running, model Prophet bisa di-load, base template dengan dark theme siap.

| #   | Task                                                       | Estimasi |
| --- | ---------------------------------------------------------- | -------- |
| 1.1 | Init Django project `config/`, satu app `predictor`        | 1h       |
| 1.2 | Setup PostgreSQL + Docker Compose (django + db)            | 2h       |
| 1.3 | Setup Tailwind CSS + build pipeline                        | 2h       |
| 1.4 | Buat `base.html` — navbar glassmorphism, footer, CSS variables dark theme, skeleton shimmer | 3h |
| 1.5 | Copy `ihsg_prophet_model.joblib` ke `media/models/`       | 0.5h     |
| 1.6 | Buat `PredictionService` — load model dengan joblib        | 2h       |
| 1.7 | Model `HistoricalData` + `PredictionResult` + `ModelVersion` + migrasi | 2h |
| 1.8 | Test load model via management command                     | 1h       |
| 1.9 | Setup linting (ruff) + Makefile                            | 1h       |

**Definition of Done**:
- `python manage.py runserver` berjalan dengan navbar dark + glassmorphism
- Model Prophet sukses di-load via shell/management command
- Tailwind menghasilkan CSS dengan theme IHSG

---

## Sprint 2: Pipeline Data & Training

**Goal**: Fetch IHSG dari Yahoo Finance, train Prophet, predict, semua via CLI. Model versioning jalan.

| #   | Task                                                              | Estimasi |
| --- | ----------------------------------------------------------------- | -------- |
| 2.1 | Script `fetch_ihsg.py` — ambil `^JKSE` via yfinance, validasi     | 3h       |
| 2.2 | Management command `fetch_ihsg` → simpan ke `HistoricalData`      | 1h       |
| 2.3 | Script `train.py` — preprocessing, Prophet fit (ID holidays, multiplicative seasonality) | 4h |
| 2.4 | Management command `train_model` → train + save `.joblib` versioned + eval metrics | 2h |
| 2.5 | Management command `predict` — load active model → predict 90 hari → simpan | 2h |
| 2.6 | Pipeline Makefile: `make retrain` = fetch → train → predict       | 1h       |
| 2.7 | Model versioning: `ModelVersion` tracking, auto-pilih MAE terbaik | 2h       |
| 2.8 | Setup Celery + Redis + Celery Beat untuk retrain mingguan         | 3h       |

**Definition of Done**:
- `make retrain` end-to-end: fetch → train (ID holidays) → predict → save
- Model versions tercatat di DB, active model otomatis yang terbaik
- Celery Beat siap menjadwalkan retrain tiap minggu

---

## Sprint 3: Dashboard Inti

**Goal**: Halaman `/` dengan hybrid chart + hero metrics + fitur premium dasar.

| #   | Task                                                             | Estimasi |
| --- | ---------------------------------------------------------------- | -------- |
| 3.1 | DashboardView — query historis + prediksi (active model)         | 2h       |
| 3.2 | Template `index.html` — layout dashboard penuh                   | 2h       |
| 3.3 | Hero Metrics — 4 card (IHSG Now, Change %, Week Change, Prediksi 30d) + count-up animasi | 3h |
| 3.4 | Hybrid Chart — Chart.js area: historis (solid green) + prediksi (dashed gold) + confidence band | 4h |
| 3.5 | Range selector 1M/3M/6M/1Y/ALL + loading skeleton                | 2h       |
| 3.6 | Multi Timeframe tabs — 7d / 30d / 90d prediksi switch            | 2h       |
| 3.7 | Confidence Score — circular gauge dari uncertainty width          | 2h       |
| 3.8 | Sentiment Badge — Bullish/Bearish/Neutral dari trend 30d         | 1h       |
| 3.9 | Last Updated timestamp + tombol "Refresh Data" manual + status badge (IHSG tutup 1x/hari) | 2h |
| 3.10 | Export chart sebagai PNG                                         | 1h       |
| 3.11 | Responsive mobile-first                                          | 2h       |

**Definition of Done**:
- Dashboard menampilkan grafik hybrid + 4 metric card + tab 7d/30d/90d
- Confidence score dan sentiment badge muncul dengan data real
- Tombol "Refresh Data" manual + last updated badge berfungsi
- Responsive di mobile

---

## Sprint 4: Indikator Teknikal & Komponen Premium

**Goal**: Tambah indikator teknikal, decomposition chart, accuracy tracker.

| #   | Task                                                                 | Estimasi |
| --- | -------------------------------------------------------------------- | -------- |
| 4.1 | SMA 20 & 50 overlay di chart (togglable)                             | 2h       |
| 4.2 | Prophet Decomposition Chart — trend + weekly + yearly (3 subcharts)  | 4h       |
| 4.3 | Volatility Indicator card (std dev return 20d)                       | 1h       |
| 4.4 | Prediction vs Actual tracker — tabel prediksi lalu vs realisasi + coming soon label | 3h |
| 4.5 | Micro-interactions: smooth fade-in, glow effect, tooltip premium     | 2h       |
| 4.6 | `/api/metrics.json` endpoint untuk refresh chart via tombol manual   | 1h       |

**Definition of Done**:
- SMA 20/50 bisa di-toggle di chart
- Decomposition chart menampilkan 3 komponen Prophet
- Prediction vs Actual siap (dengan label coming soon sampai data real terkumpul)
- Semua mikro-interaksi halus

---

## Sprint 5: About, Accuracy Tracker, Polish & Deploy

**Goal**: Halaman about, model stats, error handling, deploy production.

| #   | Task                                                              | Estimasi |
| --- | ----------------------------------------------------------------- | -------- |
| 5.1 | Halaman `/about` — metodologi, disclaimer, cara baca chart         | 2h       |
| 5.2 | Model Stats di about — MAE, RMSE, data range, last training        | 1h       |
| 5.3 | Accuracy Tracker chart — grafik akurasi antar versi model          | 2h       |
| 5.4 | Riwayat Model table — versi, tanggal train, metrik, is_active      | 1h       |
| 5.5 | Error handling — data kosong, model corrupt, fallback UI smooth    | 2h       |
| 5.6 | Custom 404/500 pages (dark theme)                                  | 1h       |
| 5.7 | Dockerfile + docker-compose final (Django + PostgreSQL + Redis + Celery) | 3h |
| 5.8 | Production setup — gunicorn, whitenoise, env vars, SECURE settings | 2h       |
| 5.9 | Deploy ke VPS / Railway / Fly.io                                   | 2h       |

**Definition of Done**:
- Halaman `/about` lengkap dengan model stats + accuracy tracker + riwayat model
- Error handling smooth (tidak muncul stack trace)
- Docker Compose satu perintah up, semua service jalan
- Deployed dan bisa diakses publik

---

## Sprint 6: USD/IDR Foundation

**Goal**: Model USD/IDR siap di-load, services multi-market, data models + migration, pipeline prediksi via CLI.

| #   | Task                                                                 | Estimasi |
| --- | -------------------------------------------------------------------- | -------- |
| 6.1 | Copy `usdidr_prophet_model.joblib` ke `media/models/`               | 0.5h     |
| 6.2 | Refactor `PredictionService` — multi-market support (IHSG + USD/IDR) | 3h       |
| 6.3 | Model `UsdIdrHistoricalData` + `UsdIdrPredictionResult` + migrasi   | 2h       |
| 6.4 | Management command `predict_usdidr` — load model → predict 90d → simpan | 2h     |

**Definition of Done**:
- Model USD/IDR sukses di-load via `PredictionService(market='usdidr')`
- `UsdIdrHistoricalData` + `UsdIdrPredictionResult` tercatat di DB
- `python manage.py predict_usdidr` menghasilkan prediksi 90 hari

---

## Sprint 7: USD/IDR Dashboard

**Goal**: Parameterized dashboard + chart refactor, navigasi dual-market, hero metrics, confidence score, sentiment badge.

| #   | Task                                                                 | Estimasi |
| --- | -------------------------------------------------------------------- | -------- |
| 7.1 | Refactor `DashboardView` + urls — parameterized by market kwarg      | 2h       |
| 7.2 | Refactor `index.html` → `dashboard.html` — semua hardcode IHSG jadi `{{ market.* }}` | 3h |
| 7.3 | Refactor `chart.js` — market-aware config (warna, label, endpoint)   | 3h       |
| 7.4 | Navbar toggle/selector — pindah antara IHSG ↔ USD/IDR               | 1h       |
| 7.5 | API endpoint `/api/usdidr/metrics.json`                              | 1h       |
| 7.6 | Hero Metrics USD/IDR — kurs now, change %, week change, prediksi 30d | 1h       |

**Definition of Done**:
- Satu `dashboard.html` melayani kedua market via context variable
- Chart.js menampilkan chart sesuai market yang aktif
- Navbar toggle berfungsi, hero metrics muncul dengan data USD/IDR

---

## Sprint 8: USD/IDR Premium + About

**Goal**: Semua indikator premium IHSG di-port ke USD/IDR, retrain pipeline, about page dual-market.

| #   | Task                                                                 | Estimasi |
| --- | -------------------------------------------------------------------- | -------- |
| 8.1 | Port Confidence Score circular gauge — reusable untuk USD/IDR        | 1h       |
| 8.2 | Port Sentiment Badge — market-aware (trend MA 30d)                   | 0.5h     |
| 8.3 | Port SMA 20/50 overlay + Decomposition Chart ke USD/IDR              | 2h       |
| 8.4 | Port Volatility Indicator card ke USD/IDR                            | 0.5h     |
| 8.5 | Port Export Chart PNG — market-aware filename                        | 0.5h     |
| 8.6 | Retrain pipeline USD/IDR — `make retrain-usdidr` + Celery Beat       | 2h       |
| 8.7 | Update About page — model stats untuk kedua market (IHSG + USD/IDR)  | 1h       |
| 8.8 | E2E test — USD/IDR prediction + dashboard render                     | 0.5h     |

**Definition of Done**:
- Semua indikator (confidence, sentiment, SMA, decomposition, volatility) berfungsi di `/usdidr/`
- `make retrain-usdidr` end-to-end
- Halaman `/about` menampilkan statistik kedua model

---

## Backlog

| #   | Item                               | Prioritas | Notes                               |
| --- | ---------------------------------- | --------- | ----------------------------------- |
| B1  | RSI indicator — subchart bawah     | Low       | Butuh data OHLC, gak relevan untuk prediksi IHSG harian |
| B2  | MACD indicator — subchart          | Low       | Sama, lebih cocok untuk trading intraday |
| B3  | Dark/light mode toggle             | Low       | Nice to have, nambah polish saja    |

---

## Estimasi Total

| Sprint | Jam  | Fokus                             |
| ------ | ---- | --------------------------------- |
| S1     | 14.5h | Foundation                        |
| S2     | 18h  | Pipeline data & training          |
| S3     | 23h  | Dashboard inti                    |
| S4     | 13h  | Indikator & komponen premium      |
| S5     | 16h  | About, polish, deploy             |
| S6     | 7.5h  | USD/IDR Foundation               |
| S7     | 11h  | USD/IDR Dashboard                 |
| S8     | 8h   | USD/IDR Premium + About          |
| **Total** | **111h** | ~9 minggu (1 dev)          |
