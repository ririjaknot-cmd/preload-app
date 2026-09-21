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
        <div style="font-family: sans-serif; font-size: 13px; color: #FFFFFF; margin-top: -10px;">
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

    # --- AMBIL DATA DARI GOOGLE SHEETS TERLEBIH DAHULU ---
    try:
        df_database = load_data()
    except Exception as e:
        st.error("❌ Gagal terhubung ke Google Sheets. Detail Error:")
        st.exception(e)
        df_database = pd.DataFrame()

    # --- SIDEBAR: NAVIGASI UTAMA & PEMISAHAN MENU ---
    st.sidebar.markdown("### 🗂️ Menu Navigasi")
    menu_pilihan = st.sidebar.radio(
        "Pilih Halaman Utama:",
        ["Summary Status", "Operasional Cabang"],
        label_visibility="collapsed"
    )

    st.sidebar.divider()

    # Variabel penampung wilayah/cabang aktif
    wilayah = None

    if menu_pilihan == "Operasional Cabang":
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

    # --- LOGIKA TAMPILAN BERDASARKAN MENU SIDEBAR ---
    if menu_pilihan == "Summary Status":
        st.title("📊 Summary Status Semua Cabang")
        st.markdown("Berikut adalah daftar seluruh cabang tujuan pengiriman beserta total jumlah box-nya.")

        if not df_database.empty and "Tujuan Pengiriman" in df_database.columns:
            if "Jumlah Box" in df_database.columns:
                df_summary = df_database.groupby("Tujuan Pengiriman")["Jumlah Box"].sum().reset_index()
                df_summary.columns = ["Tujuan Pengiriman", "Total Jumlah Box"]
            else:
                df_summary = df_database.groupby("Tujuan Pengiriman").size().reset_index(name="Total Log Data")

            st.dataframe(df_summary, use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ Data dari Google Sheets kosong atau kolom 'Tujuan Pengiriman' tidak ditemukan.")

    else:
        # Tampilan Operasional Cabang
        st.title(f"Cabang - {wilayah}")

        if not df_database.empty and "Tujuan Pengiriman" in df_database.columns:
            df_filtered = df_database[df_database["Tujuan Pengiriman"] == wilayah].copy()
        else:
            df_filtered = pd.DataFrame()

        # Terapkan format "Jumlah Box" menjadi angka biasa (tanpa tanda kurung) untuk tab ID
        if not df_filtered.empty and "Jumlah Box" in df_filtered.columns:
            # Mengubah nilai box menjadi integer, lalu dikonversi ke string biasa
            df_filtered["Jumlah Box"] = df_filtered["Jumlah Box"].fillna(0).astype(int)

        # --- TAB UTAMA (Horizontal Tabs): Tambah Tab "ID" di sebelah kiri ---
        tab_id, tab_pick, tab_preload, tab_ondelivery = st.tabs([
            "ID", "Picking", "Preload", "On Delivery"
        ])

        with tab_id:
            st.subheader(f"Data Logistik & Pencarian ID - {wilayah}")

            # Kolom Pencarian ID Request di atas list
            keyword_cari = st.text_input("🔍 Cari ID Request:", placeholder="Ketik ID Request yang ingin dicari...", key="search_id_request")

            df_display = df_filtered.copy()

            # Logika filter pencarian jika kolom ID Request ada
            if keyword_cari and not df_display.empty:
                # Cari kolom yang mirip dengan ID Request (misal: 'ID Request', 'Request ID', atau 'ID')
                id_col_candidates = [col for col in df_display.columns if 'id' in col.lower() or 'request' in col.lower()]
                if id_col_candidates:
                    target_col = id_col_candidates[0]
                    df_display = df_display[df_display[target_col].astype(str).str.contains(keyword_cari, case=False, na=False)]

            if not df_display.empty:
                # Menampilkan dataframe dengan hide_index=True agar lebih rapi tanpa kolom index
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.info("Tidak ada data logistik yang cocok atau tersedia untuk cabang ini.")

        with tab_pick:
            st.subheader(f"Proses Picking - {wilayah}")
            id_picking = st.text_input("Input ID Request", key="input_picking")
            st.markdown("##### Panel Kontrol Picking Aktif")
            st.write("Silakan masukkan ID Request di atas untuk memproses data picking cabang ini.")
            
            # Kolom Input Scan / Ketik ID Request
            scan_input = st.text_input("📷 Scan / Masukkan ID Request:", placeholder="Arahkan scanner ke barcode atau ketik ID...", key="input_picking_scan")

            if scan_input:
                # Cek apakah ID Request ada di data cabang ini
                if not df_filtered.empty:
                    # Asumsikan kolom ID Request bernama 'ID Request' atau sesuaikan dengan kolom di Sheet Anda
                    id_col = [col for col in df_filtered.columns if 'id' in col.lower() and 'request' in col.lower()]
                    
                    if id_col:
                        target_col = id_col[0]
                        # Cek apakah ID yang di-scan ada di data
                        match_data = df_filtered[df_filtered[target_col].astype(str).str.strip() == scan_input.strip()]
                        
                        if not match_data.empty:
                            st.success(f"✅ ID Request **{scan_input}** ditemukan dan berhasil divalidasi!")
                            # Di sini nanti status di Google Sheets bisa di-update otomatis menjadi 'Completed' / 'Picked'
                        else:
                            st.error(f"❌ ID Request **{scan_input}** tidak ditemukan di data cabang {wilayah}!")
                    else:
                        st.warning("⚠️ Kolom ID Request tidak terdeteksi pada struktur data sheet.")

            st.markdown("##### 📋 Daftar Monitoring Status Picking")
            
            if not df_filtered.empty:
                # Menambahkan kolom status tiruan (atau ambil dari database jika sudah ada kolom statusnya)
                df_picking_view = df_filtered.copy()
                
                # Contoh penambahan kolom status visual jika belum ada di sheet
                if "Status Picking" not in df_picking_view.columns:
                    df_picking_view["Status Picking"] = "Belum (Pending)" # Default merah/pending

                # Fungsi styling warna baris untuk st.dataframe
                def color_status(val):
                    if val == "Komplit" or val == "Ready":
                        return 'background-color: #d4edda; color: #155724;' # Hijau soft
                    elif val == "Proses":
                        return 'background-color: #fff3cd; color: #856404;' # Kuning soft
                    else:
                        return 'background-color: #f8d7da; color: #721c24;' # Merah soft

                # Tampilkan data dengan format tanpa index
                st.dataframe(
                    df_picking_view, 
                    use_container_width=True, 
                    hide_index=True
                )
            else:
                st.info("Belum ada data logistik untuk ditampilkan pada cabang ini.")

        with tab_preload:
            st.subheader(f"Proses Preload - {wilayah}")

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
                "Jumlah Box": ["5/5", "12/12", "8/8"], 
                "Status": ["Ready", "Ready", "Pending"],
                "Zona Mezzanine": ["Zone A", "Zone B", "Zone A"]
            })
            st.dataframe(df_preload, use_container_width=True, hide_index=True)

        with tab_ondelivery:
            st.subheader(f"Proses On Delivery - {wilayah}")
            st.write("Centang kotak di bawah untuk menandai status pengiriman:")

            df_delivery = pd.DataFrame([
                {"ID Manifest": "MNF-001", "ID Request": "REQ-001", "Jumlah Box": "5/5", "Status": "Ready", "Mark as On Delivery": True},
                {"ID Manifest": "MNF-001", "ID Request": "REQ-002", "Jumlah Box": "12/12", "Status": "Process", "Mark as On Delivery": False}
            ])
            st.dataframe(df_delivery, use_container_width=True, hide_index=True)
