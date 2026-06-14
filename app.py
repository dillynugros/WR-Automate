import streamlit as st
import feedparser
import urllib.parse
import requests
from google import genai

# --- MENGAMBIL API KEY SECARA OTOMATIS ---
api_key = st.secrets["GEMINI_API_KEY"]

# --- KONFIGURASI ANTARMUKA (UI) ---
st.set_page_config(page_title="Generator Weekly Report Banten", page_icon="📰", layout="wide")

# --- INJEKSI CSS CUSTOM UNTUK TEMA & WRAPPING ---
st.markdown("""
    <style>
    /* Memaksa teks dan link panjang untuk turun ke bawah (wrap) */
    .stMarkdown p, .stMarkdown a {
        word-wrap: break-word;
        overflow-wrap: break-word;
        white-space: pre-wrap;
    }
    
    /* Tombol Biru Profesional */
    div.stButton > button {
        background-color: #1E3A8A; /* Biru Gelap Profesional */
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
    }
    div.stButton > button:hover {
        background-color: #0056b3; /* Biru Terang saat Disorot */
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📰 Generator Laporan Mingguan Otomatis")
st.markdown("Aplikasi ini menarik berita terkini dan menggunakan Gemini AI untuk menyusun Isu Strategis & Rekomendasi.")

# --- SIDEBAR UNTUK PENGATURAN ---
with st.sidebar:
    st.header("⚙️ Pengaturan")
    topik = st.text_input("Topik Berita", value="Makan Bergizi Gratis")
    wilayah = st.text_input("Wilayah Spesifik", value="Banten")
    
    # Range slider diperpanjang hingga 30 hari
    hari_kebelakang = st.slider("Cari berita berapa hari ke belakang?", 1, 30, 7)

# --- FUNGSI PENCARIAN & VALIDASI BERITA ---
def cari_berita(topik, wilayah, hari):
    query = f'"{topik}" {wilayah} when:{hari}d'
    url_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={url_query}&hl=id&gl=ID&ceid=ID:id"
    
    feed = feedparser.parse(rss_url)
    berita_valid = []
    
    # Menyamar sebagai browser biasa agar tidak diblokir oleh media online
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    if getattr(feed, 'entries', None):
        for entry in feed.entries:
            # Jika sudah dapat 10 berita valid, hentikan pencarian
            if len(berita_valid) >= 10:
                break
                
            title = getattr(entry, 'title', 'Tanpa Judul')
            link = getattr(entry, 'link', '#')
            
            if link != '#' and "news.google.com" in link:
                try:
                    # Skrip "mengetuk" tautan untuk memastikan webnya tidak error
                    # Menggunakan timeout 5 detik agar aplikasi tidak macet menunggu web lemot
                    response = requests.get(link, headers=headers, timeout=5, allow_redirects=True)
                    
                    # Jika status 200 (OK), masukkan ke dalam daftar
                    if response.status_code == 200:
                        berita_valid.append(f"- {title} ({link})")
                except requests.RequestException:
                    # Jika tautan mati, error, atau lemot, abaikan dan lanjut ke berita berikutnya
                    continue
            
    return "\n".join(berita_valid)

# --- TOMBOL PROSES ---
if st.button("🚀 Buat Laporan Mingguan"):
    with st.spinner("Mencari berita, memvalidasi tautan, dan menyusun laporan..."):
        try:
            # 1. Tarik & Validasi Data Berita
            kumpulan_berita = cari_berita(topik, wilayah, hari_kebelakang)
            
            # 2. Jujur jika tidak ada berita valid
            if not kumpulan_berita.strip():
                st.warning(f"Sesuai parameter yang diminta, tidak ada pemberitaan valid atau akuntabel terkait isu '{topik}' spesifik di '{wilayah}' dalam {hari_kebelakang} hari terakhir.")
            else:
                # 3. Proses ke Gemini API hanya jika ada berita valid
                client = genai.Client(api_key=api_key)
                
                prompt = f"""
                Anda adalah analis kebijakan. Berikut adalah daftar berita VALID 
                tentang '{topik}' di wilayah '{wilayah}' selama {hari_kebelakang} hari terakhir:
                
                {kumpulan_berita}
                
                Buatkan laporan mingguan dengan format baku berikut:
                ISU STRATEGIS
                • [1 kalimat per isu spesifik wilayah - jika tidak relevan, abaikan]
                REKOMENDASI
                • [1 kalimat: SIAPA (aktor kebijakan) + APA (tindakan konkret) untuk setiap isu di atas]
                
                PENTING:
                1. Pastikan mencantumkan sumber link berita persis di bawah setiap isu.
                2. JANGAN PERNAH menyajikan hasil di dalam format 'code block' (tanda ```). Tuliskan semuanya sebagai teks paragraf biasa.
                3. Jangan mengarang informasi. Berpegang teguh HANYA pada berita yang diberikan.
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                
                # Tampilkan Hasil
                st.success("Laporan Berhasil Dibuat dengan sumber berita tervalidasi!")
                st.markdown("### Hasil Laporan Mingguan")
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"Terjadi kesalahan teknis: {e}")
