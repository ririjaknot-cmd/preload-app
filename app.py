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

# --- FUNGSI AMAN UNTUK UPDATE HANYA KOLOM OPERASIONAL (F KE KANAN) ---
def safe_conn_update(df_global_master, df_local_updated, id_request_target):
    """
    Fungsi ini memastikan hanya kolom operasional (seperti Progress, Zona Mezzanine, dll)
    yang diperbarui ke Google Sheets, tanpa menyentuh kolom A sampai E (data murni).
    """
    try:
        # Cari kolom ID di database master
        id_col_candidates = [col for col in df_global_master.columns if 'id' in col.lower() or 'request' in col.lower()]
        if not id_col_candidates:
            return
        
        global_id_col = id_col_candidates[0]
        
        # Cari baris yang sesuai dengan ID Request yang diubah
        mask_master = df_global_master[global_id_col].astype(str).str.split('.').str[0].str.strip() == str(id_request_target).strip()
        mask_local = df_local_updated["ID Request"].astype(str).str.split('.').str.0.str.strip() == str(id_request_target).strip()
        
        if mask_master.any() and mask_local.any():
            local_idx = df_local_updated[mask_local].index[0]
            
            # Daftar kolom operasional yang diizinkan untuk di-update (Mulai dari kolom F ke kanan)
            kolom_operasional = ["Progress", "Zona Mezzanine", "Loader", "Waktu Preload", "Status"]
            
            for col in kolom_operasional:
                if col in df_local_updated.columns and col in df_global_master.columns:
                    val_to_update = df_local_updated.loc[local_idx, col]
                    df_global_master.loc[mask_master, col] = val_to_update
            
            # Kirim pembaruan ke Google Sheets
            conn.update(worksheet="Database log", data=df_global_master)
    except Exception as e:
        print(f"Error safe_conn_update: {e}")

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
                        
                        # Sinkronisasi aman (hanya update kolom operasional F ke kanan)
                        safe_conn_update(df_database, df_pick_current, scan_input)

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
                        
                        # Sinkronisasi aman (hanya update kolom operasional F ke kanan)
                        safe_conn_update(df_database, df_pick_current, clean_manual_id)

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
                list_pilihan_zona = [
                    "-",
                    *[f"A{i}" for i in range(1, 12)],
                    *[f"B{i}" for i in range(1, 10)],
                    *[f"C{i}" for i in range(1, 12)],
                    *[f"D{i}" for i in range(1, 12)],
                    *[f"E{i}" for i in range(1, 10)],
                    *[f"F{i}" for i in range(1, 10)],
                    "SC 1", "SC 2"
                ]

                editor_key = f"data_editor_zona_unique_{wilayah}"

                def handle_zona_change():
                    if editor_key in st.session_state:
                        edited_data = st.session_state[editor_key]
                        changes = edited_data.get("edited_rows", {})
                        
                        if changes:
                            current_df = st.session_state[session_key]
                            
                            for row_idx_str, updated_values in changes.items():
                                row_idx = int(row_idx_str)
                                if "Zona Mezzanine" in updated_values:
                                    new_zona = str(updated_values["Zona Mezzanine"]).strip()
                                    
                                    current_df.at[row_idx, "Zona Mezzanine"] = new_zona
                                    id_req = current_df.at[row_idx, "ID Request"]
                                    
                                    # Sinkronisasi aman (hanya update kolom operasional F ke kanan)
                                    safe_conn_update(df_database, current_df, id_req)

                kolom_tampil_editor = ["ID Request", "Tujuan Pengiriman", "Jumlah Box", "Progress", "Zona Mezzanine", "Loader", "Waktu Preload", "Status"]
                df_editor_view = df_pick_current[[col for col in kolom_tampil_editor if col in df_pick_current.columns]].copy()

                edited_df = st.data_editor(
                    df_editor_view,
                    column_config={
                        "ID Request": st.column_config.TextColumn("ID Request", disabled=True),
                        "Tujuan Pengiriman": st.column_config.TextColumn("Tujuan Pengiriman", disabled=True),
                        "Jumlah Box": st.column_config.NumberColumn("Jumlah Box", disabled=True),
                        "Progress": st.column_config.NumberColumn("Progress", disabled=True),
                        "Zona Mezzanine": st.column_config.SelectboxColumn(
                            "📍 Zona Mezzanine",
                            help="Pilih zona penyimpanan dari dropdown",
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

            st.markdown("---")

            # --- 3. MENU MANIFEST DI DALAM TAB PRELOAD ---
            mode_manifest_key = f"mode_buat_manifest_{wilayah}"
            if mode_manifest_key not in st.session_state:
                st.session_state[mode_manifest_key] = False

            if not st.session_state[mode_manifest_key]:
                if st.button("➕ Buat Manifest Baru", key=f"btn_buka_manifest_{wilayah}", use_container_width=True):
                    st.session_state[mode_manifest_key] = True
                    st.rerun()
            else:
                st.markdown("### 📝 Form Pembuatan Manifest Baru")
                
                nomor_manifest = st.text_input("Nomor / Nama Manifest:", placeholder="Contoh: MNF-JKT-20260922-01", key=f"input_no_manifest_{wilayah}")
                buat_kosong = st.checkbox("Buat Manifest Kosong (Tanpa ID Request terlebih dahulu)", key=f"chk_manifest_kosong_{wilayah}")
                
                selected_ids_for_manifest = []
                
                if not buat_kosong:
                    st.markdown("#### Pilih ID Request yang Berstatus 🟡 Processed:")
                    
                    df_pick_data = st.session_state[session_key]
                    df_processed_only = df_pick_data[df_pick_data["Status"] == "🟡 Processed"]
                    
                    if not df_processed_only.empty:
                        for idx, row in df_processed_only.iterrows():
                            id_req = row["ID Request"]
                            tujuan = row.get("Tujuan Pengiriman", "-")
                            box = row.get("Jumlah Box", 0)
                            
                            is_checked = st.checkbox(
                                f"ID: **{id_req}** | Tujuan: {tujuan} | Total Box: {box}", 
                                key=f"chk_id_{wilayah}_{id_req}"
                            )
                            if is_checked:
                                selected_ids_for_manifest.append(id_req)
                    else:
                        st.info("⚠️ Belum ada ID Request dengan status '🟡 Processed' yang tersedia untuk dimasukkan ke manifest.")

                col_m_simpan, col_m_batal = st.columns(2)
                
                with col_m_simpan:
                    if st.button("💾 Simpan Manifest", key=f"btn_simpan_manifest_{wilayah}", use_container_width=True):
                        if not nomor_manifest.strip():
                            st.error("❌ Nomor/Nama Manifest wajib diisi!")
                        else:
                            wib_zone = timezone(timedelta(hours=7))
                            manifest_storage_key = f"list_manifest_{wilayah}"
                            if manifest_storage_key not in st.session_state:
                                st.session_state[manifest_storage_key] = []
                            
                            new_manifest_data = {
                                "Nomor Manifest": nomor_manifest.strip(),
                                "Wilayah": wilayah,
                                "Dibuat Oleh": st.session_state.user_nama,
                                "Waktu Dibuat": datetime.datetime.now(wib_zone).strftime("%Y-%m-%d %H:%M:%S"),
                                "Daftar ID Request": str(selected_ids_for_manifest) if selected_ids_for_manifest else "(Kosong)",
                                "Status Manifest": "Active"
                            }
                            
                            st.session_state[manifest_storage_key].append(new_manifest_data)
                            st.success(f"✅ Manifest **{nomor_manifest}** berhasil dibuat dengan {len(selected_ids_for_manifest)} ID Request!")
                            
                            st.session_state[mode_manifest_key] = False
                            st.rerun()

                with col_m_batal:
                    if st.button("❌ Batal", key=f"btn_batal_manifest_{wilayah}", use_container_width=True):
                        st.session_state[mode_manifest_key] = False
                        st.rerun()

            st.markdown("##### 📦 Daftar Manifest Aktif")
            manifest_storage_key = f"list_manifest_{wilayah}"
            if manifest_storage_key in st.session_state and st.session_state[manifest_storage_key]:
                df_manifest_list = pd.DataFrame(st.session_state[manifest_storage_key])
                st.dataframe(df_manifest_list, use_container_width=True, hide_index=True)
            else:
                st.info("Belum ada manifest aktif yang dibuat untuk cabang ini.")

        with tab_ondelivery:
            st.subheader(f"Proses On Delivery - {wilayah}")
            st.write("Centang kotak di bawah untuk menandai status pengiriman:")
            
            df_delivery = pd.DataFrame([
                {"ID Manifest": "MNF-001", "ID Request": "REQ-001", "Jumlah Box": "5/5", "Status": "Ready", "Mark as On Delivery": True},
                {"ID Manifest": "MNF-001", "ID Request": "REQ-002", "Jumlah Box": "12/12", "Status": "Process", "Mark as On Delivery": False}
            ])
            st.dataframe(df_delivery, use_container_width=True, hide_index=True)
