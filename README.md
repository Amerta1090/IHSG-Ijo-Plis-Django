# IHSG & USD/IDR Predictor

Platform prediksi pergerakan IHSG dan nilai tukar USD/IDR menggunakan Facebook Prophet, disajikan dengan dashboard dark mode yang meyakinkan Anda bahwa masa depan bisa ditebak (setidaknya secara statistik).

## Fitur

- **Dashboard parameterized** — satu halaman, dua market (IHSG dan USD/IDR), tinggal ganti `market` di URL.
- **Hybrid chart** — area chart hijau untuk data historis yang sudah terjadi, garis emas putus-putus untuk prediksi yang semoga mendekati kenyataan.
- **Confidence band** — area transparan di sekitar prediksi yang melebar seiring waktu, sebagai pengingat bahwa model juga tidak tahu apa-apa tentang hari depan.
- **SMA 20/50** — moving average yang bisa di-toggle, untuk Anda yang masih percaya pada indikator teknikal klasik.
- **Multi timeframe** — 7, 30, 90 hari prediksi, dengan tingkat kepastian yang menurun secara eksponensial.
- **Confidence score gauge** — seberapa yakin model terhadap prediksinya, dalam bentuk lingkaran yang jarang penuh.
- **Sentiment badge** — Bullish/Bearish/Neutral berdasarkan slope prediksi 30 hari, untuk kepuasan batin semata.
- **Volatility indicator** — standar deviasi return 20 hari terakhir. Hijau jika tenang, merah jika panik.
- **Component decomposition** — trend, weekly cycle, yearly cycle hasil decompose Prophet. Ilustrasi bahwa pasar saham ternyata dipengaruhi oleh hari dalam seminggu.
- **FORCE_REFRESH** — tombol yang benar-benar menjalankan retrain_all (fetch data + train ulang + predict), bukan sekadar reload halaman.
- **Export PNG** — unduh chart sebagai gambar, kalau-kalau Anda ingin menyimpan bukti prediksi untuk ditertawakan di kemudian hari.

## Kriteria Sistem

```
[Browser] <---> [Django] <---> [PostgreSQL]
                     |
             [Prophet Model (.joblib)]
             [Redis + Celery (optional)]
```

### Stack

| Layer | Teknologi |
|-------|-----------|
| Backend | Django 5.x |
| Database | PostgreSQL (production), SQLite (development) |
| ML Engine | Facebook Prophet (via `prophet` package) |
| Frontend | Django Templates + Tailwind CSS + Chart.js |
| Task Queue | Celery + Redis (optional, untuk retrain terjadwal) |
| Deployment | Docker + Gunicorn + Railway |

## Struktur Direktori (Relevan)

```
apps/predictor/
├── management/commands/
│   ├── fetch_ihsg.py         # ambil data IHSG dari Yahoo Finance
│   ├── fetch_usdidr.py       # ambil data USD/IDR dari Yahoo Finance
│   ├── train_model.py        # train Prophet untuk IHSG
│   ├── train_usdidr.py       # train Prophet untuk USD/IDR
│   ├── predict.py            # generate prediksi IHSG
│   ├── predict_usdidr.py     # generate prediksi USD/IDR
│   ├── retrain_all.py        # all-in-one: fetch + train + predict untuk kedua market
│   ├── setup_beat.py         # setup Celery Beat schedule
│   └── load_model.py         # load model dari file .joblib
├── models.py                 # HistoricalData, PredictionResult, ModelVersion + USD/IDR variants
├── views.py                  # dashboard, about, API endpoints
└── services.py               # TrainingService (fetch, train, eval) + PredictionService (load, predict)
```

## Cara Penggunaan Lokal

### Prasyarat

- Python 3.11+
- Node.js (untuk Tailwind CSS)
- PostgreSQL atau SQLite untuk development

### Setup

```bash
# Clone
git clone <repo-url>
cd ihsg_project

# Virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
npm install

# Environment variables (copy dan sesuaikan)
cp .env.example .env

# Migrate
python manage.py migrate

# Build CSS
npm run build

# Jalankan
python manage.py runserver
```

### Management Commands

```bash
# Fetch data dari Yahoo Finance
python manage.py fetch_ihsg          # Data IHSG ~10 tahun
python manage.py fetch_usdidr        # Data USD/IDR ~10 tahun

# Train model
python manage.py train_model         # Prophet untuk IHSG
python manage.py train_usdidr        # Prophet untuk USD/IDR

# Generate prediksi
python manage.py predict --periods 90
python manage.py predict_usdidr --periods 90

# All-in-one
python manage.py retrain_all         # fetch + train + predict untuk kedua market

# Setup Celery Beat (jika menggunakan Redis)
python manage.py setup_beat
```

Atau via Makefile yang sudah disediakan:

```bash
make dev            # runserver
make retrain-all    # retrain_all
make fetch          # fetch_ihsg
make train          # train_model
make predict        # predict untuk IHSG
```

## API Endpoints

| Endpoint | Method | Deskripsi |
|----------|--------|-----------|
| `/` | GET | Dashboard IHSG |
| `/usdidr/` | GET | Dashboard USD/IDR |
| `/about/` | GET | Informasi model, metrik, riwayat |
| `/health/` | GET | Health check (response: "ok") |
| `/api/metrics.json` | GET | Data historis + prediksi IHSG (JSON) |
| `/api/usdidr/metrics.json` | GET | Data historis + prediksi USD/IDR (JSON) |
| `/api/decomposition.json` | GET | Komponen trend/weekly/yearly IHSG |
| `/api/usdidr/decomposition.json` | GET | Komponen trend/weekly/yearly USD/IDR |
| `/api/trigger-retrain.json` | GET | Memicu retrain_all (background thread) |
| `/api/retrain-status.json` | GET | Status retrain yang sedang berjalan |

## Deployment (Railway)

Project ini dideploy di Railway sebagai Docker container. Environment variables yang perlu diatur:

| Variable | Contoh | Keterangan |
|----------|--------|------------|
| `DJANGO_SETTINGS_MODULE` | `config.settings.prod` | Wajib |
| `DJANGO_SECRET_KEY` | `<generate-random>` | Wajib |
| `DATABASE_URL` | (auto dari Railway PostgreSQL) | Otomatis oleh Railway |
| `ALLOWED_HOSTS` | `.railway.app,domain.com` | Host yang diizinkan |
| `CSRF_TRUSTED_ORIGINS` | `https://*.railway.app` | Origin CSRF yang dipercaya |
| `PORT` | `8080` | Port (diisi otomatis oleh Railway) |

Stack deployment: Dockerfile dengan Gunicorn sebagai WSGI server, WhiteNoise untuk static files, dan migrasi otomatis saat startup.

## Metodologi Model

- **Algoritma**: Facebook Prophet dengan linear growth, multiplicative seasonality, dan Indonesian holidays.
- **Fitur**: Yearly + weekly seasonality, changepoint_prior_scale=0.05.
- **Data training**: ~10 tahun harga penutupan harian (IHSG dari `^JKSE`, USD/IDR dari `USDIDR=X` via Yahoo Finance).
- **Retrain**: Periodik (mingguan) via Celery Beat, atau manual via `retrain_all`.
- **Versioning**: Setiap retrain menghasilkan model baru dengan timestamp. Model dengan MAE terendah otomatis menjadi active model.
- **Evaluasi**: MAE dan RMSE dihitung terhadap data historis yang digunakan untuk training. Disimpan di ModelVersion untuk tracking akurasi antar versi.

## Catatan Penting (Disclaimer yang Sebenarnya Juga Penting)

- Data IHSG dan USD/IDR bersumber dari Yahoo Finance. Delay data sekitar 15-20 menit untuk harga real-time.
- IHSG hanya tutup sekali sehari (15:00 WIB). Tidak ada data intraday.
- Prediksi lebih dari 30 hari memiliki confidence band yang melebar secara signifikan. Ini bukan bug, ini karakteristik dasar forecasting.
- Model tidak memiliki akses ke news sentiment, kebijakanBank Indonesia, perang dagang, atau keputusan presiden yang tiba-tiba.
- Semua prediksi bersifat indikatif dan bukan merupakan saran investasi. Jika Anda mengambil keputusan finansial berdasarkan prediksi model ini, ingatlah bahwa model yang sama juga memprediksi kapan Anda akan menyesal.

## Lisensi

Tidak ada lisensi resmi. Kode ini disediakan untuk keperluan pembelajaran dan hiburan semata. Gunakan risiko sendiri, terutama jika Anda berniat menggunakannya untuk trading.
