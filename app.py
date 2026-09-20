import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components

# Konfigurasi halaman agar menggunakan mode 'wide' (lebar) ala dashboard
st.set_page_config(page_title="V2 Pre Load", layout="wide")

# --- KAMUS DATA PENGGUNA (User Dictionary) ---
USER_DATABASE = {
    "riri.jaknot@gmail.com": {"nama": "Riri Ridwan Genta Yudha", "pin": "1234"},
    "adamrayhan.jaknot@gmail.com": {"nama": "Adam Rayhan", "pin": "1234"},
    "satriopjn@gmail.com": {"nama": "Satrio Sudiyanto", "pin": "1234"},
    "ahmadallfiansc@gmail.com": {"nama": "Ahmad Alfian", "pin": "1234"},
    "ajikurnianto93@gmail.com": {"nama": "Aji Kurnianto", "pin": "1234"},
    "alekhandoko98@gmail.com": {"nama": "Alek Handoko", "pin": "1234"},
    "alghifariathian@gmail.com": {"nama": "Athian Alghifari", "pin": "1234"},
    "amelyaadm@gmail.com": {"nama": "Amelya Putri", "pin": "1234"},
    "ardi03027@gmail.com": {"nama": "Eka Febri Setiardi", "pin": "1234"},
    "arifsa2703@gmail.com": {"nama": "Arif Saputra", "pin": "1234"},
    "bedhel089f@gmail.com": {"nama": "Fadhilah Al Azani", "pin": "1234"},
    "olifiaekmanda7@gmail.com": {"nama": "Olifia Ekmanda", "pin": "1234"},
    "rayadiagung22@gmail.com": {"nama": "Rayadi Agung", "pin": "1234"},
    "siwhayy170@gmail.com": {"nama": "Wahyu Adi Sucipto", "pin": "1234"},
    "tasyaameliaa05@gmail.com": {"nama": "Tasya Amelia", "pin": "1234"}
}

# --- INISIALISASI SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "user_nama" not in st.session_state:
    st.session_state.user_nama = ""

# --- KONEKSI GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Fungsi untuk membaca data dari sheet "Database log"
def load_data():
    # ttl=0 memastikan data dibaca secara real-time tanpa cache yang lama
    df = conn.read(worksheet="Database log", ttl=0)
    return df

# --- FUNGSI HALAMAN LOGIN ---
def tampilkan_halaman_login():
    st.markdown("<h2 style='text-align: center;'>🔐 Login V2 Pre Load System</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Silakan masukkan email terdaftar dan PIN Anda.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("form_login"):
            email_input = st.text_input("Email Pengguna").strip().lower()
            pin_input = st.text_input("PIN / Password", type="password")
            submit_btn = st.form_submit_button("Masuk (Login)", use_container_width=True)
            
            if submit_btn:
                if email_input in USER_DATABASE and USER_DATABASE[email_input]["pin"] == pin_input:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email_input
                    st.session_state.user_nama = USER_DATABASE[email_input]["nama"]
                    st.success(f"Login berhasil! Selamat datang, {st.session_state.user_nama}")
                    st.rerun()
                else:
                    st.error("Email atau PIN salah. Silakan periksa kembali.")

# --- KONTROL UTAMA: CEK STATUS LOGIN ---
if not st.session_state.logged_in:
    tampilkan_halaman_login()
else:
    # =========================================================================
    # KODE DASHBOARD UTAMA (Hanya tampil jika sudah login)
    # =========================================================================

    # --- HEADER ---
    col_head1, col_head2 = st.columns([4, 1])
    with col_head1:
        st.markdown("### V2 Pre Load 2026")
    with col_head2:
        st.text(f"👤 {st.session_state.user_nama}")
        
        # Komponen HTML + JS untuk Jam & Tanggal Live berdetik
        components.html("""
        <div style="font-family: sans-serif; font-size: 13px; color: #31333F; margin-top: -10px;">
            🕒 <span id="live-clock">Loading...</span>
        </div>
        <script>
        function updateClock() {
            const now = new Date();
            const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            
            const dayName = days[now.getDay()];
            const dayNum = String(now.getDate()).padStart(2, '0');
            const monthName = months[now.getMonth()];
            const year = now.getFullYear();
            
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const seconds = String(now.getSeconds()).padStart(2, '0');
            
            const timeString = `${dayName}, ${dayNum} ${monthName} ${year}, ${hours}:${minutes}:${seconds}`;
            document.getElementById('live-clock').innerText = timeString;
        }
        setInterval(updateClock, 1000);
        updateClock();
        </script>
        """, height=30)

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state.user_nama = ""
            st.rerun()

    st.divider()

    # --- SIDEBAR (Menu Vertikal: Wilayah / Tujuan Pengiriman) ---
    st.sidebar.header("Tujuan Pengiriman")
    wilayah = st.sidebar.radio(
        "Pilih Cabang:",
        [
            "Jakarta Pusat", "Jakarta Barat", "Jakarta Utara", 
            "Tangerang", "Cikupa", "Bandung", "Semarang", 
            "Surabaya Timur", "Surabaya Barat", "Yogyakarta", 
            "Makassar", "Medan", "Official Store"
        ]
    )

    st.title(f"Cabang - {wilayah}")

# --- AMBIL DATA DARI GOOGLE SHEETS ---
try:
    df_database = load_data()
    if not df_database.empty and "Tujuan Pengiriman" in df_database.columns:
        df_filtered = df_database[df_database["Tujuan Pengiriman"] == wilayah]
    else:
        df_filtered = pd.DataFrame()
        st.warning("⚠️ Berhasil terhubung, tetapi kolom 'Tujuan Pengiriman' tidak ditemukan atau data kosong.")
except Exception as e:
    # Ini akan menampilkan teks error asli secara mendetail di layar aplikasi
    st.error("❌ Gagal terhubung ke Google Sheets. Detail Error:")
    st.exception(e)
    df_database = pd.DataFrame()
    df_filtered = pd.DataFrame()
    # --- TAB UTAMA (Horizontal Tabs) ---
    tab_summary, tab_pick, tab_preload, tab_ondelivery = st.tabs([
        "Summary Status", "Picking", "Preload", "On Delivery"
    ])

    with tab_summary:
        st.subheader(f"Summary Status untuk {wilayah}")
        st.metric("Total Log Data Cabang Ini", len(df_filtered))

    with tab_pick:
        st.subheader("Proses Picking")
        id_picking = st.text_input("Input ID Request", key="input_picking")
        
        st.markdown("##### Data Logistik Sesuai Cabang")
        # Menampilkan data dari Google Sheet yang sudah difilter sesuai cabang
        st.dataframe(df_filtered, use_container_width=True)

    with tab_preload:
        st.subheader("Proses Preload")
        
        if st.button("📦 Buat Manifest Baru"):
            st.success("Manifest baru berhasil dibuat!")

        daftar_manifest = ["MNF-001", "MNF-002", "MNF-003"]
        manifest_terpilih = st.selectbox("Pilih Nomor Manifest untuk Input ID:", daftar_manifest)
        
        if manifest_terpilih:
            st.info(f"Kolom input aktif untuk Manifest: **{manifest_terpilih}**")
            st.text_input(f"Input ID Request untuk {manifest_terpilih}", key=f"input_{manifest_terpilih}")

        st.markdown("##### Daftar Manifest Preload")
        df_preload = pd.DataFrame({
            "ID Manifest": ["MNF-001", "MNF-001", "MNF-002"],
            "ID Request": ["REQ-001", "REQ-002", "REQ-003"], 
            "Jumlah Box": [5, 12, 8], 
            "Status": ["Ready", "Ready", "Pending"],
            "Zona Mezzanine": ["Zone A", "Zone B", "Zone A"]
        })
        st.data_editor(df_preload, key="editor_preload_manifest")

    with tab_ondelivery:
        st.subheader("Proses On Delivery")
        st.write("Centang kotak di bawah untuk menandai status pengiriman:")
        
        df_delivery = pd.DataFrame([
            {"ID Manifest": "MNF-001", "ID Request": "REQ-001", "Jumlah Box": 5, "Status": "Ready", "Mark as On Delivery": True},
            {"ID Manifest": "MNF-001", "ID Request": "REQ-002", "Jumlah Box": 12, "Status": "Process", "Mark as On Delivery": False}
        ])
        st.dataframe(df_delivery)
