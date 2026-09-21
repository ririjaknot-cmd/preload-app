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
            "ID Request", "Picking", "Preload", "On Delivery"
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
            
            # Inisialisasi session state untuk menyimpan perubahan picking per cabang selama sesi aktif
            session_key = f"df_picking_{wilayah}"
            if session_key not in st.session_state or st.session_state.get("current_wilayah") != wilayah:
                df_filtered_cabang = df_filtered.copy()
                
                # Standarisasi Kolom ID (Paksa jadi string bersih)
                id_col_candidates = [col for col in df_filtered_cabang.columns if 'id' in col.lower() or 'request' in col.lower()]
                if id_col_candidates:
                    actual_id_col = id_col_candidates[0]
                    df_filtered_cabang.rename(columns={actual_id_col: "ID Request"}, inplace=True)
                else:
                    df_filtered_cabang["ID Request"] = "-"
                
                df_filtered_cabang["ID Request"] = df_filtered_cabang["ID Request"].astype(str).str.split('.').str[0].str.strip()
                
                # Standarisasi Kolom Jumlah Box & Progress
                if "Jumlah Box" not in df_filtered_cabang.columns:
                    df_filtered_cabang["Jumlah Box"] = 1
                else:
                    df_filtered_cabang["Jumlah Box"] = pd.to_numeric(df_filtered_cabang["Jumlah Box"], errors='coerce').fillna(1).astype(int)

                if "Progress" not in df_filtered_cabang.columns:
                    df_filtered_cabang["Progress"] = 0
                else:
                    df_filtered_cabang["Progress"] = pd.to_numeric(df_filtered_cabang["Progress"], errors='coerce').fillna(0).astype(int)
                
                # Standarisasi Kolom Picker, Waktu, & Status
                if "Picker" not in df_filtered_cabang.columns:
                    df_filtered_cabang["Picker"] = "-"
                else:
                    df_filtered_cabang["Picker"] = df_filtered_cabang["Picker"].fillna("-").astype(str).replace(["None", "nan", ""], "-")
                
                if "Waktu Picking" not in df_filtered_cabang.columns:
                    df_filtered_cabang["Waktu Picking"] = "-"
                else:
                    df_filtered_cabang["Waktu Picking"] = df_filtered_cabang["Waktu Picking"].fillna("-").astype(str).replace(["None", "nan", ""], "-")
                
                def mapping_status_picking(row):
                    prog = row.get("Progress", 0)
                    jml = row.get("Jumlah Box", 1)
                    if prog >= jml and jml > 0:
                        return "🟡 Processed"
                    else:
                        return "🔴 Pending"

                df_filtered_cabang["Status"] = df_filtered_cabang.apply(mapping_status_picking, axis=1)
                
                kolom_picking = ["ID Request", "Tujuan Pengiriman", "Jumlah Box", "Progress", "Picker", "Waktu Picking", "Status"]
                kolom_tersedia = [col for col in kolom_picking if col in df_filtered_cabang.columns]
                
                st.session_state[session_key] = df_filtered_cabang[kolom_tersedia].copy()
                st.session_state["current_wilayah"] = wilayah
                
            df_pick_current = st.session_state[session_key]

            # --- OPSI 1: SCANNER BARCODE CEPAT (+1 BOX) ---
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
                        import datetime
                        waktu_sekarang = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
                        
                        idx = df_pick_current[match_mask].index[0]
                        jml_box = int(df_pick_current.loc[idx, "Jumlah Box"])
                        current_prog = int(df_pick_current.loc[idx, "Progress"])
                        
                        new_prog = current_prog + 1
                        if new_prog > jml_box:
                            new_prog = jml_box
                        
                        new_status = "🟡 Processed" if new_prog >= jml_box else "🔴 Pending"
                        
                        # Update state lokal
                        df_pick_current.loc[idx, "Progress"] = new_prog
                        df_pick_current.loc[idx, "Picker"] = st.session_state.user_nama
                        df_pick_current.loc[idx, "Waktu Picking"] = waktu_sekarang
                        df_pick_current.loc[idx, "Status"] = new_status
                        
                        try:
                            global_id_candidates = [col for col in df_database.columns if 'id' in col.lower() or 'request' in col.lower()]
                            if global_id_candidates:
                                global_id_col = global_id_candidates[0]
                                global_mask = df_database[global_id_col].astype(str).str.split('.').str[0].str.strip() == scan_input
                                
                                if "Progress" in df_database.columns:
                                    df_database["Progress"] = pd.to_numeric(df_database["Progress"], errors='coerce').fillna(0).astype(int)
                                    df_database.loc[global_mask, "Progress"] = new_prog
                                if "Picker" in df_database.columns:
                                    df_database["Picker"] = df_database["Picker"].astype(str)
                                    df_database.loc[global_mask, "Picker"] = str(st.session_state.user_nama)
                                if "Waktu Picking" in df_database.columns:
                                    df_database["Waktu Picking"] = df_database["Waktu Picking"].astype(str)
                                    df_database.loc[global_mask, "Waktu Picking"] = str(waktu_sekarang)
                                if "Status" in df_database.columns:
                                    df_database["Status"] = df_database["Status"].astype(str)
                                    df_database.loc[global_mask, "Status"] = "Processed" if new_prog >= jml_box else "Pending"
                        except Exception:
                            pass

                        st.session_state[f"last_msg_{wilayah}"] = ("success", f"✅ **{scan_input}** (+1 Box, Progress: {new_prog}/{jml_box})")
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

            # --- OPSI 2: INPUT MANUAL JUMLAH BESAR (PULUHAN / RATUSAN BOX) ---
            with st.expander("📦 Input Manual Jumlah Box Besar (Untuk Puluhan/Ratusan Box)"):
                col_m1, col_m2, col_m3 = st.columns([2, 2, 1])
                with col_m1:
                    manual_id = st.text_input("Ketik ID Request", key=f"manual_id_{wilayah}", placeholder="Masukkan ID...")
                with col_m2:
                    manual_qty = st.number_input("Jumlah Box yang Ingin Ditambahkan", min_value=1, value=1, step=1, key=f"manual_qty_{wilayah}")
                with col_m3:
                    st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True) # Penyelaras tinggi tombol
                    btn_proses_manual = st.button("Proses", key=f"btn_manual_{wilayah}", use_container_width=True)

                if btn_proses_manual and manual_id:
                    clean_manual_id = manual_id.strip()
                    match_mask_m = df_pick_current["ID Request"] == clean_manual_id
                    
                    if match_mask_m.any():
                        import datetime
                        waktu_sekarang = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
                        
                        idx_m = df_pick_current[match_mask_m].index[0]
                        jml_box_m = int(df_pick_current.loc[idx_m, "Jumlah Box"])
                        current_prog_m = int(df_pick_current.loc[idx_m, "Progress"])
                        
                        # Tambahkan jumlah box sesuai input manual
                        new_prog_m = current_prog_m + int(manual_qty)
                        if new_prog_m > jml_box_m:
                            new_prog_m = jml_box_m
                            st.warning(f"⚠️ Progress dibatasi maksimal sejumlah Jumlah Box ({jml_box_m})!")
                        
                        new_status_m = "🟡 Processed" if new_prog_m >= jml_box_m else "🔴 Pending"
                        
                        # Update state lokal
                        df_pick_current.loc[idx_m, "Progress"] = new_prog_m
                        df_pick_current.loc[idx_m, "Picker"] = st.session_state.user_nama
                        df_pick_current.loc[idx_m, "Waktu Picking"] = waktu_sekarang
                        df_pick_current.loc[idx_m, "Status"] = new_status_m
                        
                        try:
                            global_id_candidates = [col for col in df_database.columns if 'id' in col.lower() or 'request' in col.lower()]
                            if global_id_candidates:
                                global_id_col = global_id_candidates[0]
                                global_mask_m = df_database[global_id_col].astype(str).str.split('.').str[0].str.strip() == clean_manual_id
                                
                                if "Progress" in df_database.columns:
                                    df_database["Progress"] = pd.to_numeric(df_database["Progress"], errors='coerce').fillna(0).astype(int)
                                    df_database.loc[global_mask_m, "Progress"] = new_prog_m
                                if "Picker" in df_database.columns:
                                    df_database["Picker"] = df_database["Picker"].astype(str)
                                    df_database.loc[global_mask_m, "Picker"] = str(st.session_state.user_nama)
                                if "Waktu Picking" in df_database.columns:
                                    df_database["Waktu Picking"] = df_database["Waktu Picking"].astype(str)
                                    df_database.loc[global_mask_m, "Waktu Picking"] = str(waktu_sekarang)
                                if "Status" in df_database.columns:
                                    df_database["Status"] = df_database["Status"].astype(str)
                                    df_database.loc[global_mask_m, "Status"] = "Processed" if new_prog_m >= jml_box_m else "Pending"
                        except Exception:
                            pass

                        st.success(f"✅ ID **{clean_manual_id}** berhasil ditambah {manual_qty} box (Progress: {new_prog_m}/{jml_box_m})")
                        st.rerun()
                    else:
                        st.error(f"❌ ID Request **{clean_manual_id}** tidak ditemukan di cabang ini!")

            # Tombol Sinkronisasi Manual ke Google Sheets
            col_btn1, col_btn2 = st.columns([2, 4])
            with col_btn1:
                if st.button("💾 Simpan/Sinkron ke Cloud", key=f"sync_cloud_{wilayah}", use_container_width=True):
                    try:
                        conn.update(worksheet="Database log", data=df_database)
                        st.success("Berhasil sinkronisasi ke Google Sheets!")
                    except Exception as e:
                        st.error(f"Gagal sync: {e}")

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

            st.markdown("##### 📋 Monitoring Data Picking Cabang")
            if not df_pick_current.empty:
                st.dataframe(df_pick_current, use_container_width=True, hide_index=True)
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
