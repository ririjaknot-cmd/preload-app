import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components
import datetime
import gspread
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
            st.markdown("Gunakan **Scan Satuan** atau **Input ID & Jumlah Box** untuk memperbarui data ke Google Sheets.")

            # Pilihan Metode Input
            metode_input = st.radio("Pilih Metode Input:", ["Scan Satuan", "Input ID & Jumlah Box"], horizontal=True)

            if metode_input == "Scan Satuan":
                # Input Scan Satuan
                input_widget_key = f"input_preload_scan_{wilayah}"
                if input_widget_key not in st.session_state:
                    st.session_state[input_widget_key] = ""

                def proses_scan_preload():
                    scan_input = st.session_state[input_widget_key].strip()
                    if not scan_input:
                        return
                    
                    try:
                        creds_dict = dict(st.secrets["connections"]["gsheets"])
                        gc = gspread.service_account_from_dict(creds_dict)
                        spreadsheet_name = st.secrets["connections"]["gsheets"].get("spreadsheet")
                        sh = gc.open_by_url(spreadsheet_name) if spreadsheet_name.startswith("http") else gc.open(spreadsheet_name)
                        ws = sh.worksheet("Database log")
                        
                        data_rows = ws.get_all_records()
                        
                        found_row_index = None
                        for idx, row in enumerate(data_rows):
                            row_id = str(row.get("ID") or row.get("id request") or list(row.values())[0]).split('.')[0].strip()
                            if row_id == scan_input:
                                found_row_index = idx + 2
                                break
                        
                        if found_row_index:
                            now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
                            current_datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")
                            current_loader = str(st.session_state.user_nama)
                            current_status = "Preloaded"
                            
                            ws.update_cell(found_row_index, 6, current_loader)       # Kolom F: Loader
                            ws.update_cell(found_row_index, 7, current_datetime_str)  # Kolom G: Waktu Preload
                            ws.update_cell(found_row_index, 9, current_status)        # Kolom I: Status
                            
                            st.session_state[f"last_msg_{wilayah}"] = ("success", f"✅ ID **{scan_input}** berhasil di-preload oleh {current_loader} pada {current_datetime_str}!")
                            st.session_state[f"sound_effect_{wilayah}"] = "success"
                        else:
                            st.session_state[f"last_msg_{wilayah}"] = ("error", f"❌ ID **{scan_input}** tidak ditemukan di database.")
                            st.session_state[f"sound_effect_{wilayah}"] = "error"
                            
                    except Exception as e:
                        st.session_state[f"last_msg_{wilayah}"] = ("error", f"❌ Gagal memperbarui Google Sheets: {e}")
                        st.session_state[f"sound_effect_{wilayah}"] = "error"
                    
                    st.session_state[input_widget_key] = ""

                st.text_input(
                    "📷 Scan / Masukkan ID Request:", 
                    placeholder="Arahkan scanner atau ketik ID lalu tekan Enter...", 
                    key=input_widget_key,
                    on_change=proses_scan_preload
                )

            else:
                # Form input 1 ID tunggal dan Jumlah Box dengan Validasi & Pengamanan Kolom A:E
                form_single_key = f"form_single_box_preload_{wilayah}"
                
                with st.form(key=form_single_key, clear_on_submit=True):
                    input_id_val = st.text_input(
                        "Masukkan ID",
                        placeholder="Ketik atau scan 1 ID di sini..."
                    )
                    jumlah_box_val = st.number_input(
                        "Jumlah Box",
                        min_value=1,
                        value=1,
                        step=1
                    )
                    
                    submit_single = st.form_submit_button("🚀 Proses Preload", type="primary")

                if submit_single:
                    target_id = input_id_val.strip()
                    if not target_id:
                        st.warning("⚠️ Masukkan ID terlebih dahulu.")
                    else:
                        try:
                            creds_dict = dict(st.secrets["connections"]["gsheets"])
                            gc = gspread.service_account_from_dict(creds_dict)
                            spreadsheet_name = st.secrets["connections"]["gsheets"].get("spreadsheet")
                            sh = gc.open_by_url(spreadsheet_name) if spreadsheet_name.startswith("http") else gc.open(spreadsheet_name)
                            ws = sh.worksheet("Database log")
                            
                            data_rows = ws.get_all_records()
                            
                            found_row_index = None
                            current_db_box = None
                            for idx, row in enumerate(data_rows):
                                row_id = str(row.get("ID") or row.get("id request") or list(row.values())[0]).split('.')[0].strip()
                                if row_id == target_id:
                                    found_row_index = idx + 2
                                    # Ambil nilai jumlah box yang ada di database saat ini (Kolom E / key 'Jumlah Box')
                                    current_db_box = row.get("Jumlah Box") or row.get("jumlah box") or list(row.values())[4]
                                    break
                            
                            if found_row_index:
                                # Cek apakah jumlah box yang diinput sama dengan yang sudah ada di database
                                try:
                                    db_box_int = int(str(current_db_box).strip()) if current_db_box not in [None, ""] else None
                                except ValueError:
                                    db_box_int = None

                                if db_box_int is not None and db_box_int == int(jumlah_box_val):
                                    st.warning(f"⚠️ ID **{target_id}** sudah memiliki Jumlah Box **{jumlah_box_val}** di database. Input ditolak karena tidak ada perubahan.")
                                    st.session_state[f"sound_effect_{wilayah}"] = "error"
                                else:
                                    now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
                                    current_datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")
                                    current_loader = str(st.session_state.user_nama)
                                    current_status = "Preloaded"
                                    
                                    # PENTING: Hanya update kolom spesifik (Kolom E, F, G, I) agar Kolom A:D aman tidak tertimpa
                                    ws.update_cell(found_row_index, 5, int(jumlah_box_val))  # Kolom E: Jumlah Box
                                    ws.update_cell(found_row_index, 6, current_loader)         # Kolom F: Loader
                                    ws.update_cell(found_row_index, 7, current_datetime_str)    # Kolom G: Waktu Preload
                                    ws.update_cell(found_row_index, 9, current_status)          # Kolom I: Status
                                    
                                    st.success(f"✅ ID **{target_id}** berhasil diperbarui dengan Jumlah Box: **{jumlah_box_val}**!")
                                    st.session_state[f"sound_effect_{wilayah}"] = "success"
                                    st.rerun()
                            else:
                                st.error(f"❌ ID **{target_id}** tidak ditemukan di database.")
                                st.session_state[f"sound_effect_{wilayah}"] = "error"
                                
                        except Exception as e:
                            st.error(f"❌ Terjadi kesalahan sistem saat memperbarui data: {e}")

            # Menampilkan notifikasi & suara hasil proses
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
