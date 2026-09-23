import streamlit as st
import pandas as pd
import datetime
from datetime import timezone, timedelta
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components

# Konfigurasi halaman
st.set_page_config(page_title="V2 Pre Load", layout="wide")

# --- KAMUS DATA PENGGUNA ---
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

def load_data_live():
    try:
        df = conn.read(worksheet="Database log", ttl=0)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        print(f"Error load data: {e}")
        return pd.DataFrame()

# --- FUNGSI AMAN UPDATE REAL-TIME SESUAI KOLOM GSHEETS ---
def safe_conn_update_realtime(id_request_target, updated_values_dict):
    try:
        df_fresh = conn.read(worksheet="Database log", ttl=0)
        df_fresh.columns = df_fresh.columns.str.strip()

        # Deteksi kolom ID
        id_col_candidates = [col for col in df_fresh.columns if col.lower() == 'id' or 'request' in col.lower()]
        if not id_col_candidates:
            return False
        global_id_col = id_col_candidates[0]
        
        # Standarisasi kolom wajib agar sesuai dengan Google Sheets Anda
        kolom_wajib = ["ID", "Tujuan Pengiriman", "Jam Proses Scan", "Tanggal Proses Scan", "Jumlah Box", "Loader", "Waktu Preload", "Status", "Zona Mezzanine"]
        for col in kolom_wajib:
            if col not in df_fresh.columns:
                df_fresh[col] = 0 if col == "Jumlah Box" else "-"
        
        mask = df_fresh[global_id_col].astype(str).str.split('.').str[0].str.strip() == str(id_request_target).strip()
        
        if mask.any():
            for col, val in updated_values_dict.items():
                if col in df_fresh.columns:
                    df_fresh.loc[mask, col] = val
            
            conn.update(worksheet="Database log", data=df_fresh)
            st.cache_data.clear()
            return True
        return False
    except Exception as e:
        print(f"Error safe_conn_update_realtime: {e}")
        return False

# --- HALAMAN LOGIN ---
def tampilkan_halaman_login():
    st.markdown("<h2 style='text-align: center;'>🔐 Login V2 Pre Load System</h2>", unsafe_allow_html=True)
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
                    st.error("Email atau PIN salah.")

if not st.session_state.logged_in:
    tampilkan_halaman_login()
else:
    # --- HEADER ---
    col_head1, col_head2 = st.columns([4, 1])
    with col_head1:
        st.markdown("### V2 Pre Load 2026")
    with col_head2:
        st.text(f"👤 {st.session_state.user_nama}")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    st.divider()
    df_database = load_data_live()

    # --- SIDEBAR NAVIGASI ---
    st.sidebar.markdown("### 🗂️ Menu Navigasi")
    menu_pilihan = st.sidebar.radio("Pilih Halaman Utama:", ["Summary Status", "Operasional Cabang"], label_visibility="collapsed")

    wilayah = None
    if menu_pilihan == "Operasional Cabang":
        st.sidebar.header("Tujuan Pengiriman")
        wilayah = st.sidebar.radio(
            "Pilih Cabang:",
            ["Jakarta Pusat", "Jakarta Barat", "Jakarta Utara", "Tangerang", "Cikupa", "Bandung", "Semarang", "Surabaya Timur", "Surabaya Barat", "Yogyakarta", "Makassar", "Medan", "Official Store"]
        )

    if menu_pilihan == "Summary Status":
        st.title("📊 Summary Status Semua Cabang")
        if not df_database.empty and "Tujuan Pengiriman" in df_database.columns:
            if "Jumlah Box" in df_database.columns:
                df_summary = df_database.groupby("Tujuan Pengiriman")["Jumlah Box"].sum().reset_index()
                df_summary.columns = ["Tujuan Pengiriman", "Total Jumlah Box"]
            else:
                df_summary = df_database.groupby("Tujuan Pengiriman").size().reset_index(name="Total Log Data")
            st.dataframe(df_summary, use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ Data kosong atau kolom 'Tujuan Pengiriman' tidak ditemukan.")
    else:
        st.title(f"Cabang - {wilayah}")
        df_filtered = df_database[df_database["Tujuan Pengiriman"] == wilayah].copy() if not df_database.empty and "Tujuan Pengiriman" in df_database.columns else pd.DataFrame()

        # Standarisasi kolom tampilan
        for col, default_val in [("Jumlah Box", 1), ("Loader", "-"), ("Waktu Preload", "-"), ("Status", "Pending"), ("Zona Mezzanine", "-")]:
            if col not in df_filtered.columns:
                df_filtered[col] = default_val

        tab_id, tab_preload, tab_ondelivery = st.tabs(["ID Request", "Preload", "On Delivery"])

        with tab_id:
            st.subheader(f"Data Logistik - {wilayah}")
            keyword_cari = st.text_input("🔍 Cari ID Request:", key="search_id")
            df_display = df_filtered.copy()
            if keyword_cari and not df_display.empty:
                id_col = [c for c in df_display.columns if c.lower() == 'id'][0]
                df_display = df_display[df_display[id_col].astype(str).str.contains(keyword_cari, case=False, na=False)]
            st.dataframe(df_display, use_container_width=True, hide_index=True)

        with tab_preload:
            st.subheader(f"Proses Preload & Manifest - {wilayah}")
            
            df_fc = df_filtered.copy()
            id_col_name = [c for c in df_fc.columns if c.lower() == 'id'][0] if any(c.lower() == 'id' for c in df_fc.columns) else "ID"
            if id_col_name != "ID":
                df_fc.rename(columns={id_col_name: "ID"}, inplace=True)
            
            df_fc["ID"] = df_fc["ID"].astype(str).str.split('.').str[0].str.strip()
            df_fc["Jumlah Box"] = pd.to_numeric(df_fc["Jumlah Box"], errors='coerce').fillna(1).astype(int)

            input_widget_key = f"input_scan_{wilayah}"
            if input_widget_key not in st.session_state:
                st.session_state[input_widget_key] = ""

            def proses_input_scan():
                scan_input = st.session_state[input_widget_key].strip()
                if not scan_input:
                    return
                
                df_live_check = load_data_live()
                df_cabang_live = df_live_check[df_live_check["Tujuan Pengiriman"] == wilayah].copy()
                id_c = [c for c in df_cabang_live.columns if c.lower() == 'id'][0]
                df_cabang_live.rename(columns={id_c: "ID"}, inplace=True)
                df_cabang_live["ID"] = df_cabang_live["ID"].astype(str).str.split('.').str[0].str.strip()

                match_mask = df_cabang_live["ID"] == scan_input
                if match_mask.any():
                    wib_zone = timezone(timedelta(hours=7))
                    waktu_sekarang = datetime.datetime.now(wib_zone).strftime("%Y-%m-%d %H:%M:%S")
                    
                    update_payload = {
                        "Loader": str(st.session_state.user_nama),
                        "Waktu Preload": str(waktu_sekarang),
                        "Status": "Processed"
                    }
                    
                    success = safe_conn_update_realtime(scan_input, update_payload)
                    if success:
                        st.session_state[f"last_msg_{wilayah}"] = ("success", f"✅ ID **{scan_input}** berhasil diproses!")
                    else:
                        st.session_state[f"last_msg_{wilayah}"] = ("error", f"❌ Gagal memperbarui Google Sheets.")
                else:
                    st.session_state[f"last_msg_{wilayah}"] = ("error", f"❌ ID **{scan_input}** tidak ditemukan di cabang ini!")
                
                st.session_state[input_widget_key] = ""

            st.text_input("📷 Scan / Masukkan ID:", key=input_widget_key, on_change=proses_input_scan, placeholder="Ketik ID lalu tekan Enter...")

            if f"last_msg_{wilayah}" in st.session_state:
                m_type, m_text = st.session_state[f"last_msg_{wilayah}"]
                if m_type == "success": st.success(m_text)
                else: st.error(m_text)
                del st.session_state[f"last_msg_{wilayah}"]

            # Data Editor untuk Zona Mezzanine
            list_pilihan_zona = ["-", *[f"A{i}" for i in range(1, 12)], *[f"B{i}" for i in range(1, 10)], "SC 1", "SC 2"]
            editor_key = f"data_editor_zona_{wilayah}"

            def handle_zona_change():
                if editor_key in st.session_state:
                    changes = st.session_state[editor_key].get("edited_rows", {})
                    for row_idx_str, updated_values in changes.items():
                        if "Zona Mezzanine" in updated_values:
                            new_zona = str(updated_values["Zona Mezzanine"]).strip()
                            id_req = str(df_fc.at[int(row_idx_str), "ID"]).strip()
                            safe_conn_update_realtime(id_req, {"Zona Mezzanine": new_zona})

            kolom_tampil = ["ID", "Tujuan Pengiriman", "Jam Proses Scan", "Tanggal Proses Scan", "Jumlah Box", "Loader", "Waktu Preload", "Status", "Zona Mezzanine"]
            df_editor_view = df_fc[[col for col in kolom_tampil if col in df_fc.columns]].copy()

            st.data_editor(
                df_editor_view,
                column_config={
                    "ID": st.column_config.TextColumn("ID", disabled=True),
                    "Tujuan Pengiriman": st.column_config.TextColumn("Tujuan Pengiriman", disabled=True),
                    "Jumlah Box": st.column_config.NumberColumn("Jumlah Box", disabled=True),
                    "Zona Mezzanine": st.column_config.SelectboxColumn("📍 Zona Mezzanine", options=list_pilihan_zona, required=False),
                    "Loader": st.column_config.TextColumn("Loader", disabled=True),
                    "Waktu Preload": st.column_config.TextColumn("Waktu Preload", disabled=True),
                    "Status": st.column_config.TextColumn("Status", disabled=True)
                },
                use_container_width=True,
                hide_index=True,
                key=editor_key,
                on_change=handle_zona_change
            )

        with tab_ondelivery:
            st.subheader(f"Proses On Delivery - {wilayah}")
            st.info("Fitur On Delivery aktif.")
            st.write("Centang kotak di bawah untuk menandai status pengiriman:")
            
            df_delivery = pd.DataFrame([
                {"ID Manifest": "MNF-001", "ID Request": "REQ-001", "Jumlah Box": "5/5", "Status": "Ready", "Mark as On Delivery": True},
                {"ID Manifest": "MNF-001", "ID Request": "REQ-002", "Jumlah Box": "12/12", "Status": "Process", "Mark as On Delivery": False}
            ])
            st.dataframe(df_delivery, use_container_width=True, hide_index=True)
