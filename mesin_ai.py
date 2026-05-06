"""
===============================================================================
SISTEM MATA AI: TRUSTWORTHY VISION ASSISTANT
File: mesin_ai.py
===============================================================================
"""

import os
import cv2
import time
import numpy as np
from PIL import Image
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from gtts import gTTS
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
from peft import PeftModel
from google.api_core.exceptions import ResourceExhausted

# ============================================================================
# KONFIGURASI & INISIALISASI MODEL (MULTI-KEY)
# ============================================================================
THRESHOLD_BLUR_SEVERE = -50.9870
THRESHOLD_BLUR_MILD = 8.4085
DROP_DARK = 15
DROP_BRIGHT = 245
DROP_CONTRAST_SEVERE = 10

# Siapkan list API Key lu di sini (bisa 2, 3, atau 10 akun sekaligus)
import streamlit as st

# GANTI BAGIAN API_KEYS LU JADI KAYAK GINI:
API_KEYS = [
    st.secrets["API_KEY_1"],
    st.secrets["API_KEY_2"],
    st.secrets["API_KEY_3"]
]
current_key_idx = 0

def init_gemini():
    """Fungsi sakti untuk ganti akun Gemini saat limit"""
    genai.configure(api_key=API_KEYS[current_key_idx])
    # Menggunakan model flash terbaru sesuai request lu
    return genai.GenerativeModel('gemini-2.5-flash')

gemini_model = init_gemini()

print("⏳ Memuat Processor dan Base Model BLIP...")
base_model_id = "Salesforce/blip-image-captioning-base"
processor = BlipProcessor.from_pretrained(base_model_id)
base_model = BlipForConditionalGeneration.from_pretrained(base_model_id)

print("⏳ Memasang Adaptor LoRA...")
lora_path = "Blip_Training_LoRA_Final/checkpoints/best_lora_model"
blip_lora_model = PeftModel.from_pretrained(base_model, lora_path)
device = "cuda" if torch.cuda.is_available() else "cpu"
blip_lora_model.to(device)
print(f"✅ Model siap di: {device.upper()}")

# ============================================================================
# FUNGSI 1 & 2: IQA & BLIP (Tidak ada perubahan, sudah sempurna)
# ============================================================================
def detect_blur_fft(image_gray, size=60):
    (h, w) = image_gray.shape
    (cX, cY) = (int(w / 2.0), int(h / 2.0))
    fft = np.fft.fft2(image_gray)
    fftShift = np.fft.fftshift(fft)
    fftShift[cY - size:cY + size, cX - size:cX + size] = 0
    fftShift = np.fft.ifftshift(fftShift)
    recon = np.fft.ifft2(fftShift)
    magnitude = 20 * np.log(np.abs(recon) + 1e-10)
    return np.mean(magnitude)

def cek_kualitas_gambar(image_pil):
    img_cv = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)
    rms_contrast = np.std(gray)
    blur_score = detect_blur_fft(gray)

    if mean_brightness < DROP_DARK: return "DROP", "Gambar terlalu gelap gulita. Mohon nyalakan lampu."
    if mean_brightness > DROP_BRIGHT: return "DROP", "Gambar terlalu silau akibat pantulan cahaya."
    if rms_contrast < DROP_CONTRAST_SEVERE: return "DROP", "Gambar pucat dan tidak memiliki kontras yang cukup."
    if blur_score < THRESHOLD_BLUR_SEVERE: return "DROP", "Gambar sangat buram. Mohon jepret ulang."
    if blur_score < THRESHOLD_BLUR_MILD: return "SOFT_BLUR", None
    return "SHARP", None

def proses_mata_blip(image_pil):
    inputs = processor(image_pil, return_tensors="pt").to(device)
    out = blip_lora_model.generate(**inputs)
    return processor.decode(out[0], skip_special_tokens=True)

# ============================================================================
# FUNGSI 3: GEMINI (Exponential Backoff + API Rotation)
# ============================================================================
def proses_otak_gemini(caption_mentah, status_kualitas, max_retries=3):
    global gemini_model, current_key_idx
    
    if status_kualitas == "SOFT_BLUR":
        konteks_kualitas = "PERINGATAN: Gambar agak buram, detail kecil mungkin terlewat."
    else:
        konteks_kualitas = "Kualitas gambar baik."

    prompt = (
        "Kamu adalah AI Asisten untuk Tunanetra.\n"
        f"Hasil deteksi gambar: \"{caption_mentah}\".\n"
        f"Catatan kualitas: {konteks_kualitas}\n"
        "Tugas: Buat 1 kalimat deskripsi natural Bahasa Indonesia, "
        "estimasi Confidence Score 1-100%, dan alasan singkat skor tersebut.\n"
        "WAJIB balas HANYA dalam format 3 baris ini, tanpa tambahan apapun:\n"
        "Deskripsi: [1 kalimat]\n"
        "Skor: [angka]%\n"
        "Alasan: [1 kalimat singkat]"
    )

    wait_times = [0, 15, 30]

    # LOOP 1: Exponential Backoff (Waktu tunggu)
    for attempt in range(max_retries):
        if wait_times[attempt] > 0:
            print(f"⏳ Menunggu {wait_times[attempt]} detik sebelum mencoba lagi...")
            time.sleep(wait_times[attempt])

        # LOOP 2: Rotasi API Key (Ganti akun kalau satu akun limit)
        for _ in range(len(API_KEYS)):
            try:
                response = gemini_model.generate_content(
                    prompt,
                    generation_config=GenerationConfig(max_output_tokens=500)
                )
                return response.text

            except ResourceExhausted:
                print(f"⚠️ Key ke-{current_key_idx+1} Limit! Memutar ke Key berikutnya...")
                # Putar Index Key
                current_key_idx = (current_key_idx + 1) % len(API_KEYS)
                gemini_model = init_gemini() # Re-load model dengan key baru
                
            except Exception as e:
                return (
                    "STATUS: ERROR\n"
                    "Deskripsi: Gangguan koneksi pada sistem AI.\n"
                    "Skor: 0\n"
                    f"Alasan: {str(e)}"
                )
                
    # Kalau kedua loop di atas selesai tapi masih gagal, berarti semua akun hancur lebur
    return (
        "STATUS: RATE_LIMIT\n"
        "Deskripsi: Semua server cadangan sedang sibuk.\n"
        "Skor: 0\n"
        "Alasan: Batas permintaan API dari semua akun telah tercapai."
    )

def buat_suara(teks, nama_file="output.mp3"):
    tts = gTTS(text=teks, lang='id', slow=False)
    tts.save(nama_file)
    return nama_file