import streamlit as st
import time
from duckduckgo_search import DDGS
from google import genai

# --- MENGAMBIL API KEY SECARA OTOMATIS ---
api_key = st.secrets["GEMINI_API_KEY"]

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
st.markdown("Aplikasi ini menarik berita terkini dan menggunakan Gemini AI untuk menyusun Isu Strategis & Rekomendasi.")

# --- SIDEBAR UNTUK PENGATURAN ---
with st.sidebar:
    st.header("⚙️ Pengaturan")
    topik = st.text_input("Topik Berita", value="Makan Bergizi Gratis")
    wilayah = st.text_input("Wilayah Spesifik", value="Banten")
    hari_kebelakang = st.slider("Cari berita berapa hari ke belakang?", 1, 30, 7)

# --- FUNGSI PENCARIAN BERITA (DENGAN SILENT RETRY) ---
def cari_berita(topik, wilayah, hari):
    query = f'"{topik}" {wilayah}'
    
    if hari <= 1:
        rentang = "d"
    elif hari <= 7:
        rentang = "w"
    else:
        rentang = "m"
        
    berita_asli = []
    
    # Maksimal percobaan diam-diam jika server menolak
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # Gunakan context manager (with) agar koneksi langsung ditutup rapi
            with DDGS() as ddgs:
                results = list(ddgs.news(keywords=query, region="id-id", safesearch="off", timelimit=rentang, max_results=10))
                
                if results:
                    for r in results:
                        title = r.get('title', 'Tanpa Judul')
                        link = r.get('url', '')
                        if link:
                            berita_asli.append(f"- {title} ({link})")
                            
                return "\n".join(berita_asli)
                
        except Exception:
            # Jika gagal (diblokir server), aplikasi tidak langsung error.
            # Aplikasi akan istirahat 3 detik lalu mencoba lagi di background.
            if attempt < max_retries - 1:
                time.sleep(3)
                continue
            else:
                # Jika 3x dicoba masih gagal mutlak, kirim sinyal error
                return "ERROR_DDG"

# --- TOMBOL PROSES ---
if st.button("🚀 Buat Laporan Mingguan"):
    with st.spinner("Mencari URL berita asli dan menyusun laporan..."):
        try:
            kumpulan_berita = cari_berita(topik, wilayah, hari_kebelakang)
            
            if "ERROR_DDG" in kumpulan_berita:
                # Pesan error diperhalus dan memberikan instruksi jelas, bukan error sistem mentah
                st.warning("Mohon maaf, sistem anti-bot DuckDuckGo sedang mengetatkan penjagaan. Mohon tunggu 1-2 menit sebelum menekan tombol kembali.")
            elif not kumpulan_berita.strip():
                st.info(f"Benar-benar TIDAK DITEMUKAN berita terkait isu '{topik}' spesifik di '{wilayah}' dalam {hari_kebelakang} hari terakhir pada mesin pencari berita.")
            else:
                client = genai.Client(api_key=api_key)
                
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
                
                st.success("Laporan Berhasil Dibuat!")
                st.markdown("### Hasil Laporan Mingguan")
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"Terjadi kesalahan teknis pada pemrosesan teks: {e}")
