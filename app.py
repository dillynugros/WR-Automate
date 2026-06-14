import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta, timezone
from google import genai

# --- MENGAMBIL API KEY SECARA OTOMATIS ---
gemini_api_key = st.secrets["GEMINI_API_KEY"]
gnews_api_key = st.secrets["GNEWS_API_KEY"]

# --- KONFIGURASI ANTARMUKA (UI) ---
st.set_page_config(page_title="Generator Weekly Report Banten", page_icon="📰", layout="wide")

st.markdown("""
    <style>
    .stMarkdown p, .stMarkdown a {
        word-wrap: break-word;
        overflow-wrap: break-word;
        white-space: pre-wrap;
    }
    div.stButton > button {
        background-color: #1E3A8A;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
    }
    div.stButton > button:hover {
        background-color: #0056b3;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📰 Generator Laporan Mingguan Otomatis")
st.markdown("Aplikasi ini menarik berita terkini via API resmi dan menggunakan Gemini AI untuk menyusun Isu Strategis & Rekomendasi.")

# --- SIDEBAR UNTUK PENGATURAN ---
with st.sidebar:
    st.header("⚙️ Pengaturan")
    topik = st.text_input("Topik Berita", value="Makan Bergizi Gratis")
    wilayah = st.text_input("Wilayah Spesifik", value="Banten")
    hari_kebelakang = st.slider("Cari berita berapa hari ke belakang?", 1, 30, 7)

# --- FUNGSI PENCARIAN BERITA (GNEWS API RESMI + FILTER MEDIA BESAR) ---
def cari_berita_api(topik, wilayah, hari):
    query = f'"{topik}" AND "{wilayah}"'
    url_query = urllib.parse.quote(query)
    
    # Kalkulasi batas waktu mundur sesuai slider (Format ISO 8601 UTC)
    waktu_mulai = (datetime.now(timezone.utc) - timedelta(days=hari)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Endpoint GNews API
    url = f"https://gnews.io/api/v4/search?q={url_query}&lang=id&country=id&max=20&from={waktu_mulai}&apikey={gnews_api_key}"
    
    berita_asli = []
    
    # DAFTAR PUTIH (WHITELIST) MEDIA BESAR KREDIBEL
    media_besar = [
        "kompas.com", "detik.com", "tempo.co", "antaranews.com", 
        "cnnindonesia.com", "republika.co.id", "bisnis.com", 
        "cnbcindonesia.com", "kontan.co.id", "investor.id", 
        "liputan6.com", "kumparan.com", "tirto.id", "merdeka.com", 
        "jawapos.com", "suara.com", "tribunnews.com", "pikiran-rakyat.com"
    ]
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            for article in articles:
                title = article.get('title', 'Tanpa Judul')
                link = article.get('url', '')
                source_name = article.get('source', {}).get('name', '').lower()
                
                if link:
                    # CEK VALIDITAS: URL atau nama sumber media harus ada di daftar putih
                    link_lower = link.lower()
                    if any(domain in link_lower for domain in media_besar) or any(domain in source_name for domain in media_besar):
                        berita_asli.append(f"- {title} ({link})")
                        
                    if len(berita_asli) >= 10:
                        break
                        
            return "\n".join(berita_asli)
        else:
            return f"ERROR_API: Kode {response.status_code} - Terjadi masalah pada server berita."
            
    except Exception as e:
        return f"ERROR_REQ: Terputus dari jaringan - {e}"

# --- TOMBOL PROSES ---
if st.button("🚀 Buat Laporan Mingguan"):
    with st.spinner("Mengunduh data berita dari API Resmi dan menyusun laporan..."):
        try:
            kumpulan_berita = cari_berita_api(topik, wilayah, hari_kebelakang)
            
            if "ERROR_" in kumpulan_berita:
                st.error(f"Gagal menarik data: {kumpulan_berita}")
            elif not kumpulan_berita.strip():
                st.warning(f"Sesuai parameter yang diminta, tidak ada pemberitaan dari media terverifikasi terkait isu '{topik}' spesifik di '{wilayah}' dalam periode waktu tersebut.")
            else:
                client = genai.Client(api_key=gemini_api_key)
                
                prompt = f"""
                Anda adalah analis kebijakan. Berikut adalah daftar berita VALID dengan tautan langsung 
                tentang '{topik}' di wilayah '{wilayah}':
                
                {kumpulan_berita}
                
                Buatkan laporan mingguan dengan format baku berikut:
                ISU STRATEGIS
                • [1 kalimat per isu spesifik wilayah - jika tidak relevan, abaikan]
                REKOMENDASI
                • [1 kalimat: SIAPA (aktor kebijakan) + APA (tindakan konkret) untuk setiap isu di atas]
                
                PENTING:
                1. Pastikan mencantumkan sumber link berita persis di bawah setiap isu.
                2. JANGAN PERNAH menyajikan hasil di dalam format 'code block' (tanda ```). Tuliskan semuanya sebagai teks paragraf biasa.
                3. Jangan mengarang informasi. Berpegang teguh HANYA pada daftar berita di atas.
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                
                st.success("Laporan Berhasil Dibuat dengan Data API Valid!")
                st.markdown("### Hasil Laporan Mingguan")
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"Terjadi kesalahan teknis pada kecerdasan buatan: {e}")
