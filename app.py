import streamlit as st
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

# --- PENGATURAN HALAMAN ---
st.set_page_config(page_title="Aplikasi Preload & Picking Logistik", layout="wide")

st.title("📦 Sistem Manajemen Preload & Picking Logistik")

# --- KONEKSI GOOGLE SHEETS ---
# Pastikan di secrets.toml sudah diatur koneksi gsheets-nya
conn = st.connection("gsheets", type=GSheetsConnection)

# Fungsi untuk membaca data dari Google Sheets secara cepat & berkala
@st.cache_data(ttl=5)
def load_data_from_cloud():
    # Membaca sheet dengan nama "Database log" (sesuaikan jika nama sheet Anda berbeda)
    return conn.read(worksheet="Database log", ttl=0)

# Muat database utama
try:
    df_database = load_data_from_cloud()
except Exception as e:
    st.error(f"❌ Gagal terhubung ke Google Sheets. Periksa konfigurasi secrets Anda. Detail: {e}")
    st.stop()

# --- HEADER: INFORMASI USER & TOMBOL REFRESH GLOBAL ---
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    if "user_nama" not in st.session_state:
        st.session_state.user_nama = "Petugas Gudang"
    st.info(f"User Login: **{st.session_state.user_nama}**")

with col_head2:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        for key in list(st.session_state.keys()):
            if "df_picking_" in key or "list_manifest_" in key:
                del st.session_state[key]
        st.success("Data berhasil diperbarui dari Cloud!")
        st.rerun()

st.markdown("---")

# --- PEMILIHAN WILAYAH / CABANG ---
# Menyesuaikan dengan kolom wilayah yang ada di spreadsheet Anda
wilayah_candidates = [col for col in df_database.columns if 'wilayah' in col.lower() or 'cabang' in col.lower()]
actual_wilayah_col = wilayah_candidates[0] if wilayah_candidates else None

if actual_wilayah_col:
    wilayah_list = df_database[actual_wilayah_col].dropna().unique().tolist()
    wilayah = st.selectbox("Pilih Wilayah / Cabang Operasional:", wilayah_list)
    df_filtered = df_database[df_database[actual_wilayah_col] == wilayah].copy()
else:
    wilayah = "Pusat"
    df_filtered = df_database.copy()

# --- PEMBUATAN TAB UTAMA ---
tab_pick, tab_preload = st.tabs(["🚀 Proses Picking", "📋 Active Tab Preload"])

# ==========================================
# TAB 1: PROSES PICKING
# ==========================================
with tab_pick:
    st.subheader(f"Proses Picking - {wilayah}")
    
    session_key = f"df_picking_{wilayah}"
    if session_key not in st.session_state or st.session_state.get("current_wilayah") != wilayah:
        df_filtered_cabang = df_filtered.copy()
        
        # Deteksi kolom ID Request secara fleksibel tanpa merusak struktur asli
        id_col_candidates = [col for col in df_filtered_cabang.columns if 'id' in col.lower() or 'request' in col.lower()]
        if id_col_candidates:
            actual_id_col = id_col_candidates[0]
            df_filtered_cabang.rename(columns={actual_id_col: "ID Request"}, inplace=True)
        else:
            df_filtered_cabang["ID Request"] = "-"
        
        df_filtered_cabang["ID Request"] = df_filtered_cabang["ID Request"].astype(str).str.split('.').str[0].str.strip()
        
        # Standarisasi pengecekan kolom pendukung
        if "Jumlah Box" not in df_filtered_cabang.columns:
            df_filtered_cabang["Jumlah Box"] = 1
        else:
            df_filtered_cabang["Jumlah Box"] = pd.to_numeric(df_filtered_cabang["Jumlah Box"], errors='coerce').fillna(1).astype(int)

        if "Progress" not in df_filtered_cabang.columns:
            df_filtered_cabang["Progress"] = 0
        else:
            df_filtered_cabang["Progress"] = pd.to_numeric(df_filtered_cabang["Progress"], errors='coerce').fillna(0).astype(int)
        
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
        
        # Pertahankan kolom asli spreadsheet + kolom pendukung proses
        kolom_utama = list(df_database.columns)
        for kol in ["ID Request", "Progress", "Picker", "Waktu Picking", "Status"]:
            if kol not in kolom_utama:
                kolom_utama.append(kol)
                
        kolom_tersedia = [col for col in kolom_utama if col in df_filtered_cabang.columns]
        
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
                waktu_sekarang = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
                
                idx = df_pick_current[match_mask].index[0]
                jml_box = int(df_pick_current.loc[idx, "Jumlah Box"])
                current_prog = int(df_pick_current.loc[idx, "Progress"])
                
                new_prog = current_prog + 1
                if new_prog > jml_box:
                    new_prog = jml_box
                
                new_status = "🟡 Processed" if new_prog >= jml_box else "🔴 Pending"
                
                # Update State Lokal
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
                        
                        # Sinkronisasi Otomatis ke Google Sheets
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
                waktu_sekarang = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
                
                idx_m = df_pick_current[match_mask_m].index[0]
                jml_box_m = int(df_pick_current.loc[idx_m, "Jumlah Box"])
                current_prog_m = int(df_pick_current.loc[idx_m, "Progress"])
                
                new_prog_m = current_prog_m + int(manual_qty)
                if new_prog_m > jml_box_m:
                    new_prog_m = jml_box_m
                    st.warning(f"⚠️ Progress dibatasi maksimal sejumlah Jumlah Box ({jml_box_m})!")
                
                new_status_m = "🟡 Processed" if new_prog_m >= jml_box_m else "🔴 Pending"
                
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

    st.markdown("##### 📋 Monitoring Data Picking Cabang")
    if not df_pick_current.empty:
        st.dataframe(df_pick_current, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data logistik untuk ditampilkan pada cabang ini.")


# ==========================================
# TAB 2: ACTIVE TAB PRELOAD
# ==========================================
with tab_preload:
    st.subheader(f"Manifest & Preload - {wilayah}")
    
    mode_manifest_key = f"mode_buat_manifest_{wilayah}"
    if mode_manifest_key not in st.session_state:
        st.session_state[mode_manifest_key] = False

    if not st.session_state[mode_manifest_key]:
        if st.button("➕ Buat Manifest Baru", key=f"btn_buka_manifest_{wilayah}", use_container_width=True):
            st.session_state[mode_manifest_key] = True
            st.rerun()
    else:
        st.markdown("---")
        st.markdown("### 📝 Form Pembuatan Manifest Baru")
        
        nomor_manifest = st.text_input("Nomor / Nama Manifest:", placeholder="Contoh: MNF-JKT-20260922-01", key=f"input_no_manifest_{wilayah}")
        buat_kosong = st.checkbox("Buat Manifest Kosong (Tanpa ID Request terlebih dahulu)", key=f"chk_manifest_kosong_{wilayah}")
        
        selected_ids_for_manifest = []
        
        if not buat_kosong:
            st.markdown("#### Pilih ID Request yang Berstatus 🟡 Processed:")
            
            session_key_pick = f"df_picking_{wilayah}"
            if session_key_pick in st.session_state:
                df_pick_data = st.session_state[session_key_pick]
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
            else:
                st.warning("⚠️ Data picking untuk wilayah ini belum dimuat.")

        col_m_simpan, col_m_batal = st.columns(2)
        
        with col_m_simpan:
            if st.button("💾 Simpan Manifest", key=f"btn_simpan_manifest_{wilayah}", use_container_width=True):
                if not nomor_manifest.strip():
                    st.error("❌ Nomor/Nama Manifest wajib diisi!")
                else:
                    manifest_storage_key = f"list_manifest_{wilayah}"
                    if manifest_storage_key not in st.session_state:
                        st.session_state[manifest_storage_key] = []
                    
                    new_manifest_data = {
                        "Nomor Manifest": nomor_manifest.strip(),
                        "Wilayah": wilayah,
                        "Dibuat Oleh": st.session_state.user_nama,
                        "Waktu Dibuat": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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

    st.markdown("---")
    st.markdown("##### 📦 Daftar Manifest Aktif")
    
    manifest_storage_key = f"list_manifest_{wilayah}"
    if manifest_storage_key in st.session_state and st.session_state[manifest_storage_key]:
        df_manifest_list = pd.DataFrame(st.session_state[manifest_storage_key])
        st.dataframe(df_manifest_list, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada manifest aktif yang dibuat untuk cabang ini.")
