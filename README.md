# 👁️ Mata AI: Trustworthy Vision Assistant untuk Tunanetra

Proyek ini adalah implementasi *Vision-Language Model* menggunakan **BLIP (LoRA Fine-tuned pada dataset VizWiz)** dan **Gemini API** yang dilengkapi dengan *Image Quality Assessment* (IQA) sebagai *guardrail* (penjaga kualitas).

## 🚀 Fitur Utama
- **IQA Filter (FFT & Contrast):** Mencegah AI berhalusinasi dengan menolak gambar buram/gelap sebelum diproses.
- **Auto API-Rotation:** Mencegah aplikasi *crash* akibat *Rate Limit* pada API Gratis.
- **Audio Autoplay:** Output langsung dibacakan otomatis menggunakan gTTS.
- **Logging System:** Merekam *feedback* pengguna langsung ke dalam format CSV.

## ⚙️ Cara Menjalankan Aplikasi
1. Clone repositori ini.
2. Install library: `pip install -r requirements.txt`
3. Masukkan API Key Gemini Anda di dalam `mesin_ai.py`
4. Jalankan perintah: `streamlit run app.py`