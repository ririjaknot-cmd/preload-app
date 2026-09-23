import streamlit as st
import pandas as pd
import datetime
from datetime import timezone, timedelta
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

# Fungsi untuk membaca data dari sheet "Database log"
@st.cache_data(ttl=5)
def load_data():
    df = conn.read(worksheet="Database log", ttl=0)
    df.columns = df.columns.str.strip()
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

    # --- AMBIL DATA DARI GOOGLE SHEETS ---
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
        st.title(f"Cabang - {wilayah}")

        if not df_database.empty and "Tujuan Pengiriman" in df_database.columns:
            df_filtered = df_database[df_database["Tujuan Pengiriman"] == wilayah].copy()
        else:
            df_filtered = pd.DataFrame()

        if not df_filtered.empty and "Jumlah Box" in df_filtered.columns:
            df_filtered["Jumlah Box"] = df_filtered["Jumlah Box"].fillna(0).astype(int)

        # --- TAB UTAMA ---
        tab_id, tab_preload, tab_ondelivery = st.tabs([
            "ID Request", "Preload", "On Delivery"
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

        # ==========================================
        # TAB PRELOAD
        # ==========================================
        with tab_preload:
            st.subheader(f"Proses Preload & Manifest - {wilayah}")
            
            session_key = f"df_picking_{wilayah}"
            if session_key not in st.session_state or st.session_state.get("current_wilayah") != wilayah:
                df_filtered_cabang = df_filtered.copy()
                
                id_col_candidates = [col for col in df_filtered_cabang.columns if 'id' in col.lower() or 'request' in col.lower()]
                if id_col_candidates:
                    actual_id_col = id_col_candidates[0]
                    df_filtered_cabang.rename(columns={actual_id_col: "ID Request"}, inplace=True)
                else:
                    df_filtered_cabang["ID Request"] = "-"
                
                df_filtered_cabang["ID Request"] = df_filtered_cabang["ID Request"].astype(str).str.split('.').str[0].str.strip()
                
                if "Jumlah Box" not in df_filtered_cabang.columns:
                    df_filtered_cabang["Jumlah Box"] = 1
                else:
                    df_filtered_cabang["Jumlah Box"] = pd.to_numeric(df_filtered_cabang["Jumlah Box"], errors='coerce').fillna(1).astype(int)

                if "Progress" not in df_filtered_cabang.columns:
                    df_filtered_cabang["Progress"] = 0
                else:
                    df_filtered_cabang["Progress"] = pd.to_numeric(df_filtered_cabang["Progress"], errors='coerce').fillna(0).astype(int)
                
                if "Loader" not in df_filtered_cabang.columns:
                    df_filtered_cabang["Loader"] = "-"
                else:
                    df_filtered_cabang["Loader"] = df_filtered_cabang["Loader"].fillna("-").astype(str).replace(["None", "nan", ""], "-")
                
                if "Waktu Preload" not in df_filtered_cabang.columns:
                    df_filtered_cabang["Waktu Preload"] = "-"
                else:
                    df_filtered_cabang["Waktu Preload"] = df_filtered_cabang["Waktu Preload"].fillna("-").astype(str).replace(["None", "nan", ""], "-")
                
                # Deteksi fleksibel kolom Zona Mezzanine dari Google Sheets
                zona_col_candidates = [col for col in df_filtered_cabang.columns if 'zona' in col.lower() or 'mezzanine' in col.lower()]
                if zona_col_candidates:
                    actual_zona_col = zona_col_candidates[0]
                    if actual_zona_col != "Zona Mezzanine":
                        df_filtered_cabang.rename(columns={actual_zona_col: "Zona Mezzanine"}, inplace=True)
                else:
                    df_filtered_cabang["Zona Mezzanine"] = "-"

                df_filtered_cabang["Zona Mezzanine"] = df_filtered_cabang["Zona Mezzanine"].fillna("-").astype(str).replace(["None", "nan", ""], "-")

                def mapping_status_preload(row):
                    prog = row.get("Progress", 0)
                    jml = row.get("Jumlah Box", 1)
                    if prog >= jml and jml > 0:
                        return "🟡 Processed"
                    else:
                        return "🔴 Pending"

                df_filtered_cabang["Status"] = df_filtered_cabang.apply(mapping_status_preload, axis=1)
                
                # SUSUNAN KOLOM SESUAI PERMINTAAN: ID Request - Tujuan Pengiriman - Jumlah Box - Progress - Zona Mezzanine - Loader - Waktu Preload - Status
                kolom_preload_display = ["ID Request", "Tujuan Pengiriman", "Jumlah Box", "Progress", "Zona Mezzanine", "Loader", "Waktu Preload", "Status"]
                kolom_tersedia = [col for col in kolom_preload_display if col in df_filtered_cabang.columns]
                
                st.session_state[session_key] = df_filtered_cabang[kolom_tersedia].copy()
                st.session_state["current_wilayah"] = wilayah
                
            df_pick_current = st.session_state[session_key]

            # --- 1. SCANNER BARCODE CEPAT & OTOMATIS SYNC ---
            input_widget_key = f"input_scan_{wilayah}"
            if input_widget_key not in st.session_state:
                st.session_state[input_widget_key] = ""

            def proses_input_scan():
                scan_input = st.session_state[input_widget_key].strip()
                if not scan_input:
                    return
                
                if not df_pick_current.empty:
                    match_mask = df_pick_current["ID Request"] == scan_input
                    
                    if match_mask.any():
                        wib_zone = timezone(timedelta(hours=7))
                        waktu_sekarang = datetime.datetime.now(wib_zone).strftime("%Y-%m-%d %H:%M:%S")
                        
                        idx = df_pick_current[match_mask].index[0]
                        jml_box = int(df_pick_current.loc[idx, "Jumlah Box"])
                        current_prog = int(df_pick_current.loc[idx, "Progress"])
                        
                        new_prog = current_prog + 1
                        if new_prog > jml_box:
                            new_prog = jml_box
                        
                        new_status = "🟡 Processed" if new_prog >= jml_box else "🔴 Pending"
                        
                        df_pick_current.loc[idx, "Progress"] = new_prog
                        df_pick_current.loc[idx, "Loader"] = st.session_state.user_nama
                        df_pick_current.loc[idx, "Waktu Preload"] = waktu_sekarang
                        df_pick_current.loc[idx, "Status"] = new_status
                        
                        try:
                            global_id_candidates = [col for col in df_database.columns if 'id' in col.lower() or 'request' in col.lower()]
                            if global_id_candidates:
                                global_id_col = global_id_candidates[0]
                                global_mask = df_database[global_id_col].astype(str).str.split('.').str[0].str.strip() == scan_input
                                
                                if "Progress" in df_database.columns:
                                    df_database["Progress"] = pd.to_numeric(df_database["Progress"], errors='coerce').fillna(0).astype(int)
                                    df_database.loc[global_mask, "Progress"] = new_prog
                                if "Loader" in df_database.columns:
                                    df_database["Loader"] = df_database["Loader"].astype(str)
                                    df_database.loc[global_mask, "Loader"] = str(st.session_state.user_nama)
                                if "Waktu Preload" in df_database.columns:
                                    df_database["Waktu Preload"] = df_database["Waktu Preload"].astype(str)
                                    df_database.loc[global_mask, "Waktu Preload"] = str(waktu_sekarang)
                                if "Status" in df_database.columns:
                                    df_database["Status"] = df_database["Status"].astype(str)
                                    df_database.loc[global_mask, "Status"] = "Processed" if new_prog >= jml_box else "Pending"
                                
                                conn.update(worksheet="Database log", data=df_database)
                        except Exception as e:
                            print(f"Error sync sheets: {e}")

                        st.session_state[f"last_msg_{wilayah}"] = ("success", f"✅ **{scan_input}** berhasil disimpan (+1 Box, Progress: {new_prog}/{jml_box})")
                        st.session_state[f"sound_effect_{wilayah}"] = "success"
                    else:
                        st.session_state[f"last_msg_{wilayah}"] = ("error", f"❌ ID **{scan_input}** tidak ditemukan!")
                        st.session_state[f"sound_effect_{wilayah}"] = "error"
                
                st.session_state[input_widget_key] = ""

            st.text_input(
                "📷 Scan / Masukkan ID Request:", 
                placeholder="Arahkan scanner atau ketik ID lalu tekan Enter...", 
                key=input_widget_key,
                on_change=proses_input_scan
            )

            # --- 2. INPUT MANUAL JUMLAH BESAR & OTOMATIS SYNC ---
            with st.expander("📦 Input Manual Jumlah Box Besar (Untuk Puluhan/Ratusan Box)"):
                manual_id_key = f"manual_id_input_{wilayah}"
                clear_flag_key = f"clear_manual_flag_{wilayah}"
                
                if st.session_state.get(clear_flag_key, False):
                    st.session_state[manual_id_key] = ""
                    st.session_state[clear_flag_key] = False

                if manual_id_key not in st.session_state:
                    st.session_state[manual_id_key] = ""

                col_m1, col_m2, col_m3 = st.columns([2, 2, 1])
                with col_m1:
                    manual_id = st.text_input("Ketik ID Request", key=manual_id_key, placeholder="Masukkan ID...")
                with col_m2:
                    manual_qty = st.number_input("Jumlah Box yang Ingin Ditambahkan", min_value=1, value=1, step=1, key=f"manual_qty_{wilayah}")
                with col_m3:
                    st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
                    btn_proses_manual = st.button("Proses", key=f"btn_manual_{wilayah}", use_container_width=True)

                if btn_proses_manual and st.session_state[manual_id_key]:
                    clean_manual_id = st.session_state[manual_id_key].strip()
                    match_mask_m = df_pick_current["ID Request"] == clean_manual_id
                    
                    if match_mask_m.any():
                        wib_zone = timezone(timedelta(hours=7))
                        waktu_sekarang = datetime.datetime.now(wib_zone).strftime("%Y-%m-%d %H:%M:%S")
                        
                        idx_m = df_pick_current[match_mask_m].index[0]
                        jml_box_m = int(df_pick_current.loc[idx_m, "Jumlah Box"])
                        current_prog_m = int(df_pick_current.loc[idx_m, "Progress"])
                        
                        new_prog_m = current_prog_m + int(manual_qty)
                        if new_prog_m > jml_box_m:
                            new_prog_m = jml_box_m
                            st.warning(f"⚠️ Progress dibatasi maksimal sejumlah Jumlah Box ({jml_box_m})!")
                        
                        new_status_m = "🟡 Processed" if new_prog_m >= jml_box_m else "🔴 Pending"
                        
                        df_pick_current.loc[idx_m, "Progress"] = new_prog_m
                        df_pick_current.loc[idx_m, "Loader"] = st.session_state.user_nama
                        df_pick_current.loc[idx_m, "Waktu Preload"] = waktu_sekarang
                        df_pick_current.loc[idx_m, "Status"] = new_status_m
                        
                        try:
                            global_id_candidates = [col for col in df_database.columns if 'id' in col.lower() or 'request' in col.lower()]
                            if global_id_candidates:
                                global_id_col = global_id_candidates[0]
                                global_mask_m = df_database[global_id_col].astype(str).str.split('.').str[0].str.strip() == clean_manual_id
                                
                                if "Progress" in df_database.columns:
                                    df_database["Progress"] = pd.to_numeric(df_database["Progress"], errors='coerce').fillna(0).astype(int)
                                    df_database.loc[global_mask_m, "Progress"] = new_prog_m
                                if "Loader" in df_database.columns:
                                    df_database["Loader"] = df_database["Loader"].astype(str)
                                    df_database.loc[global_mask_m, "Loader"] = str(st.session_state.user_nama)
                                if "Waktu Preload" in df_database.columns:
                                    df_database["Waktu Preload"] = df_database["Waktu Preload"].astype(str)
                                    df_database.loc[global_mask_m, "Waktu Preload"] = str(waktu_sekarang)
                                if "Status" in df_database.columns:
                                    df_database["Status"] = df_database["Status"].astype(str)
                                    df_database.loc[global_mask_m, "Status"] = "Processed" if new_prog_m >= jml_box_m else "Pending"
                                
                                conn.update(worksheet="Database log", data=df_database)
                        except Exception as e:
                            st.error(f"Gagal sync ke Google Sheets: {e}")

                        st.success(f"✅ ID **{clean_manual_id}** berhasil ditambah {manual_qty} box dan tersinkron ke Cloud!")
                        st.session_state[clear_flag_key] = True
                        st.rerun()
                    else:
                        st.error(f"❌ ID Request **{clean_manual_id}** tidak ditemukan di cabang ini!")

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

            st.markdown("##### 📋 Monitoring Data Preload & Scanning Cabang")
            
            if not df_pick_current.empty:
                # Daftar lengkap pilihan Zona Mezzanine sesuai referensi
                list_pilihan_zona = [
                    *[f"A{i}" for i in range(1, 12)],
                    *[f"B{i}" for i in range(1, 10)],
                    *[f"C{i}" for i in range(1, 12)],
                    *[f"D{i}" for i in range(1, 12)],
                    *[f"E{i}" for i in range(1, 10)],
                    *[f"F{i}" for i in range(1, 10)],
                    "SC 1", "SC 2"
                ]

                def parse_zona_list(val):
                    if pd.isna(val) or val == "-" or val == "":
                        return []
                    if isinstance(val, list):
                        return val
                    return [v.strip() for v in str(val).split(",") if v.strip()]

                if "Zona_List" not in df_pick_current.columns:
                    df_pick_current["Zona_List"] = df_pick_current["Zona Mezzanine"].apply(parse_zona_list)

                # Kunci unik berdasarkan wilayah yang sedang dibuka untuk mencegah duplikasi key di Streamlit
                editor_key = f"data_editor_zona_unique_{wilayah}"

                # Fungsi callback untuk auto-sync ke Google Sheets saat ada perubahan zona
                def handle_zona_change():
                    if editor_key in st.session_state:
                        edited_data = st.session_state[editor_key]
                        changes = edited_data.get("edited_rows", {})
                        
                        if changes:
                            current_df = st.session_state[session_key]
                            
                            for row_idx_str, updated_values in changes.items():
                                row_idx = int(row_idx_str)
                                if "Zona_List" in updated_values:
                                    new_zones = updated_values["Zona_List"]
                                    zone_str = ", ".join(new_zones) if new_zones else "-"
                                    
                                    current_df.at[row_idx, "Zona_List"] = new_zones
                                    current_df.at[row_idx, "Zona Mezzanine"] = zone_str
                                    
                                    id_req = current_df.at[row_idx, "ID Request"]
                                    
                                    try:
                                        global_id_candidates = [col for col in df_database.columns if 'id' in col.lower() or 'request' in col.lower()]
                                        if global_id_candidates:
                                            global_id_col = global_id_candidates[0]
                                            global_mask = df_database[global_id_col].astype(str).str.split('.').str[0].str.strip() == str(id_req)
                                            
                                            global_zona_candidates = [col for col in df_database.columns if 'zona' in col.lower() or 'mezzanine' in col.lower()]
                                            zona_col_name = global_zona_candidates[0] if global_zona_candidates else "Zona Mezzanine"
                                            
                                            # HANYA UPDATE KOLOM ZONA SAJA PADA DATABASE GLOBAL
                                            df_database.loc[global_mask, zona_col_name] = zone_str
                                            
                                            # Kirim hanya data spesifik atau pastikan kolom A-E tidak berubah
                                            conn.update(worksheet="Database log", data=df_database)
                                    except Exception as e:
                                        print(f"Gagal auto-sync zona: {e}")

                kolom_tampil_editor = ["ID Request", "Tujuan Pengiriman", "Jumlah Box", "Progress", "Zona_List", "Loader", "Waktu Preload", "Status"]
                df_editor_view = df_pick_current[[col for col in kolom_tampil_editor if col in df_pick_current.columns]].copy()

                edited_df = st.data_editor(
                    df_editor_view,
                    column_config={
                        "ID Request": st.column_config.TextColumn("ID Request", disabled=True),
                        "Tujuan Pengiriman": st.column_config.TextColumn("Tujuan Pengiriman", disabled=True),
                        "Jumlah Box": st.column_config.NumberColumn("Jumlah Box", disabled=True),
                        "Progress": st.column_config.NumberColumn("Progress", disabled=True),
                        "Zona_List": st.column_config.MultiselectColumn(
                            "📍 Zona Mezzanine",
                            help="Pilih satu atau beberapa zona",
                            options=list_pilihan_zona,
                            required=False
                        ),
                        "Loader": st.column_config.TextColumn("Loader", disabled=True),
                        "Waktu Preload": st.column_config.TextColumn("Waktu Preload", disabled=True),
                        "Status": st.column_config.TextColumn("Status", disabled=True)
                    },
                    use_container_width=True,
                    hide_index=True,
                    key=editor_key,
                    on_change=handle_zona_change
                )
            else:
                st.info("Belum ada data logistik untuk ditampilkan pada cabang ini.")

        with tab_ondelivery:
            st.subheader(f"Proses On Delivery - {wilayah}")
            st.write("Centang kotak di bawah untuk menandai status pengiriman:")
            
            df_delivery = pd.DataFrame([
                {"ID Manifest": "MNF-001", "ID Request": "REQ-001", "Jumlah Box": "5/5", "Status": "Ready", "Mark as On Delivery": True},
                {"ID Manifest": "MNF-001", "ID Request": "REQ-002", "Jumlah Box": "12/12", "Status": "Process", "Mark as On Delivery": False}
            ])
            st.dataframe(df_delivery, use_container_width=True, hide_index=True)
