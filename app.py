import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components
import datetime

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
    "tasyaameliaa05@gmail.com": {"nama": "Tasya Amelia", "pin": "1234"},
    "mahesaagusta28@gmail.com": {"nama": "Mahesa Agusta", "pin": "1234"}
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
    # --- HEADER ---
    col_head1, col_head2 = st.columns([4, 1])
    with col_head1:
        st.markdown("### V2 Pre Load 2026")
    with col_head2:
        st.text(f"👤 {st.session_state.user_nama}")
        
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

    try:
        df_database = load_data()
    except Exception as e:
        st.error("❌ Gagal terhubung ke Google Sheets. Detail Error:")
        st.exception(e)
        df_database = pd.DataFrame()

    # --- SIDEBAR: NAVIGASI UTAMA ---
    st.sidebar.markdown("### 🗂️ Menu Navigasi")
    menu_pilihan = st.sidebar.radio(
        "Pilih Halaman Utama:",
        ["Summary Status", "Operasional Cabang"],
        label_visibility="collapsed"
    )

    st.sidebar.divider()

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
        st.title(f"Cabang - {wilayah}")

        if not df_database.empty and "Tujuan Pengiriman" in df_database.columns:
            df_filtered = df_database[df_database["Tujuan Pengiriman"] == wilayah].copy()
        else:
            df_filtered = pd.DataFrame()

        if not df_filtered.empty and "Jumlah Box" in df_filtered.columns:
            df_filtered["Jumlah Box"] = df_filtered["Jumlah Box"].fillna(0).astype(int)

        # Tab diubah fokus utamanya ke Preload menggantikan Picking
        tab_id, tab_preload, tab_ondelivery = st.tabs([
            "ID Request", "Preload (Scan & Manifest)", "On Delivery"
        ])

        with tab_id:
            st.subheader(f"Data Logistik & Pencarian ID - {wilayah}")
            keyword_cari = st.text_input("🔍 Cari ID Request:", placeholder="Ketik ID Request yang ingin dicari...", key="search_id_request")
            
            df_display = df_filtered.copy()
            if keyword_cari and not df_display.empty:
                id_col_candidates = [col for col in df_display.columns if 'id' in col.lower() or 'request' in col.lower()]
                if id_col_candidates:
                    target_col = id_col_candidates[0]
                    df_display = df_display[df_display[target_col].astype(str).str.contains(keyword_cari, case=False, na=False)]

            if not df_display.empty:
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.info("Tidak ada data logistik yang cocok atau tersedia untuk cabang ini.")

        with tab_preload:
            st.subheader(f"Proses Preload & Scanning - {wilayah}")
            st.markdown("Scan ID Request untuk memperbarui data **Loader**, **Waktu Preload**, dan **Status** langsung ke Google Sheets.")

            # Input Scan untuk Preload
            input_widget_key = f"input_preload_scan_{wilayah}"
            if input_widget_key not in st.session_state:
                st.session_state[input_widget_key] = ""

            def proses_scan_preload():
                scan_input = st.session_state[input_widget_key].strip()
                if not scan_input:
                    return
                
                # Muat ulang data terbaru dari Google Sheets untuk menghindari konflik state lama
                df_current_db = load_data()
                
                if not df_current_db.empty:
                    id_col_candidates = [col for col in df_current_db.columns if col.lower() in ['id', 'id request']]
                    id_col = id_col_candidates[0] if id_col_candidates else df_current_db.columns[0]
                    
                    # Konversi kolom ID ke string untuk pencocokan yang akurat
                    global_mask = df_current_db[id_col].astype(str).str.split('.').str[0].str.strip() == scan_input
                    
                    if global_mask.any():
                        now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
                        current_datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Pastikan kolom target bertipe string
                        for col_target in ["Loader", "Waktu Preload", "Status"]:
                            if col_target in df_current_db.columns:
                                df_current_db[col_target] = df_current_db[col_target].astype(str)
                        
                        # Hanya update kolom Loader, Waktu Preload, dan Status (biarkan kolom A:E tetap utuh)
                        if "Loader" in df_current_db.columns:
                            df_current_db.loc[global_mask, "Loader"] = str(st.session_state.user_nama)
                        if "Waktu Preload" in df_current_db.columns:
                            df_current_db.loc[global_mask, "Waktu Preload"] = current_datetime_str
                        if "Status" in df_current_db.columns:
                            df_current_db.loc[global_mask, "Status"] = "Preloaded"
                        
                        try:
                            conn.update(worksheet="Database log", data=df_current_db)
                            st.session_state[f"last_msg_{wilayah}"] = ("success", f"✅ ID **{scan_input}** berhasil di-preload oleh {st.session_state.user_nama} pada {current_datetime_str}!")
                            st.session_state[f"sound_effect_{wilayah}"] = "success"
                        except Exception as e:
                            st.session_state[f"last_msg_{wilayah}"] = ("error", f"❌ Gagal memperbarui Google Sheets: {e}")
                    else:
                        st.session_state[f"last_msg_{wilayah}"] = ("error", f"❌ ID **{scan_input}** tidak ditemukan di database.")
                        st.session_state[f"sound_effect_{wilayah}"] = "error"
                
                st.session_state[input_widget_key] = ""

            st.text_input(
                "📷 Scan / Masukkan ID Request untuk Preload:", 
                placeholder="Arahkan scanner atau ketik ID lalu tekan Enter...", 
                key=input_widget_key,
                on_change=proses_scan_preload
            )

            # Menampilkan notifikasi & suara hasil scan
            if f"last_msg_{wilayah}" in st.session_state:
                m_type, m_text = st.session_state[f"last_msg_{wilayah}"]
                if m_type == "success":
                    st.success(m_text)
                else:
                    st.error(m_text)
                del st.session_state[f"last_msg_{wilayah}"]

            if f"sound_effect_{wilayah}" in st.session_state:
                sound_type = st.session_state[f"sound_effect_{wilayah}"]
                if sound_type == "success":
                    audio_html = '<audio autoplay><source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg"></audio>'
                else:
                    audio_html = '<audio autoplay><source src="https://assets.mixkit.co/active_storage/sfx/2957/2957-preview.mp3" type="audio/mpeg"></audio>'
                st.markdown(audio_html, unsafe_allow_html=True)
                del st.session_state[f"sound_effect_{wilayah}"]

            st.markdown("---")
            st.markdown(f"##### 📋 Data Riwayat Preload Cabang: {wilayah}")
            
            if not df_filtered.empty:
                # Sembunyikan kolom Jam Proses Scan dan Tanggal Proses Scan dari tampilan tab Preload
                df_preload_display = df_filtered.copy()
                kolom_dihapus = ["Jam Proses Scan", "Tanggal Proses Scan"]
                for col in kolom_dihapus:
                    if col in df_preload_display.columns:
                        df_preload_display = df_preload_display.drop(columns=[col])
                
                st.dataframe(df_preload_display, use_container_width=True, hide_index=True)
            else:
                st.info("Belum ada data logistik untuk ditampilkan pada cabang ini.")

        with tab_ondelivery:
            st.subheader(f"Proses On Delivery - {wilayah}")
            st.write("Daftar pengiriman barang yang siap dikirim:")
            
            df_delivery = pd.DataFrame([
                {"ID Request": "588834", "Tujuan": wilayah, "Status": "Ready for Delivery"}
            ])
            st.dataframe(df_delivery, use_container_width=True, hide_index=True)
