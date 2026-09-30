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

# --- FUNGSI FORMAT STATUS DENGAN IKON WARNA ---
def format_status_dengan_ikon(progress_val, jumlah_box_db):
    """
    Menentukan status dan memberikan ikon/warna:
    - 🔴 Pending: Belum ada progress / kosong / None / 0
    - 🟡 Not Completed: Sudah di-preload tapi progress < jumlah_box_db
    - 🟢 Completed: Sudah di-preload dan progress >= jumlah_box_db
    """
    # Cek apakah progress kosong / None / nan / string kosong
    if progress_val is None:
        return "🔴 Pending"
    
    prog_str = str(progress_val).strip().lower()
    if prog_str in ["", "none", "nan", "nat", "0"]:
        return "🔴 Pending"
    
    try:
        # Konversi ke float dulu untuk mengantisipasi nilai "1.0", lalu ke integer
        prog_int = int(float(progress_val))
        max_box = int(float(jumlah_box_db))
    except (ValueError, TypeError):
        return "🔴 Pending"
        
    # Jika progress sudah ada nilainya (angka valid > 0)
    if prog_int <= 0:
        return "🔴 Pending"
    elif prog_int < max_box:
        return "🟡 Not Completed"
    else:
        return "🟢 Completed"

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
        tab_id, tab_preload, tab_manifest = st.tabs([
            "ID Request", "Preload", "Manifest"
        ])

        with tab_id:
            st.subheader(f"Data Logistik & Pencarian ID - {wilayah}")
            keyword_cari = st.text_input("🔍 Cari ID Request:", placeholder="Ketik ID Request yang ingin dicari...", key="search_id_request")
            
            df_display = df_filtered.copy()
            
            # Terapkan format status dengan ikon warna secara dinamis pada tabel ID Request
            if not df_display.empty:
                status_formatted_list = []
                for idx, row in df_display.iterrows():
                    try:
                        jb = row.get("Jumlah Box") or 0
                        pr = row.get("Progress")
                        st_formatted = format_status_dengan_ikon(pr, jb)
                        status_formatted_list.append(st_formatted)
                    except Exception:
                        status_formatted_list.append("🔴 Pending")
                
                df_display["Status"] = status_formatted_list

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
            st.markdown("Gunakan **Scan Satuan** (langsung enter/scan) atau **Input ID & Jumlah Box** untuk memperbarui data ke Kolom Progress Google Sheets.")

            # Pilihan Metode Input
            metode_input = st.radio("Pilih Metode Input:", ["Scan Satuan", "Input ID & Jumlah Box"], horizontal=True)

            if metode_input == "Scan Satuan":
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
                        row_tujuan = ""
                        max_box_db = 0
                        current_progress_val = None

                        for idx, row in enumerate(data_rows):
                            row_id = str(row.get("ID") or row.get("id request") or list(row.values())[0]).split('.')[0].strip()
                            if row_id == scan_input:
                                found_row_index = idx + 2
                                row_tujuan = str(row.get("Tujuan Pengiriman") or list(row.values())[1]).strip()
                                try:
                                    max_box_db = int(float(str(row.get("Jumlah Box") or list(row.values())[4]).strip()))
                                except ValueError:
                                    max_box_db = 0
                                
                                current_progress_val = row.get("Progress")
                                break
                        
                        if not found_row_index:
                            st.session_state[f"last_msg_{wilayah}"] = ("error", f"❌ ID **{scan_input}** tidak terdaftar di database.")
                            st.session_state[f"sound_effect_{wilayah}"] = "error"
                        elif row_tujuan.lower() != wilayah.lower():
                            st.session_state[f"last_msg_{wilayah}"] = ("error", f"❌ ID **{scan_input}** ditolak! Tujuan pengiriman ({row_tujuan}) tidak sesuai dengan wilayah aktif ({wilayah}).")
                            st.session_state[f"sound_effect_{wilayah}"] = "error"
                        else:
                            # ATURAN SCAN SATUAN: Selalu bernilai 1 per scan
                            scan_jumlah_box = 1

                            # Ambil nilai progress saat ini untuk divalidasi/ditambahkan
                            try:
                                prog_int = int(float(current_progress_val)) if current_progress_val not in [None, "", "None", "nan"] else 0
                            except (ValueError, TypeError):
                                prog_int = 0

                            # Validasi apakah jumlah progress sudah mencapai batas maksimum database
                            if prog_int >= max_box_db:
                                st.session_state[f"last_msg_{wilayah}"] = ("error", f"⚠️ ID **{scan_input}** sudah mencapai batas maksimal Jumlah Box ({max_box_db}) di database.")
                                st.session_state[f"sound_effect_{wilayah}"] = "error"
                            else:
                                # Akumulasi progress (tambah 1 setiap kali scan satuan)
                                progress_baru = prog_int + scan_jumlah_box
                                
                                # Tentukan Status otomatis berdasarkan progress baru vs max_box_db
                                if progress_baru < max_box_db:
                                    current_status = "Not Completed"
                                else:
                                    current_status = "Completed"

                                now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
                                current_datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")
                                current_loader = str(st.session_state.user_nama)
                                
                                # Update ke Google Sheets
                                ws.update_cell(found_row_index, 6, progress_baru)       # Kolom F: Progress (Akumulasi +1)
                                ws.update_cell(found_row_index, 7, current_loader)        # Kolom G: Loader
                                ws.update_cell(found_row_index, 8, current_datetime_str)   # Kolom H: Waktu Preload
                                ws.update_cell(found_row_index, 10, current_status)       # Kolom J: Status
                                
                                st.session_state[f"last_msg_{wilayah}"] = ("success", f"✅ ID **{scan_input}** berhasil di-scan satuan (+1 Box). Total Progress: **{progress_baru}/{max_box_db}**!")
                                st.session_state[f"sound_effect_{wilayah}"] = "success"
                                
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
                form_single_key = f"form_single_box_preload_{wilayah}"
                with st.form(key=form_single_key, clear_on_submit=True):
                    input_id_val = st.text_input("Masukkan ID", placeholder="Ketik atau scan 1 ID di sini...")
                    jumlah_box_val = st.number_input("Jumlah Box (Progress)", min_value=1, value=1, step=1)
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
                            row_tujuan = ""
                            max_box_db = 0
                            current_progress_val = None

                            for idx, row in enumerate(data_rows):
                                row_id = str(row.get("ID") or row.get("id request") or list(row.values())[0]).split('.')[0].strip()
                                if row_id == target_id:
                                    found_row_index = idx + 2
                                    row_tujuan = str(row.get("Tujuan Pengiriman") or list(row.values())[1]).strip()
                                    try:
                                        max_box_db = int(float(str(row.get("Jumlah Box") or list(row.values())[4]).strip()))
                                    except ValueError:
                                        max_box_db = 0
                                    current_progress_val = row.get("Progress")
                                    break
                            
                            # Validasi 1: Apakah ID terdaftar?
                            if not found_row_index:
                                st.error(f"❌ ID **{target_id}** tidak terdaftar di database.")
                                st.session_state[f"sound_effect_{wilayah}"] = "error"
                            
                            # Validasi 2: Apakah tujuan pengiriman sesuai wilayah aktif?
                            elif row_tujuan.lower() != wilayah.lower():
                                st.error(f"❌ ID **{target_id}** ditolak! Tujuan pengiriman ({row_tujuan}) tidak sesuai dengan wilayah aktif ({wilayah}).")
                                st.session_state[f"sound_effect_{wilayah}"] = "error"
                            
                            else:
                                # Konversi progress saat ini ke integer (jika kosong/None dianggap 0)
                                try:
                                    prog_lama = int(float(current_progress_val)) if current_progress_val not in [None, "", "None", "nan"] else 0
                                except (ValueError, TypeError):
                                    prog_lama = 0

                                # Validasi 3: Cek apakah ID sudah Completed (progress lama sudah mencapai / melewati max_box_db)
                                if prog_lama >= max_box_db and max_box_db > 0:
                                    st.error(f"⚠️ ID **{target_id}** sudah berstatus **Completed** (Progress: {prog_lama}/{max_box_db}). Input ditolak karena sudah selesai.")
                                    st.session_state[f"sound_effect_{wilayah}"] = "error"
                                
                                # Validasi 4: Cek apakah total progress (lama + input baru) melebihi batas database
                                elif (prog_lama + int(jumlah_box_val)) > max_box_db:
                                    sisa_box = max_box_db - prog_lama
                                    st.error(f"❌ Jumlah box yang dimasukkan (**{jumlah_box_val}**) melebihi sisa kuota. Progress saat ini: {prog_lama}/{max_box_db} (Sisa kuota: {sisa_box} box).")
                                    st.session_state[f"sound_effect_{wilayah}"] = "error"
                                
                                else:
                                    # Hitung akumulasi progress baru
                                    progress_baru = prog_lama + int(jumlah_box_val)
                                    
                                    # Tentukan status otomatis
                                    if progress_baru < max_box_db:
                                        current_status = "Not Completed"
                                    else:
                                        current_status = "Completed"

                                    now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
                                    current_datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")
                                    current_loader = str(st.session_state.user_nama)
                                    
                                    # Update ke Google Sheets
                                    ws.update_cell(found_row_index, 6, progress_baru)       # Kolom F: Progress (Akumulasi)
                                    ws.update_cell(found_row_index, 7, current_loader)        # Kolom G: Loader
                                    ws.update_cell(found_row_index, 8, current_datetime_str)   # Kolom H: Waktu Preload
                                    ws.update_cell(found_row_index, 10, current_status)       # Kolom J: Status
                                    
                                    st.success(f"✅ ID **{target_id}** berhasil diperbarui! Progress baru: **{progress_baru}/{max_box_db}** (Status: {current_status})")
                                    st.session_state[f"sound_effect_{wilayah}"] = "success"
                                    st.rerun()
                                    
                        except Exception as e:
                            st.error(f"❌ Terjadi kesalahan sistem: {e}")
                            st.session_state[f"sound_effect_{wilayah}"] = "error"

            # Notifikasi & suara
            if f"last_msg_{wilayah}" in st.session_state:
                m_type, m_text = st.session_state[f"last_msg_{wilayah}"]
                if m_type == "success":
                    st.success(m_text)
                else:
                    st.error(m_text)
                del st.session_state[f"last_msg_{wilayah}"]

            if f"sound_effect_{wilayah}" in st.session_state:
                sound_type = st.session_state[f"sound_effect_{wilayah}"]
                audio_html = f'<audio autoplay><source src="https://assets.mixkit.co/active_storage/sfx/{"2869" if sound_type=="success" else "2957"}/{"2869" if sound_type=="success" else "2957"}-preview.mp3" type="audio/mpeg"></audio>'
                st.markdown(audio_html, unsafe_allow_html=True)
                del st.session_state[f"sound_effect_{wilayah}"]

            st.markdown("---")

            # ==========================================
            # MENU UPDATE ZONA MEZZANINE (COLLAPSED / EXPANDER)
            # ==========================================
            with st.expander("🏗️ Menu Update Zona Mezzanine (Klik untuk Buka/Tutup)", expanded=False):
                st.markdown(f"Pilih **beberapa ID Request** sekaligus dan tentukan **Zona Mezzanine**-nya untuk memperbarui data secara bersamaan.")
                
                daftar_zona_mezzanine = [
                    "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "A11",
                    "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9",
                    "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C11",
                    "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11",
                    "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9",
                    "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9",
                    "SC 1", "SC 2"
                ]

                if not df_filtered.empty:
                    list_id_tersedia = []
                    for idx, row in df_filtered.iterrows():
                        r_id = str(row.get("ID") or row.get("id request") or "").split('.')[0].strip()
                        if r_id and r_id not in list_id_tersedia:
                            list_id_tersedia.append(r_id)

                    with st.form(key=f"form_update_mezzanine_multi_{wilayah}", clear_on_submit=True):
                        selected_ids_mz = st.multiselect(
                            "Pilih ID Request (Bisa pilih lebih dari satu):",
                            options=list_id_tersedia,
                            placeholder="Cari atau pilih beberapa ID..."
                        )
                        
                        selected_zones = st.multiselect(
                            "Pilih Zona Mezzanine (Bisa pilih lebih dari satu):",
                            options=daftar_zona_mezzanine,
                            placeholder="Ketik atau pilih zona (contoh: A1, B2)..."
                        )
                        
                        submit_mz = st.form_submit_button("💾 Simpan Zona Mezzanine untuk Semua ID Terpilih", type="primary")

                    if submit_mz:
                        if not selected_ids_mz:
                            st.warning("⚠️ Pilih minimal satu ID Request terlebih dahulu.")
                        elif not selected_zones:
                            st.warning("⚠️ Pilih minimal satu Zona Mezzanine.")
                        else:
                            try:
                                creds_dict = dict(st.secrets["connections"]["gsheets"])
                                gc = gspread.service_account_from_dict(creds_dict)
                                spreadsheet_name = st.secrets["connections"]["gsheets"].get("spreadsheet")
                                sh = gc.open_by_url(spreadsheet_name) if spreadsheet_name.startswith("http") else gc.open(spreadsheet_name)
                                ws = sh.worksheet("Database log")
                                
                                data_rows = ws.get_all_records()
                                string_zona_hasil = ", ".join(selected_zones)
                                
                                berhasilan_count = 0
                                for target_id in selected_ids_mz:
                                    found_row_index = None
                                    for idx, row in enumerate(data_rows):
                                        row_id = str(row.get("ID") or row.get("id request") or list(row.values())[0]).split('.')[0].strip()
                                        if row_id == str(target_id).strip():
                                            found_row_index = idx + 2
                                            break
                                    
                                    if found_row_index:
                                        ws.update_cell(found_row_index, 9, string_zona_hasil)
                                        berhasilan_count += 1
                                
                                if berhasilan_count > 0:
                                    st.success(f"✅ Berhasil memperbarui Zona Mezzanine (**{string_zona_hasil}**) untuk **{berhasilan_count} ID Request** sekaligus!")
                                    st.session_state[f"sound_effect_{wilayah}"] = "success"
                                    st.rerun()
                                else:
                                    st.error("❌ ID yang dipilih tidak ditemukan di database Google Sheets.")
                                    
                            except Exception as e:
                                st.error(f"❌ Gagal memperbarui zona ke Google Sheets: {e}")
                else:
                    st.info("Belum ada data ID untuk wilayah ini.")

            st.markdown("---")
            st.markdown(f"##### 📋 Data Riwayat Preload Cabang: {wilayah}")
            
            if not df_filtered.empty:
                df_preload_display = df_filtered.copy()
                
                # Format Kolom Status dengan Ikon Warna secara dinamis berdasarkan Progress & Jumlah Box
                status_formatted_list = []
                for idx, row in df_preload_display.iterrows():
                    try:
                        jb = row.get("Jumlah Box") or 0
                        pr = row.get("Progress")
                        st_formatted = format_status_dengan_ikon(pr, jb)
                        status_formatted_list.append(st_formatted)
                    except Exception:
                        status_formatted_list.append("🔴 Pending")
                
                df_preload_display["Status"] = status_formatted_list

                kolom_dihapus = ["Jam Proses Scan", "Tanggal Proses Scan"]
                for col in kolom_dihapus:
                    if col in df_preload_display.columns:
                        df_preload_display = df_preload_display.drop(columns=[col])
                
                # Mengatur posisi kolom "Zona Mezzanine" agar berada tepat di sebelah "Waktu Preload" pada tabel
                if "Zona Mezzanine" in df_preload_display.columns and "Waktu Preload" in df_preload_display.columns:
                    cols = list(df_preload_display.columns)
                    cols.remove("Zona Mezzanine")
                    idx_waktu = cols.index("Waktu Preload")
                    cols.insert(idx_waktu + 1, "Zona Mezzanine")
                    df_preload_display = df_preload_display[cols]
                
                st.dataframe(df_preload_display, use_container_width=True, hide_index=True)
            else:
                st.info("Belum ada data logistik untuk ditampilkan pada cabang ini.")

        with tab_manifest:
            st.subheader(f"📦 Manajemen Manifest Pengiriman - {wilayah}")
            st.markdown("Kelola surat jalan / manifest pengiriman berdasarkan Zona Mezzanine.")

            # Kumpulkan semua ID yang sudah pernah masuk ke manifest manapun untuk cabang ini
            all_manifested_ids = set()
            df_manifest_all_cache = pd.DataFrame()
            try:
                df_manifest_all_cache = conn.read(worksheet="Manifest log", ttl=0)
                if df_manifest_all_cache is not None and not df_manifest_all_cache.empty:
                    df_manifest_all_cache.columns = [str(c).strip() for c in df_manifest_all_cache.columns]
                    if "Tujuan Pengiriman" in df_manifest_all_cache.columns:
                        df_wilayah_mnf = df_manifest_all_cache[
                            df_manifest_all_cache["Tujuan Pengiriman"].astype(str).str.strip().str.lower() == wilayah.strip().lower()
                        ]
                        for id_str_val in df_wilayah_mnf["ID List"].dropna():
                            for single_id in str(id_str_val).split(","):
                                cl_id = single_id.strip()
                                if cl_id:
                                    all_manifested_ids.add(cl_id)
            except Exception:
                pass

            # Tombol untuk memunculkan form Buat Manifest Baru Berdasarkan Zona Mezzanine
            with st.expander("➕ Buat Manifest Berdasarkan Zona Mezzanine", expanded=False):
                with st.form(key=f"form_buat_manifest_zona_{wilayah}", clear_on_submit=True):
                    st.markdown("Pilih satu atau beberapa **Zona Mezzanine** yang ingin dimanifestkan.")
                    
                    list_zona_tersedia = []
                    if not df_filtered.empty and "Zona Mezzanine" in df_filtered.columns:
                        for z_val in df_filtered["Zona Mezzanine"].dropna():
                            z_str = str(z_val).strip()
                            if z_str and z_str.lower() not in ["none", "", "nan"]:
                                for sub_z in z_str.split(","):
                                    clean_z = sub_z.strip()
                                    if clean_z and clean_z not in list_zona_tersedia:
                                        list_zona_tersedia.append(clean_z)
                    
                    list_zona_tersedia.sort()

                    selected_zones_manifest = st.multiselect(
                        "Pilih Zona Mezzanine:",
                        options=list_zona_tersedia,
                        placeholder="Pilih zona (contoh: A1, B2)..."
                    )
                    
                    submit_manifest = st.form_submit_button("🚀 Generate Manifest dari Zona", type="primary")

                if submit_manifest:
                    if not selected_zones_manifest:
                        st.warning("⚠️ Pilih minimal satu Zona Mezzanine terlebih dahulu.")
                    else:
                        try:
                            matched_ids = []
                            total_box_manifest = 0

                            for idx, row in df_filtered.iterrows():
                                row_zona = str(row.get("Zona Mezzanine", "")).strip()
                                if any(z.lower() in row_zona.lower() for z in selected_zones_manifest):
                                    r_id = str(row.get("ID") or row.get("id request") or "").split('.')[0].strip()
                                    
                                    if r_id and r_id not in all_manifested_ids and r_id not in matched_ids:
                                        matched_ids.append(r_id)
                                        try:
                                            b_val = row.get("Jumlah Box", 1)
                                            max_box = int(float(b_val)) if b_val not in [None, "", "None", "nan"] else 1
                                            total_box_manifest += max_box
                                        except (ValueError, TypeError):
                                            total_box_manifest += 1

                            if not matched_ids:
                                st.warning("⚠️ Tidak ada ID Request baru yang ditemukan pada zona mezzanine yang dipilih.")
                            else:
                                now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
                                nomor_manifest = f"MNF-{now.strftime('%Y%m%d-%H%M%S')}"
                                
                                creds_dict = dict(st.secrets["connections"]["gsheets"])
                                gc = gspread.service_account_from_dict(creds_dict)
                                spreadsheet_name = st.secrets["connections"]["gsheets"].get("spreadsheet")
                                sh = gc.open_by_url(spreadsheet_name) if spreadsheet_name.startswith("http") else gc.open(spreadsheet_name)
                                
                                try:
                                    ws_manifest = sh.worksheet("Manifest log")
                                except gspread.exceptions.WorksheetNotFound:
                                    ws_manifest = sh.add_worksheet(title="Manifest log", rows=100, cols=10)
                                    ws_manifest.append_row(["Nomor Manifest", "Tujuan Pengiriman", "Zona Mezzanine", "ID List", "Jumlah Box", "Dibuat Oleh", "Waktu Buat", "Status Manifest"])

                                dibuat_oleh = str(st.session_state.user_nama)
                                waktu_buat = now.strftime("%Y-%m-%d %H:%M:%S")
                                status_manifest = "Manifested"
                                zona_str = ", ".join(selected_zones_manifest)

                                ws_manifest.append_row([
                                    nomor_manifest,
                                    wilayah,
                                    zona_str,
                                    ", ".join(matched_ids),
                                    total_box_manifest,
                                    dibuat_oleh,
                                    waktu_buat,
                                    status_manifest
                                ])

                                # Update progress di sheet database log / preload
                                try:
                                    ws_main = sh.worksheet("Database log")
                                    records_main = ws_main.get_all_records()
                                    header_main = ws_main.row_values(1)
                                    
                                    id_col_i = header_main.index("ID") + 1 if "ID" in header_main else (header_main.index("id request") + 1 if "id request" in header_main else None)
                                    prog_col_i = header_main.index("Progress") + 1 if "Progress" in header_main else None
                                    box_col_i = header_main.index("Jumlah Box") + 1 if "Jumlah Box" in header_main else None
                                    
                                    if id_col_i and prog_col_i:
                                        for r_i, r_val in enumerate(records_main, start=2):
                                            curr_row_id = str(r_val.get("ID") or r_val.get("id request") or "").split('.')[0].strip()
                                            if curr_row_id in matched_ids:
                                                max_b = int(float(r_val.get("Jumlah Box", 1))) if r_val.get("Jumlah Box") not in [None, "", "nan"] else 1
                                                ws_main.update_cell(r_i, prog_col_i, max_b)
                                except Exception:
                                    pass

                                st.success(f"✅ Berhasil membuat Manifest **{nomor_manifest}** dari Zona **{zona_str}** (Total ID: {len(matched_ids)})!")
                                st.session_state[f"sound_effect_{wilayah}"] = "success"
                                st.rerun()

                        except Exception as e:
                            st.error(f"❌ Gagal membuat manifest: {e}")

            st.markdown("---")
            st.markdown(f"##### 📋 Daftar Manifest Cabang: {wilayah}")

            df_manifest_wilayah = pd.DataFrame()
            try:
                df_manifest_all = conn.read(worksheet="Manifest log", ttl=0)
                if df_manifest_all is not None and not df_manifest_all.empty:
                    df_manifest_all.columns = [str(c).strip() for c in df_manifest_all.columns]
                    if "Tujuan Pengiriman" in df_manifest_all.columns:
                        df_manifest_wilayah = df_manifest_all[
                            df_manifest_all["Tujuan Pengiriman"].astype(str).str.strip().str.lower() == wilayah.strip().lower()
                        ].copy()
            except Exception as e:
                st.warning(f"⚠️ Gagal memuat data manifest: {e}")

            if not df_manifest_wilayah.empty:
                for index, row_mnf in df_manifest_wilayah.iterrows():
                    m_no = str(row_mnf.get("Nomor Manifest", ""))
                    m_zona = str(row_mnf.get("Zona Mezzanine", ""))
                    m_tbox = str(row_mnf.get("Jumlah Box", "0"))
                    m_oleh = str(row_mnf.get("Dibuat Oleh", ""))
                    m_waktu = str(row_mnf.get("Waktu Buat", ""))
                    m_status = str(row_mnf.get("Status Manifest", "Manifested"))

                    c_info, c_btn = st.columns([5, 1])
                    with c_info:
                        st.markdown(
                            f"**No. Manifest:** `{m_no}` | **Zona:** {m_zona} | **Jumlah Box:** `{m_tbox}` | "
                            f"**Status:** `{m_status}` | **Oleh:** {m_oleh} ({m_waktu})"
                        )
                    with c_btn:
                        btn_key = f"detail_mnf_{wilayah}_{m_no}_{index}"
                        if st.button("🔍 Detail", key=btn_key, use_container_width=True):
                            st.session_state[f"active_detail_manifest_{wilayah}"] = m_no

                    st.markdown("---")

                # Detail Manifest Aktif (Hanya muncul jika tombol detail diklik)
                active_mnf = st.session_state.get(f"active_detail_manifest_{wilayah}")
                if active_mnf:
                    selected_row_data = df_manifest_wilayah[df_manifest_wilayah["Nomor Manifest"].astype(str) == str(active_mnf)]
                    
                    if not selected_row_data.empty:
                        st.markdown("---")
                        st.markdown(f"### 🔍 Detail Manifest: `{active_mnf}`")
                        
                        row_info = selected_row_data.iloc[0]
                        current_id_list_str = str(row_info.get("ID List", ""))
                        ids_in_manifest = [i.strip() for i in current_id_list_str.split(",") if i.strip()]
                        
                        st.info(f"**Zona Terliput:** {row_info.get('Zona Mezzanine')} | **Jumlah Box:** {row_info.get('Jumlah Box')} | **Waktu Buat:** {row_info.get('Waktu Buat')}")
                        
                        # --- FORM SCAN ID SUSULAN (MASUK) & SCAN ID KELUAR ---
                        col_scan_in, col_scan_out = st.columns(2)
                        
                        with col_scan_in:
                            with st.form(key=f"form_scan_susulan_{active_mnf}", clear_on_submit=True):
                                st.markdown("##### ➕ Scan ID Masuk / Susulan")
                                scan_input_id = st.text_input("Scan/Ketik ID Request Baru:", placeholder="Tempel/Scan ID...")
                                btn_submit_susulan = st.form_submit_button("Tambah ke Manifest")
                                
                                if btn_submit_susulan:
                                    clean_new_id = scan_input_id.strip().split('.')[0]
                                    if not clean_new_id:
                                        st.warning("⚠️ Masukkan ID yang valid.")
                                    elif clean_new_id in all_manifested_ids:
                                        st.error(f"❌ ID `{clean_new_id}` sudah terdaftar di manifest lain!")
                                    elif clean_new_id in ids_in_manifest:
                                        st.warning(f"⚠️ ID `{clean_new_id}` sudah ada di manifest ini.")
                                    else:
                                        try:
                                            creds_dict = dict(st.secrets["connections"]["gsheets"])
                                            gc = gspread.service_account_from_dict(creds_dict)
                                            spreadsheet_name = st.secrets["connections"]["gsheets"].get("spreadsheet")
                                            sh = gc.open_by_url(spreadsheet_name) if spreadsheet_name.startswith("http") else gc.open(spreadsheet_name)
                                            
                                            # Cek database log / preload untuk ambil jumlah box dan update progress
                                            ws_main = sh.worksheet("Database log")
                                            records_main = ws_main.get_all_records()
                                            header_main = ws_main.row_values(1)
                                            
                                            id_col_i = header_main.index("ID") + 1 if "ID" in header_main else (header_main.index("id request") + 1 if "id request" in header_main else None)
                                            prog_col_i = header_main.index("Progress") + 1 if "Progress" in header_main else None
                                            
                                            added_box = 1
                                            if id_col_i:
                                                for r_idx, r_val in enumerate(records_main, start=2):
                                                    r_id_str = str(r_val.get("ID") or r_val.get("id request") or "").split('.')[0].strip()
                                                    if r_id_str == clean_new_id:
                                                        max_box_val = int(float(r_val.get("Jumlah Box", 1))) if r_val.get("Jumlah Box") not in [None, "", "nan"] else 1
                                                        added_box = max_box_val
                                                        if prog_col_i:
                                                            ws_main.update_cell(r_idx, prog_col_i, max_box_val)
                                                        break

                                            # Update Manifest log
                                            ws_m = sh.worksheet("Manifest log")
                                            header_m = ws_m.row_values(1)
                                            
                                            mnf_col_idx = header_m.index("Nomor Manifest") + 1 if "Nomor Manifest" in header_m else 1
                                            idlist_idx = header_m.index("ID List") + 1 if "ID List" in header_m else 4
                                            tbox_idx = header_m.index("Jumlah Box") + 1 if "Jumlah Box" in header_m else 5
                                            
                                            manifest_col_values = ws_m.col_values(mnf_col_idx)
                                            row_idx = None
                                            for idx_m, val_m in enumerate(manifest_col_values, start=1):
                                                if str(val_m).strip() == str(active_mnf):
                                                    row_idx = idx_m
                                                    break
                                            
                                            if row_idx:
                                                row_values = ws_m.row_values(row_idx)
                                                ids_in_manifest.append(clean_new_id)
                                                new_id_list_str = ", ".join(ids_in_manifest)
                                                
                                                try:
                                                    current_total_box = int(float(row_values[tbox_idx - 1])) if len(row_values) >= tbox_idx and row_values[tbox_idx - 1] != '' else 0
                                                except:
                                                    current_total_box = 0
                                                new_total_box = current_total_box + added_box
                                                
                                                ws_m.update_cell(row_idx, idlist_idx, new_id_list_str)
                                                ws_m.update_cell(row_idx, tbox_idx, new_total_box)
                                                
                                                st.success(f"✅ Berhasil menambahkan ID `{clean_new_id}` (Box: {added_box}) ke manifest!")
                                                st.rerun()
                                            else:
                                                st.error("❌ Baris manifest tidak ditemukan di Google Sheets.")
                                        except Exception as e:
                                            st.error(f"❌ Gagal menambahkan ID susulan: {e}")

                        with col_scan_out:
                            with st.form(key=f"form_scan_keluar_{active_mnf}", clear_on_submit=True):
                                st.markdown("##### ➖ Scan ID Keluar (Keluarkan dari Manifest)")
                                scan_out_id = st.text_input("Scan/Ketik ID yang akan dikeluarkan:", placeholder="ID yang ingin dihapus...")
                                btn_submit_keluar = st.form_submit_button("Keluarkan dari Manifest", type="secondary")
                                
                                if btn_submit_keluar:
                                    clean_out_id = scan_out_id.strip().split('.')[0]
                                    if clean_out_id not in ids_in_manifest:
                                        st.error(f"❌ ID `{clean_out_id}` tidak ditemukan dalam manifest ini!")
                                    else:
                                        try:
                                            creds_dict = dict(st.secrets["connections"]["gsheets"])
                                            gc = gspread.service_account_from_dict(creds_dict)
                                            spreadsheet_name = st.secrets["connections"]["gsheets"].get("spreadsheet")
                                            sh = gc.open_by_url(spreadsheet_name) if spreadsheet_name.startswith("http") else gc.open(spreadsheet_name)
                                            
                                            # Ambil jumlah box ID tersebut dan kembalikan progress di Database log menjadi 0 (atau dikurangi)
                                            ws_main = sh.worksheet("Database log")
                                            records_main = ws_main.get_all_records()
                                            header_main = ws_main.row_values(1)
                                            
                                            id_col_i = header_main.index("ID") + 1 if "ID" in header_main else (header_main.index("id request") + 1 if "id request" in header_main else None)
                                            prog_col_i = header_main.index("Progress") + 1 if "Progress" in header_main else None
                                            
                                            removed_box = 1
                                            if id_col_i:
                                                for r_idx, r_val in enumerate(records_main, start=2):
                                                    r_id_str = str(r_val.get("ID") or r_val.get("id request") or "").split('.')[0].strip()
                                                    if r_id_str == clean_out_id:
                                                        removed_box = int(float(r_val.get("Jumlah Box", 1))) if r_val.get("Jumlah Box") not in [None, "", "nan"] else 1
                                                        # Reset progress di database log menjadi 0 atau dikurangi
                                                        if prog_col_i:
                                                            ws_main.update_cell(r_idx, prog_col_i, 0)
                                                        break

                                            # Update Manifest log
                                            ws_m = sh.worksheet("Manifest log")
                                            header_m = ws_m.row_values(1)
                                            
                                            mnf_col_idx = header_m.index("Nomor Manifest") + 1 if "Nomor Manifest" in header_m else 1
                                            idlist_idx = header_m.index("ID List") + 1 if "ID List" in header_m else 4
                                            tbox_idx = header_m.index("Jumlah Box") + 1 if "Jumlah Box" in header_m else 5
                                            
                                            manifest_col_values = ws_m.col_values(mnf_col_idx)
                                            row_idx = None
                                            for idx_m, val_m in enumerate(manifest_col_values, start=1):
                                                if str(val_m).strip() == str(active_mnf):
                                                    row_idx = idx_m
                                                    break
                                            
                                            if row_idx:
                                                row_values = ws_m.row_values(row_idx)
                                                ids_in_manifest.remove(clean_out_id)
                                                new_id_list_str = ", ".join(ids_in_manifest)
                                                
                                                try:
                                                    current_total_box = int(float(row_values[tbox_idx - 1])) if len(row_values) >= tbox_idx and row_values[tbox_idx - 1] != '' else 0
                                                except:
                                                    current_total_box = 0
                                                new_total_box = max(0, current_total_box - removed_box)
                                                
                                                ws_m.update_cell(row_idx, idlist_idx, new_id_list_str)
                                                ws_m.update_cell(row_idx, tbox_idx, new_total_box)
                                                
                                                st.success(f"✅ Berhasil mengeluarkan ID `{clean_out_id}` dari manifest!")
                                                st.rerun()
                                            else:
                                                st.error("❌ Baris manifest tidak ditemukan di Google Sheets.")
                                        except Exception as e:
                                            st.error(f"❌ Gagal mengeluarkan ID: {e}")

                        st.markdown("---")
                        
                        # Tampilkan rincian item dalam manifest
                        if not df_filtered.empty:
                            col_id_name = "ID" if "ID" in df_filtered.columns else ("id request" if "id request" in df_filtered.columns else None)
                            if col_id_name:
                                df_filtered["clean_id"] = df_filtered[col_id_name].astype(str).str.split('.').str[0].str.strip()
                                df_detail_manifest = df_filtered[df_filtered["clean_id"].isin(ids_in_manifest)].copy()
                                
                                if not df_detail_manifest.empty:
                                    st.markdown("##### Rincian Item / ID Request dalam Manifest Ini:")
                                    if "clean_id" in df_detail_manifest.columns:
                                        df_detail_manifest = df_detail_manifest.drop(columns=["clean_id"])
                                    st.dataframe(df_detail_manifest, use_container_width=True, hide_index=True)
                                else:
                                    st.info("ℹ️ ID yang terdaftar dalam manifest ini:")
                                    st.write(ids_in_manifest)
                        
                        if st.button("❌ Tutup Detail", key=f"close_detail_{wilayah}_{active_mnf}"):
                            st.session_state[f"active_detail_manifest_{wilayah}"] = None
                            st.rerun()
            else:
                st.info(f"Belum ada data Manifest yang dibuat untuk cabang {wilayah}.")
