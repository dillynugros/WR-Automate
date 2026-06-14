import streamlit as st
import feedparser
import urllib.parse
from google import genai
from datetime import datetime, timedelta

# --- KONFIGURASI ANTARMUKA (UI) ---
st.set_page_config(page_title="Generator Weekly Report Banten", page_icon="📰")
st.title("📰 Generator Laporan Mingguan Otomatis")
st.markdown("Aplikasi ini menarik berita terkini dan menggunakan Gemini AI untuk menyusun Isu Strategis & Rekomendasi.")

# --- SIDEBAR UNTUK PENGATURAN ---
with st.sidebar:
    st.header("⚙️ Pengaturan")
    api_key = st.text_input("Masukkan Google Gemini API Key", type="password")
    st.markdown("[Dapatkan API Key di sini](https://aistudio.google.com/app/apikey)")
    
    st.divider()
    topik = st.text_input("Topik Berita", value="Makan Bergizi Gratis")
    wilayah = st.text_input("Wilayah Spesifik", value="Banten")
    hari_kebelakang = st.slider("Cari berita berapa hari ke belakang?", 1, 14, 7)

# --- FUNGSI PENCARIAN BERITA ---
def cari_berita(topik, wilayah, hari):
    query = f"{topik} {wilayah} when:{hari}d"
    url_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={url_query}&hl=id&gl=ID&ceid=ID:id"
    
    feed = feedparser.parse(rss_url)
    berita_list = []
    
    for entry in feed.entries[:10]: # Ambil 10 berita teratas
        berita_list.append(f"- {entry.title} ({entry.link})")
        
    return "\n".join(berita_list)

# --- TOMBOL PROSES ---
if st.button("🚀 Buat Laporan Mingguan"):
    if not api_key:
        st.error("Silakan masukkan Gemini API Key terlebih dahulu di menu sebelah kiri.")
    else:
        with st.spinner("Mencari berita dan menyusun laporan..."):
            try:
                # 1. Tarik Data Berita
                kumpulan_berita = cari_berita(topik, wilayah, hari_kebelakang)
                
                if not kumpulan_berita.strip():
                    st.warning("Tidak ditemukan berita untuk topik dan rentang waktu tersebut.")
                else:
                    # 2. Proses ke Gemini API
                    client = genai.Client(api_key=api_key)
                    
                    prompt = f"""
                    Anda adalah analis kebijakan. Berikut adalah daftar berita 
                    tentang '{topik}' di wilayah '{wilayah}' selama {hari_kebelakang} hari terakhir:
                    
                    {kumpulan_berita}
                    
                    Buatkan laporan mingguan dengan format baku berikut:
                    ISU STRATEGIS
                    • [1 kalimat per isu spesifik wilayah - jika tidak relevan, abaikan]
                    REKOMENDASI
                    • [1 kalimat: SIAPA (aktor kebijakan) + APA (tindakan konkret) untuk setiap isu di atas]
                    
                    Pastikan mencantumkan sumber link berita di bawah setiap isu.
                    """
                    
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt
                    )
                    
                    # 3. Tampilkan Hasil
                    st.success("Laporan Berhasil Dibuat!")
                    st.markdown("### Hasil Laporan Mingguan")
                    st.markdown(response.text)
                    
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")

5. Klik **Save**.

### Langkah 2: Sesuaikan Kode di `app.py`
Sekarang, kita buat aplikasinya mengambil kunci tersebut secara otomatis dari brankas rahasia, bukan lagi dari input pengguna di layar. 

Ubah sedikit kode `app.py` Anda di GitHub. Hapus bagian input API Key di *sidebar* dan ubah logika pemanggilannya menjadi seperti ini:

```python
import streamlit as st
import feedparser
import urllib.parse
from google import genai

# --- MENGAMBIL API KEY SECARA OTOMATIS ---
api_key = st.secrets["GEMINI_API_KEY"]

# --- KONFIGURASI ANTARMUKA (UI) ---
st.set_page_config(page_title="Generator Weekly Report Banten", page_icon="📰")
st.title("📰 Generator Laporan Mingguan Otomatis")

# --- SIDEBAR UNTUK PENGATURAN ---
with st.sidebar:
    st.header("⚙️ Pengaturan")
    # Input API Key dihapus karena sudah otomatis
    topik = st.text_input("Topik Berita", value="Makan Bergizi Gratis")
    wilayah = st.text_input("Wilayah Spesifik", value="Banten")
    hari_kebelakang = st.slider("Cari berita berapa hari ke belakang?", 1, 14, 7)

# ... (Fungsi cari_berita tetap sama) ...

# --- TOMBOL PROSES ---
if st.button("🚀 Buat Laporan Mingguan"):
    with st.spinner("Mencari berita dan menyusun laporan..."):
        try:
            kumpulan_berita = cari_berita(topik, wilayah, hari_kebelakang)
            
            if not kumpulan_berita.strip():
                st.warning("Tidak ditemukan berita untuk topik dan rentang waktu tersebut.")
            else:
                # Klien langsung menggunakan api_key dari rahasia server
                client = genai.Client(api_key=api_key)
                
                # ... (Sisa kode pemrosesan AI tetap sama) ...
