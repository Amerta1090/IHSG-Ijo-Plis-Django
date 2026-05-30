### Cara Menggunakan Model Prophet (USD/IDR) yang Telah Dilatih

Anda dapat mengintegrasikan model ini ke dalam *website* Anda dengan mengikuti langkah-langkah berikut:

#### 1. Persiapan Lingkungan
Pastikan lingkungan *deployment* Anda memiliki pustaka yang diperlukan (`prophet`, `pandas`, `joblib`). Anda bisa menginstalnya dengan `pip`:
```bash
pip install prophet pandas joblib
```

#### 2. Muat Model
Muat model yang telah disimpan (`usdidr_prophet_model.joblib`) menggunakan `joblib`:

```python
import joblib
from prophet import Prophet
import pandas as pd

# Nama file model
model_filename_usdidr = 'usdidr_prophet_model.joblib'

# Muat model dari file
loaded_usdidr_model = joblib.load(model_filename_usdidr)
print("USD/IDR Model berhasil dimuat.")
```

#### 3. Buat Dataframe Masa Depan untuk Prediksi
Model Prophet memerlukan *dataframe* dengan kolom `ds` (tanggal) untuk membuat prediksi. Tentukan berapa banyak periode (hari) ke depan yang ingin Anda prediksi.

```python
# Buat dataframe masa depan untuk 30 hari ke depan
future_usdidr_new = loaded_usdidr_model.make_future_dataframe(periods=30)

# Anda bisa memfilter hanya tanggal yang akan datang jika diperlukan
# future_usdidr_new = future_usdidr_new[future_usdidr_new['ds'] > pd.to_datetime('today')]

print("Dataframe masa depan untuk USD/IDR berhasil dibuat. 5 baris pertama:")
print(future_usdidr_new.head())
```

#### 4. Lakukan Prediksi
Setelah *dataframe* masa depan siap, Anda bisa menggunakan model untuk membuat prediksi:

```python
# Lakukan prediksi
forecast_usdidr_new = loaded_usdidr_model.predict(future_usdidr_new)

print("Prediksi USD/IDR berhasil dibuat. 5 baris pertama:")
print(forecast_usdidr_new[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].head())
```

#### 5. Interpretasi Hasil Prediksi
*   **`ds`**: Kolom tanggal atau *timestamp* untuk setiap titik prediksi.
*   **`yhat`**: Ini adalah nilai prediksi USD/IDR untuk tanggal tersebut.
*   **`yhat_lower`**: Batas bawah interval kepercayaan untuk prediksi `yhat`. Ini menunjukkan perkiraan nilai terendah yang mungkin.
*   **`yhat_upper`**: Batas atas interval kepercayaan untuk prediksi `yhat`. Ini menunjukkan perkiraan nilai tertinggi yang mungkin.

Anda dapat menggunakan nilai `yhat` sebagai prediksi utama dan `yhat_lower`, `yhat_upper` untuk menunjukkan rentang kepercayaan prediksi Anda kepada pengguna *website*.