"""
===============================================================================
UI STREAMLIT: APLIKASI MATA AI (Trustworthy Vision Assistant)
File: app.py
===============================================================================
"""

import streamlit as st
from PIL import Image
import base64
import hashlib
import csv
from datetime import datetime
import os

@st.cache_resource
def load_mesin():
    import mesin_ai
    return mesin_ai

mesin = load_mesin()

st.set_page_config(page_title="Mata AI - Tunanetra", page_icon="👁️", layout="centered")

# ==========================================
# CSS AKSESIBILITAS TINGGI (UI Dipercantik)
# ==========================================
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;} 
        footer {visibility: hidden;}
        
        /* Font size dasar lebih besar untuk Low Vision */
        p, div, span, label {
            font-size: 1.15rem !important;
        }
        
        /* Modifikasi Kotak Upload agar lebih tegas dan ramah sentuhan */
        .stFileUploader>div {
            padding: 40px 20px;
            background-color: #1E1E1E;
            border: 4px dashed #FFD700 !important;
            border-radius: 15px;
            text-align: center;
        }
        
        /* Tombol Raksasa dengan Kontras Tinggi (WCAG AA) */
        .stButton>button {
            min-height: 70px;
            font-size: 1.2rem !important;
            font-weight: bold;
            border-radius: 10px;
            border: 2px solid #ffffff;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #FFD700 !important;
            color: #000000 !important;
            border-color: #FFD700 !important;
            transform: scale(1.02);
        }
        
        /* Rapihin Alert Box */
        .stAlert {
            border-radius: 10px !important;
            font-weight: 500;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# FUNGSI LOGGING CSV (Untuk Bab 4 Skripsi)
# ==========================================
def simpan_log(hash_gambar, status, caption, hasil_ai, feedback):
    file_exists = os.path.isfile('log_evaluasi.csv')
    with open('log_evaluasi.csv', mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Waktu', 'Hash_Gambar', 'Kualitas', 'BLIP_Mentah', 'Hasil_Gemini', 'Feedback_User'])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), hash_gambar, status, caption, hasil_ai, feedback])


st.title("👁️ Mata AI")
st.markdown("**Asisten Pendeteksi Objek dengan Trustworthy AI**")

# ==========================================
# FITUR INPUT GAMBAR (KAMERA & GALERI)
# ==========================================
st.write("Silakan jepret foto langsung atau pilih dari memori HP:")

# 1. Jalur Kamera Langsung (Otomatis buka webcam/kamera HP)
gambar_kamera = st.camera_input("📸 Jepret Foto Langsung")

# 2. Jalur Galeri (Upload file)
gambar_galeri = st.file_uploader("📂 Atau Pilih dari Galeri HP", type=["jpg", "jpeg", "png"])

# LOGIKA CERDAS: Prioritaskan kamera. Kalau kamera kosong, baru pakai galeri.
# Dengan pakai nama variabel 'uploaded_file', kode lu yang di bawah NGGAK PERLU DIUBAH sama sekali!
uploaded_file = gambar_kamera if gambar_kamera is not None else gambar_galeri

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    file_hash = hashlib.md5(file_bytes).hexdigest()

    image = Image.open(uploaded_file).convert('RGB')
    st.image(image, use_container_width=True, caption="Gambar yang akan dianalisis")
    st.divider()

    if "current_image_hash" not in st.session_state or st.session_state.current_image_hash != file_hash:
        st.session_state.current_image_hash = file_hash
        st.session_state.sudah_diproses = False
        st.session_state.status_error = None

    # ==========================================
    # PROSES AI 
    # ==========================================
    if not st.session_state.sudah_diproses:
        with st.spinner("🤖 Sistem sedang berpikir... (maks ~45 detik jika padat)"):

            status, pesan = mesin.cek_kualitas_gambar(image)
            st.session_state.status_kualitas = status
            st.session_state.pesan_error = pesan

            if status == "DROP":
                st.session_state.hasil_akhir_ui = None
                st.session_state.status_error = None
                mesin.buat_suara(pesan, "error.mp3")
                st.session_state.file_audio = "error.mp3"
                st.session_state.sudah_diproses = True

            else:
                caption_mentah = mesin.proses_mata_blip(image)
                st.session_state.caption_mentah = caption_mentah

                hasil_akhir = mesin.proses_otak_gemini(caption_mentah, status)
                st.session_state.hasil_akhir_ui = hasil_akhir

                if "STATUS: RATE_LIMIT" in hasil_akhir:
                    st.session_state.status_error = "RATE_LIMIT"
                    st.session_state.sudah_diproses = True
                    teks_suara = "Maaf, server sedang penuh. Silakan coba lagi sebentar."
                elif "STATUS: ERROR" in hasil_akhir:
                    st.session_state.status_error = "ERROR"
                    st.session_state.sudah_diproses = True
                    teks_suara = "Terjadi gangguan koneksi. Periksa internet Anda."
                else:
                    st.session_state.status_error = None
                    st.session_state.sudah_diproses = True
                    try:
                        teks_suara = [b for b in hasil_akhir.split('\n') if "Deskripsi:" in b][0].replace("Deskripsi: ", "").strip()
                    except:
                        teks_suara = "Analisis selesai."

                mesin.buat_suara(teks_suara, "sukses.mp3")
                st.session_state.file_audio = "sukses.mp3"

    # ==========================================
    # TAMPILKAN HASIL
    # ==========================================
    if st.session_state.status_kualitas == "DROP":
        st.error(f"🚨 **DITOLAK SISTEM:** {st.session_state.pesan_error}")

    elif st.session_state.get("status_error") == "RATE_LIMIT":
        st.warning(
            "⛔ **Server Google Sedang Penuh**\n\n"
            "Sistem sudah memutar semua kunci API dan mencoba otomatis selama ~45 detik. "
            "Tunggu **1–2 menit penuh** lalu tekan tombol di bawah untuk mencoba ulang."
        )
        if st.button("🔄 Coba Kirim ke AI Lagi", type="primary", use_container_width=True):
            st.session_state.sudah_diproses = False
            st.session_state.status_error = None
            st.rerun()

    elif st.session_state.get("status_error") == "ERROR":
        st.error("❌ **Gagal Terhubung ke AI**\nPeriksa koneksi internet Anda, lalu tekan tombol di bawah.")
        if st.button("🔄 Coba Lagi", type="primary", use_container_width=True):
            st.session_state.sudah_diproses = False
            st.session_state.status_error = None
            st.rerun()

    else:
        hasil = st.session_state.get("hasil_akhir_ui")
        if hasil:
            try:
                baris = hasil.split('\n')
                
                # Kasih nilai default dulu biar kalau Gemini lupa, sistem nggak crash
                deskripsi = hasil # Kalau format hancur, anggap semua teks adalah deskripsi
                skor = "Tidak diketahui"
                alasan = "Sistem AI tidak memberikan alasan."

                # Cari baris per baris secara aman
                for b in baris:
                    if "Deskripsi:" in b: 
                        deskripsi = b.replace("Deskripsi:", "").strip()
                    elif "Skor:" in b: 
                        skor = b.replace("Skor:", "").strip()
                    elif "Alasan:" in b: 
                        alasan = b.replace("Alasan:", "").strip()
                
                # Tampilkan ke UI
                st.success(f"🗣️ **{deskripsi}**")

                if st.session_state.status_kualitas == "SOFT_BLUR":
                    st.warning(f"⚠️ Gambar sedikit buram. Skor Keyakinan: **{skor}**.")
                else:
                    st.info(f"✅ Kualitas Tajam. Skor Keyakinan: **{skor}**.")

                with st.expander("🔍 Lihat Jejak Pemikiran AI (Explainability)"):
                    st.write(f"**Hasil Ekstraksi BLIP:** `{st.session_state.caption_mentah}`")
                    st.write(f"**Rasionalisasi Gemini:** {alasan}")

            except Exception as e:
                # Ini cuma kepanggil kalau bener-bener error parah dari Python-nya
                st.warning("Terjadi kesalahan saat membaca teks dari AI.")
                st.write(hasil)

        # FITUR FEEDBACK LOGGING CSV
        st.divider()
        st.markdown("**Apakah hasil ini akurat?** *(Bantu kami evaluasi sistem)*")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 Akurat", use_container_width=True):
                simpan_log(st.session_state.current_image_hash, st.session_state.status_kualitas, st.session_state.caption_mentah, st.session_state.hasil_akhir_ui.replace('\n', ' | '), "AKURAT")
                st.toast("✅ Terima kasih! Log telah disimpan.")
        with col2:
            if st.button("👎 Tidak Akurat", use_container_width=True):
                simpan_log(st.session_state.current_image_hash, st.session_state.status_kualitas, st.session_state.caption_mentah, st.session_state.hasil_akhir_ui.replace('\n', ' | '), "TIDAK_AKURAT")
                st.toast("📝 Catatan evaluasi disimpan.")

    # ==========================================
    # AUTOPLAY AUDIO
    # ==========================================
    try:
        with open(st.session_state.file_audio, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f'<audio autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
            st.markdown(md, unsafe_allow_html=True)
            st.markdown("*🔊 (Sistem telah memutar suara...)*")
    except:
        pass