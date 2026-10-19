import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components
import datetime
import gspread

st.set_page_config(page_title="V2 Pre Load", layout="wide")

USER_DATABASE = {
    "riri.jaknot@gmail.com": {"nama": "Riri Ridwan Genta Yudha", "pin": "Kronus666"},
    "adamrayhan.jaknot@gmail.com": {"nama": "Adam Rayhan", "pin": "1234"},
    "satriopjn@gmail.com": {"nama": "Satrio Sudiyanto", "pin": "1234"},
    "ahmadallfiansc@gmail.com": {"nama": "Ahmad Alfian", "pin": "1234"},
    "ajikurnianto93@gmail.com": {"nama": "Aji Kurnianto", "pin": "1234"},
    "alekhandoko98@gmail.com": {"nama": "Alek Handoko", "pin": "1234"},
    "alghifariathian@gmail.com": {"nama": "Athian Alghifari", "pin": "messigoat"},
    "amelyaadm@gmail.com": {"nama": "Amelya Putri", "pin": "1234"},
    "ardi03027@gmail.com": {"nama": "Eka Febri Setiardi", "pin": "1234"},
    "arifsa2703@gmail.com": {"nama": "Arif Saputra", "pin": "1234"},
    "bedhel089f@gmail.com": {"nama": "Fadhilah Al Azani", "pin": "1234"},
    "olifiaekmanda7@gmail.com": {"nama": "Olifia Ekmanda", "pin": "1234"},
    "rayadiagung22@gmail.com": {"nama": "Rayadi Agung", "pin": "emyu13"},
    "siwhayy170@gmail.com": {"nama": "Wahyu Adi Sucipto", "pin": "1234"},
    "tasyaameliaa05@gmail.com": {"nama": "Tasya Amelia", "pin": "1234"},
    "mahesaagusta28@gmail.com": {"nama": "Mahesa Agusta", "pin": "1234"}
}


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "user_nama" not in st.session_state:
    st.session_state.user_nama = ""


conn = st.connection("gsheets", type=GSheetsConnection)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.success("Cache dibersihkan, memuat data terbaru...")
    st.rerun()

@st.cache_data(ttl=300, show_spinner="Memuat data dari Google Sheets...")
def load_cached_database():
    df = conn.read(worksheet="Database log", ttl=0)
    return df

df_database = load_cached_database()

def format_status_dengan_ikon(progress_val, jumlah_box_db):
    if progress_val is None:
        return "🔴 Pending"
    
    prog_str = str(progress_val).strip().lower()
    if prog_str in ["", "none", "nan", "nat", "0"]:
        return "🔴 Pending"
    
    try:
        prog_int = int(float(progress_val))
        max_box = int(float(jumlah_box_db))
    except (ValueError, TypeError):
        return "🔴 Pending"
        
    if prog_int <= 0:
        return "🔴 Pending"
    elif prog_int < max_box:
        return "🟡 Not Completed"
    else:
        return "🟢 Completed"

def tampilkan_halaman_login():
    st.markdown("<h2 style='text-align: center;'>🔐 Login Pre Load</h2>", unsafe_allow_html=True)
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

if not st.session_state.logged_in:
    tampilkan_halaman_login()
else:
    col_head1, col_head2 = st.columns([4, 1])
    with col_head1:
        st.markdown("### V2 Pre Load Shipment Cabang ")
    with col_head2:
        st.text(f"👽 {st.session_state.user_nama}")
        
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
        df_database = load_cached_database()
    except Exception as e:
        st.error("❌ Gagal terhubung ke Google Sheets. Detail Error:")
        st.exception(e)
        df_database = pd.DataFrame()

    st.sidebar.markdown("### Internal Menu")
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
        st.title(" Summary Status Cabang")

        if not df_database.empty and "Tujuan Pengiriman" in df_database.columns:
            if "Jumlah Box" in df_database.columns:
                df_summary = df_database.groupby("Tujuan Pengiriman")["Jumlah Box"].sum().reset_index()
                df_summary.columns = ["Tujuan Pengiriman", "Total Jumlah Box"]
            else:
                df_summary = df_database.groupby("Tujuan Pengiriman").size().reset_index(name="Total Log Data")

            st.dataframe(df_summary, use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ Database kosong atau kolom 'Tujuan Pengiriman' tidak ditemukan.")

    else:
        st.title(f"Cabang - {wilayah}")

        if not df_database.empty and "Tujuan Pengiriman" in df_database.columns:
            df_filtered = df_database[df_database["Tujuan Pengiriman"] == wilayah].copy()
            if "Status" in df_filtered.columns:
                df_filtered = df_filtered[df_filtered["Status"].astype(str).str.strip().str.lower() != "on delivery"]
        else:
            df_filtered = pd.DataFrame()

        if not df_filtered.empty and "Jumlah Box" in df_filtered.columns:
            df_filtered["Jumlah Box"] = df_filtered["Jumlah Box"].fillna(0).astype(int)

        tab_id, tab_preload, tab_manifest = st.tabs([
            "ID Request", "Preload", "Manifest"
        ])

        with tab_id:
            st.subheader(f"Data Preload & Pencarian ID - {wilayah}")
            keyword_cari = st.text_input("🔍 Cari ID Request:", placeholder="Masukkan ID Request yang ingin dicari...", key="search_id_request")
            
            df_display = df_filtered.copy()
            
            if keyword_cari and not df_database.empty:
                df_all_branch = df_database[df_database["Tujuan Pengiriman"] == wilayah].copy() if "Tujuan Pengiriman" in df_database.columns else pd.DataFrame()
                if not df_all_branch.empty:
                    id_col_candidates = [col for col in df_all_branch.columns if 'id' in col.lower() or 'request' in col.lower()]
                    if id_col_candidates:
                        target_col = id_col_candidates[0]
                        df_matched = df_all_branch[df_all_branch[target_col].astype(str).str.contains(keyword_cari, case=False, na=False)]
                        if not df_matched.empty:
                            df_display = df_matched
                            
                            for _, m_row in df_matched.iterrows():
                                m_id = str(m_row.get(target_col, "")).split('.')[0].strip()
                                m_status = str(m_row.get("Status", "")).strip().lower()
                                if m_status == "on delivery":
                                    st.warning(f"**Status ID {m_id} : On Delivery** (ID sudah dalam proses pengiriman).")

            if not df_display.empty:
                status_formatted_list = []
                for idx, row in df_display.iterrows():
                    try:
                        jb = row.get("Jumlah Box") or 0
                        pr = row.get("Progress")
                        st_formatted = format_status_dengan_ikon(pr, jb)
                        if str(row.get("Status", "")).strip().lower() == "on delivery":
                            st_formatted = "On Delivery"
                        status_formatted_list.append(st_formatted)
                    except Exception:
                        status_formatted_list.append("🔴 Pending")
                
                df_display["Status"] = status_formatted_list

            if not df_display.empty:
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.info("Tidak ada data preload yang cocok atau tersedia untuk cabang ini.")
        
        with tab_preload:
            st.subheader(f"Proses Preload & Scan - {wilayah}")

            local_df_key = f"local_df_preload_{wilayah}"
            changes_key = f"has_unsaved_changes_{wilayah}"
            
            if local_df_key not in st.session_state or st.sidebar.button("🔄 Reset Draft", key=f"reset_{wilayah}"):
                st.session_state[local_df_key] = df_filtered.copy()
                st.session_state[changes_key] = False

            df_lokal = st.session_state[local_df_key]
            id_col_name = 'ID' if 'ID' in df_lokal.columns else 'id request'

            for col_teks in ["Status", "Loader", "Waktu Preload", "Zona Mezzanine"]:
                if col_teks in df_lokal.columns:
                    df_lokal[col_teks] = df_lokal[col_teks].astype(str).replace({"nan": "", "None": ""})
            if "Progress" in df_lokal.columns:
                df_lokal["Progress"] = pd.to_numeric(df_lokal["Progress"], errors="coerce").fillna(0)

            form_input_key = f"form_input_preload_{wilayah}"
            with st.form(key=form_input_key, clear_on_submit=True):
                col_f1, col_f2 = st.columns([3, 1])
                with col_f1:
                    input_id_val = st.text_input("📷 Scan / Masukkan ID Request:", placeholder="Arahkan scanner atau ketik ID di sini...")
                with col_f2:
                    jumlah_box_val = st.number_input("Jumlah Box:", min_value=1, value=1, step=1)
                
                submit_input = st.form_submit_button("Proses Preload", type="primary", use_container_width=True)
            
            if submit_input:
                target_id = input_id_val.strip().split('.')[0]
                current_ts = str(datetime.datetime.now().timestamp()) + "_" + str(datetime.datetime.now().microsecond)
                
                if not target_id:
                    st.session_state[f"last_msg_{wilayah}"] = ("error", "⚠️ Masukkan atau scan ID terlebih dahulu.")
                    st.session_state[f"sound_effect_{wilayah}"] = ("error", current_ts)
                    st.rerun()
                else:
                    matched = df_lokal[df_lokal[id_col_name].astype(str).str.split('.').str[0].str.strip() == target_id]
                    
                    if matched.empty:
                        st.session_state[f"last_msg_{wilayah}"] = ("error", f"❌ ID **{target_id}** tidak terdaftar di database cabang ini.")
                        st.session_state[f"sound_effect_{wilayah}"] = ("error", current_ts)
                        st.rerun()
                    else:
                        idx = matched.index[0]
                        row = df_lokal.loc[idx]
                        
                        if str(row.get("Status", "")).strip().lower() == "on delivery":
                            st.session_state[f"last_msg_{wilayah}"] = ("error", f" ID **{target_id}** berstatus On Delivery. Input ditolak.")
                            st.session_state[f"sound_effect_{wilayah}"] = ("error", current_ts)
                            st.rerun()
                        else:
                            try:
                                max_box = int(float(str(row.get("Jumlah Box", 0))))
                                current_prog = int(float(row.get("Progress", 0))) if pd.notna(row.get("Progress")) else 0
                            except:
                                max_box, current_prog = 0, 0

                            if current_prog >= max_box and max_box > 0:
                                st.session_state[f"last_msg_{wilayah}"] = ("error", f"⚠️ ID **{target_id}** sudah berstatus **Completed** (Maksimal: {max_box} box).")
                                st.session_state[f"sound_effect_{wilayah}"] = ("error", current_ts)
                                st.rerun()
                            elif (current_prog + int(jumlah_box_val)) > max_box:
                                sisa_box = max_box - current_prog
                                st.session_state[f"last_msg_{wilayah}"] = ("error", f"❌ Jumlah box melebihi sisa kuota (Sisa kuota: {sisa_box} box).")
                                st.session_state[f"sound_effect_{wilayah}"] = ("error", current_ts)
                                st.rerun()
                            else:
                                new_prog = current_prog + int(jumlah_box_val)
                                new_status = "Not Completed" if new_prog < max_box else "Completed"
                                now_str = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
                                
                                df_lokal.at[idx, "Progress"] = new_prog
                                df_lokal.at[idx, "Status"] = new_status
                                df_lokal.at[idx, "Loader"] = str(st.session_state.user_nama)
                                df_lokal.at[idx, "Waktu Preload"] = now_str
                                
                                st.session_state[changes_key] = True
                                st.session_state[f"last_msg_{wilayah}"] = ("success", f"✅ ID **{target_id}** berhasil ditambahkan (+{jumlah_box_val} Box). Progress: **{new_prog}/{max_box}**")
                                st.session_state[f"sound_effect_{wilayah}"] = ("success", current_ts)
                                st.rerun()

            if f"last_msg_{wilayah}" in st.session_state:
                m_type, m_text = st.session_state[f"last_msg_{wilayah}"]
                if m_type == "success":
                    st.success(m_text)
                else:
                    st.error(m_text)
                del st.session_state[f"last_msg_{wilayah}"]

            if f"sound_effect_{wilayah}" in st.session_state:
                sound_type, timestamp_id = st.session_state[f"sound_effect_{wilayah}"]
                local_audio_path = "assets/Sukses.mp3" if sound_type == "success" else "assets/Gagal.mp3"
                
                import base64
                try:
                    with open(local_audio_path, "rb") as f:
                        audio_bytes = f.read()
                    audio_base64 = base64.b64encode(audio_bytes).decode()
                    
                    unique_audio_id = f"audio_{timestamp_id}"
                    
                    audio_html = f'''
                        <audio id="{unique_audio_id}" autoplay style="display:none;">
                            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mpeg">
                        </audio>
                        <script>
                            var audio = document.getElementById("{unique_audio_id}");
                            if (audio) {{
                                audio.volume = 1.0;
                                audio.play().catch(function(error) {{
                                    console.log("Autoplay dicegah oleh browser: ", error);
                                }});
                            }}
                        </script>
                    '''
                    st.markdown(audio_html, unsafe_allow_html=True)
                except Exception as e:
                    st.warning(f"File audio lokal tidak ditemukan: {local_audio_path}")
                    
                del st.session_state[f"sound_effect_{wilayah}"]

            st.markdown("---")

            if st.session_state.get(changes_key, False):
                st.warning("⚠️ Ada perubahan data yang **belum disimpan** ke Database!")
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.button("💾 Save", type="primary", use_container_width=True, key=f"save_{wilayah}"):
                        try:
                            creds_dict = dict(st.secrets["connections"]["gsheets"])
                            gc = gspread.service_account_from_dict(creds_dict)
                            spreadsheet_name = st.secrets["connections"]["gsheets"].get("spreadsheet")
                            sh = gc.open_by_url(spreadsheet_name) if spreadsheet_name.startswith("http") else gc.open(spreadsheet_name)
                            ws = sh.worksheet("Database log")

                            records_main = ws.get_all_records()
                            header_main = ws.row_values(1)

                            prog_col_i = header_main.index("Progress") + 1 if "Progress" in header_main else 6
                            loader_col_i = header_main.index("Loader") + 1 if "Loader" in header_main else 7
                            waktu_col_i = header_main.index("Waktu Preload") + 1 if "Waktu Preload" in header_main else 8
                            status_col_i = header_main.index("Status") + 1 if "Status" in header_main else 10

                            cell_updates = []
                            for _, row in df_lokal.iterrows():
                                r_id = str(row.get("ID") or row.get("id request") or "").split('.')[0].strip()
                                p_val = row.get("Progress")
                                l_val = row.get("Loader")
                                w_val = row.get("Waktu Preload")
                                s_val = row.get("Status")

                                for r_idx, r_val in enumerate(records_main, start=2):
                                    sheet_id_str = str(r_val.get("ID") or r_val.get("id request") or "").split('.')[0].strip()
                                    if sheet_id_str == r_id:
                                        cell_updates.append(gspread.Cell(r_idx, prog_col_i, int(p_val) if pd.notna(p_val) else 0))
                                        cell_updates.append(gspread.Cell(r_idx, loader_col_i, str(l_val) if pd.notna(l_val) else ""))
                                        cell_updates.append(gspread.Cell(r_idx, waktu_col_i, str(w_val) if pd.notna(w_val) else ""))
                                        cell_updates.append(gspread.Cell(r_idx, status_col_i, str(s_val) if pd.notna(s_val) else ""))
                                        break

                            if cell_updates:
                                ws.update_cells(cell_updates)
                                st.session_state[changes_key] = False
                                st.cache_data.clear()
                                st.success("✅ Perubahan berhasil disimpan ke Database!")
                                st.rerun()

                        except Exception as e:
                            st.error(f"❌ Gagal menyimpan ke database: {e}")

                with col_btn2:
                    if st.button("🔄 Reset", use_container_width=True, key=f"cancel_{wilayah}"):
                        del st.session_state[local_df_key]
                        st.session_state[changes_key] = False
                        st.rerun()

                st.markdown("---")

            with st.expander("Update Zona Mezzanine", expanded=False):
                daftar_zona_mezzanine = [
                    "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "A11",
                    "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9",
                    "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C11",
                    "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11",
                    "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9",
                    "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9",
                    "SC 1", "SC 2"
                ]

                if not df_lokal.empty:
                    list_id_tersedia = [str(r).split('.')[0].strip() for r in df_lokal[id_col_name].dropna().unique()]

                    with st.form(key=f"form_update_mezzanine_multi_{wilayah}", clear_on_submit=True):
                        selected_ids_mz = st.multiselect("Pilih ID Request:", options=list_id_tersedia)
                        selected_zones = st.multiselect("Pilih Zona Mezzanine:", options=daftar_zona_mezzanine)
                        submit_mz = st.form_submit_button("Simpan Zona Mezzanine", type="primary")

                    if submit_mz:
                        if selected_ids_mz and selected_zones:
                            string_zona_hasil = ", ".join(selected_zones)
                            for target_id in selected_ids_mz:
                                m_idx = df_lokal[df_lokal[id_col_name].astype(str).str.contains(target_id)].index
                                if len(m_idx) > 0:
                                    df_lokal.at[m_idx[0], "Zona Mezzanine"] = string_zona_hasil
                            st.session_state[changes_key] = True
                            st.success(f"✅ Zona Mezzanine berhasil diperbarui!")
                            st.rerun()

            st.markdown("---")
            
            st.markdown(f"##### Data Preload Cabang: {wilayah}")
            
            if not df_lokal.empty:
                df_preload_display = df_lokal.copy()
                
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

                for col in ["Jam Proses Scan", "Tanggal Proses Scan"]:
                    if col in df_preload_display.columns:
                        df_preload_display = df_preload_display.drop(columns=[col])
                
                if "Zona Mezzanine" in df_preload_display.columns and "Waktu Preload" in df_preload_display.columns:
                    cols = list(df_preload_display.columns)
                    cols.remove("Zona Mezzanine")
                    idx_waktu = cols.index("Waktu Preload")
                    cols.insert(idx_waktu + 1, "Zona Mezzanine")
                    df_preload_display = df_preload_display[cols]
                
                st.dataframe(df_preload_display, use_container_width=True, hide_index=True)
            else:
                st.info("Belum ada data preload untuk ditampilkan pada cabang ini.")

        with tab_manifest:
            st.subheader(f" Manifest Pengiriman - {wilayah}")

            id_current_progress = {}
            id_max_box = {}
            
            df_manifest_all_cache = pd.DataFrame()
            try:
                df_manifest_all_cache = conn.read(worksheet="Manifest log", ttl=0)
            except Exception:
                pass

            try:
                if not df_filtered.empty:
                    for _, r_f in df_filtered.iterrows():
                        r_id = str(r_f.get("ID") or r_f.get("id request") or "").split('.')[0].strip()
                        if r_id:
                            try:
                                m_box = int(float(r_f.get("Jumlah Box", 1)))
                            except:
                                m_box = 1
                            try:
                                p_box = int(float(r_f.get("Progress", 0)))
                            except:
                                p_box = 0
                            id_max_box[r_id] = m_box
                            id_current_progress[r_id] = p_box
            except Exception:
                pass

            with st.expander("➕ New Manifest", expanded=False):
                with st.form(key=f"form_buat_manifest_zona_{wilayah}", clear_on_submit=True):
                    
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
                        "Zona Mezzanine:",
                        options=list_zona_tersedia,
                        placeholder="Pilih zona (contoh: A1, B2)..."
                    )
                    
                    submit_manifest = st.form_submit_button("Buat Manifest", type="primary")

                if submit_manifest:
                    if not selected_zones_manifest:
                        st.warning("⚠️ Pilih minimal satu Zona Mezzanine terlebih dahulu.")
                    else:
                        try:
                            matched_ids = []
                            total_box_manifest = 0
                            id_box_added_map = {}

                            for idx, row in df_filtered.iterrows():
                                row_zona = str(row.get("Zona Mezzanine", "")).strip()
                                if any(z.lower() in row_zona.lower() for z in selected_zones_manifest):
                                    r_id = str(row.get("ID") or row.get("id request") or "").split('.')[0].strip()
                                    
                                    if r_id and r_id not in matched_ids:
                                        curr_p = id_current_progress.get(r_id, 0)
                                        box_to_manifest = curr_p if curr_p > 0 else 1 
                                        
                                        if box_to_manifest > 0:
                                            matched_ids.append(r_id)
                                            id_box_added_map[r_id] = box_to_manifest
                                            total_box_manifest += box_to_manifest

                            if not matched_ids:
                                st.warning("⚠️ Tidak ada ID Request atau progress box pada zona mezzanine yang dipilih.")
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
                                    int(total_box_manifest),
                                    dibuat_oleh,
                                    waktu_buat,
                                    status_manifest
                                ])

                                st.success(f"✅ Berhasil membuat Manifest **{nomor_manifest}** dari Zona **{zona_str}** (Total ID: {len(matched_ids)})!")
                                st.session_state[f"sound_effect_{wilayah}"] = "success"
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Gagal membuat manifest: {e}")

            st.markdown("---")
            st.markdown(f"##### Daftar Manifest Cabang: {wilayah}")

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
                    m_tbox = str(row_mnf.get("Jumlah Box", "0")).split('.')[0]
                    m_oleh = str(row_mnf.get("Dibuat Oleh", ""))
                    m_waktu = str(row_mnf.get("Waktu Buat", ""))
                    m_status = str(row_mnf.get("Status Manifest", "Manifested"))

                    c_info, c_btn1, c_btn2 = st.columns([4, 1, 1])
                    with c_info:
                        st.markdown(
                            f"**No. Manifest:** `{m_no}` | **Zona:** {m_zona} | **Jumlah Box:** `{m_tbox}` | "
                            f"**Status:** `{m_status}` | **Oleh:** {m_oleh} ({m_waktu})"
                        )
                    with c_btn1:
                        btn_key = f"detail_mnf_{wilayah}_{m_no}_{index}"
                        if st.button("🔍 Detail", key=btn_key, use_container_width=True):
                            st.session_state[f"active_detail_manifest_{wilayah}"] = m_no
                            
                    with c_btn2:
                        btn_od_key = f"od_mnf_{wilayah}_{m_no}_{index}"
                        if m_status.lower() != "on delivery":
                            
                            if st.button("On Delivery", key=btn_od_key, use_container_width=True, type="primary"):
                                try:
                                    creds_dict = dict(st.secrets["connections"]["gsheets"])
                                    gc = gspread.service_account_from_dict(creds_dict)
                                    spreadsheet_name = st.secrets["connections"]["gsheets"].get("spreadsheet")
                                    sh = gc.open_by_url(spreadsheet_name) if spreadsheet_name.startswith("http") else gc.open(spreadsheet_name)
        
                                    ws_m = sh.worksheet("Manifest log")
                                    ws_main = sh.worksheet("Database log")
        
                                    header_m = ws_m.row_values(1)
                                    status_m_idx = header_m.index("Status Manifest") + 1 if "Status Manifest" in header_m else 8
                                    idlist_m_idx = header_m.index("ID List") + 1 if "ID List" in header_m else 4
                                    mnf_col_idx = header_m.index("Nomor Manifest") + 1 if "Nomor Manifest" in header_m else 1
                                    
                                    manifest_col_values = ws_m.col_values(mnf_col_idx)
                                    row_idx_m = None
                                    ids_to_update = []
        
                                    for idx_m, val_m in enumerate(manifest_col_values, start=1):
                                        if str(val_m).strip() == str(m_no):
                                            row_idx_m = idx_m
                                            row_vals_m = ws_m.row_values(idx_m)
                                            if len(row_vals_m) >= idlist_m_idx:
                                                ids_to_update = [i.strip().split('.')[0] for i in row_vals_m[idlist_m_idx - 1].split(",") if i.strip()]
                                            break
                
                                    if row_idx_m:
                                        
                                        ws_m.update_cell(row_idx_m, status_m_idx, "On Delivery")
                                        
                                        records_main = ws_main.get_all_records()
                                        header_main = ws_main.row_values(1)
                                        id_col_i = header_main.index("ID") + 1 if "ID" in header_main else (header_main.index("id request") + 1 if "id request" in header_main else None)
                                        status_col_i = header_main.index("Status") + 1 if "Status" in header_main else (header_main.index("status") + 1 if "status" in header_main else None)
            
                                        if id_col_i and status_col_i and ids_to_update:
                                            batch_cell_updates = []
                                            for r_i, r_v in enumerate(records_main, start=2):
                                                r_id_str = str(r_v.get("ID") or r_v.get("id request") or "").split('.')[0].strip()
                                                if r_id_str in ids_to_update:
                                                    
                                                    batch_cell_updates.append(gspread.Cell(r_i, status_col_i, "On Delivery"))
                
                                                if batch_cell_updates:
                                                    ws_main.update_cells(batch_cell_updates) 
            
                                        st.success(f"✅ Manifest `{m_no}` berhasil diubah menjadi **On Delivery**!")
                                        
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Gagal merubah status On Delivery: {e}")
                        else:
                            st.markdown("*On Delivery*")

                    st.markdown("---")

                active_mnf = st.session_state.get(f"active_detail_manifest_{wilayah}")
                if active_mnf:
                    selected_row_data = df_manifest_wilayah[df_manifest_wilayah["Nomor Manifest"].astype(str) == str(active_mnf)]
                    
                    if not selected_row_data.empty:
                        st.markdown("---")
                        st.markdown(f"### 🔍 Detail Manifest: `{active_mnf}`")
                        
                        row_info = selected_row_data.iloc[0]
                        current_id_list_str = str(row_info.get("ID List", ""))
                        ids_in_manifest = [i.strip().split('.')[0] for i in current_id_list_str.split(",") if i.strip()]
                        
                        box_tampilkan = str(row_info.get('Jumlah Box', '0')).split('.')[0]
                        st.info(f"**Zona Terliput:** {row_info.get('Zona Mezzanine')} | **Jumlah Box:** {box_tampilkan} | **Waktu Buat:** {row_info.get('Waktu Buat')}")
                        
                        col_scan_in, col_scan_out = st.columns(2)
                        
                        with col_scan_in:
                            with st.form(key=f"form_scan_susulan_{active_mnf}", clear_on_submit=True):
                                st.markdown("##### ➕ Tambah ID baru ke Manifest")
                                scan_input_id = st.text_input("ID Request:", placeholder="Scan/Ketik ID...")
                                added_box_input = st.number_input("Jumlah Box yang Dimasukkan:", min_value=1, value=1, step=1)
                                btn_submit_susulan = st.form_submit_button("Tambah ke Manifest")
                                
                                if btn_submit_susulan:
                                    clean_new_id = scan_input_id.strip().split('.')[0]
                                    if not clean_new_id:
                                        st.warning("⚠️ Masukkan ID yang valid.")
                                    else:
                                        max_b = id_max_box.get(clean_new_id, None)
                                        if max_b is None:
                                            st.error(f"❌ ID `{clean_new_id}` tidak ditemukan pada data preload.")
                                        else:
                                            try:
                                                creds_dict = dict(st.secrets["connections"]["gsheets"])
                                                gc = gspread.service_account_from_dict(creds_dict)
                                                spreadsheet_name = st.secrets["connections"]["gsheets"].get("spreadsheet")
                                                sh = gc.open_by_url(spreadsheet_name) if spreadsheet_name.startswith("http") else gc.open(spreadsheet_name)
                                                
                                                ws_main = sh.worksheet("Database log")
                                                records_main = ws_main.get_all_records()
                                                header_main = ws_main.row_values(1)
                                                
                                                id_col_i = header_main.index("ID") + 1 if "ID" in header_main else (header_main.index("id request") + 1 if "id request" in header_main else None)
                                                prog_col_i = header_main.index("Progress") + 1 if "Progress" in header_main else None
                                                
                                                if id_col_i and prog_col_i:
                                                    for r_idx, r_val in enumerate(records_main, start=2):
                                                        r_id_str = str(r_val.get("ID") or r_val.get("id request") or "").split('.')[0].strip()
                                                        if r_id_str == clean_new_id:
                                                            old_p = int(float(r_val.get("Progress", 0))) if r_val.get("Progress") not in [None, "", "nan"] else 0
                                                            new_p = min(max_b, old_p + int(added_box_input))
                                                            ws_main.update_cell(r_idx, prog_col_i, int(new_p))
                                                            break

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
                                                    if clean_new_id not in ids_in_manifest:
                                                        ids_in_manifest.append(clean_new_id)
                                                    new_id_list_str = ", ".join(ids_in_manifest)
                                                    
                                                    try:
                                                        current_total_box = int(float(row_values[tbox_idx - 1])) if len(row_values) >= tbox_idx and row_values[tbox_idx - 1] != '' else 0
                                                    except:
                                                        current_total_box = 0
                                                    new_total_box = current_total_box + int(added_box_input)
                                                    
                                                    ws_m.update_cell(row_idx, idlist_idx, new_id_list_str)
                                                    ws_m.update_cell(row_idx, tbox_idx, int(new_total_box))
                                                    
                                                    st.success(f"✅ Berhasil menambahkan ID `{clean_new_id}` sebanyak {added_box_input} box ke manifest!")
                                                    st.rerun()
                                                else:
                                                    st.error("❌ Baris manifest tidak ditemukan di Google Sheets.")
                                            except Exception as e:
                                                st.error(f"❌ Gagal memperbarui manifest: {e}")

                        with col_scan_out:
                            with st.form(key=f"form_scan_keluar_{active_mnf}", clear_on_submit=True):
                                st.markdown("##### ➖ Keluarkan ID dari Manifest")
                                scan_out_id = st.text_input("ID Request:", placeholder="Scan/Ketik ID...")
                                removed_box_input = st.number_input("Jumlah Box yang Dikeluarkan:", min_value=1, value=1, step=1)
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
                                            
                                            ws_main = sh.worksheet("Database log")
                                            records_main = ws_main.get_all_records()
                                            header_main = ws_main.row_values(1)
                                            
                                            id_col_i = header_main.index("ID") + 1 if "ID" in header_main else (header_main.index("id request") + 1 if "id request" in header_main else None)
                                            prog_col_i = header_main.index("Progress") + 1 if "Progress" in header_main else None
                                            
                                            sisa_progress = 0
                                            if id_col_i and prog_col_i:
                                                for r_idx, r_val in enumerate(records_main, start=2):
                                                    r_id_str = str(r_val.get("ID") or r_val.get("id request") or "").split('.')[0].strip()
                                                    if r_id_str == clean_out_id:
                                                        old_p = int(float(r_val.get("Progress", 0))) if r_val.get("Progress") not in [None, "", "nan"] else 0
                                                        sisa_progress = max(0, old_p - int(removed_box_input))
                                                        ws_main.update_cell(r_idx, prog_col_i, int(sisa_progress))
                                                        break

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
                                                if sisa_progress == 0:
                                                    if clean_out_id in ids_in_manifest:
                                                       ids_in_manifest.remove(clean_out_id)
                                                
                                                new_id_list_str = ", ".join(ids_in_manifest)
                                                
                                                try:
                                                    current_total_box = int(float(row_values[tbox_idx - 1])) if len(row_values) >= tbox_idx and row_values[tbox_idx - 1] != '' else 0
                                                except:
                                                    current_total_box = 0
                                                
                                                new_total_box = max(0, current_total_box - int(removed_box_input))
                                                
                                                ws_m.update_cell(row_idx, idlist_idx, new_id_list_str)
                                                ws_m.update_cell(row_idx, tbox_idx, int(new_total_box))
                                                
                                                st.success(f"✅ Berhasil mengeluarkan {removed_box_input} box dari ID `{clean_out_id}` di manifest!")
                                                st.rerun()
                                            else:
                                                st.error("❌ Baris manifest tidak ditemukan di Google Sheets.")
                                        except Exception as e:
                                            st.error(f"❌ Gagal mengeluarkan ID: {e}")

                        st.markdown("---")
                        
                        with st.expander("🔗 Gabungkan Beberapa ID Menjadi 1 Box", expanded=False):
                            with st.form(key=f"form_gabung_box_{active_mnf}", clear_on_submit=True):
                                st.markdown("Pilih beberapa ID yang ingin digabungkan box-nya dalam manifest ini:")
                                
                                selected_ids_to_merge = st.multiselect(
                                    "Pilih ID yang ingin digabung:",
                                    options=ids_in_manifest,
                                    placeholder="Pilih ID..."
                                )
                                
                                target_combined_box = st.number_input(
                                    "Total Box Hasil Penggabungan:",
                                    min_value=1,
                                    value=1,
                                    step=1,
                                    help="Masukkan total box akhir untuk ID-ID yang dipilih (misal: digabung jadi 1 box)"
                                )
                                
                                btn_submit_merge = st.form_submit_button("🔄 Buat ID Gabungan", type="primary")
                                
                                if btn_submit_merge:
                                    if not selected_ids_to_merge:
                                        st.warning("⚠️ Pilih minimal satu ID untuk digabungkan.")
                                    else:
                                        try:
                                            creds_dict = dict(st.secrets["connections"]["gsheets"])
                                            gc = gspread.service_account_from_dict(creds_dict)
                                            spreadsheet_name = st.secrets["connections"]["gsheets"].get("spreadsheet")
                                            sh = gc.open_by_url(spreadsheet_name) if spreadsheet_name.startswith("http") else gc.open(spreadsheet_name)
                                            
                                            ws_m = sh.worksheet("Manifest log")
                                            header_m = ws_m.row_values(1)
                                            
                                            mnf_col_idx = header_m.index("Nomor Manifest") + 1 if "Nomor Manifest" in header_m else 1
                                            tbox_idx = header_m.index("Jumlah Box") + 1 if "Jumlah Box" in header_m else 5
                                            
                                            manifest_col_values = ws_m.col_values(mnf_col_idx)
                                            row_idx = None
                                            for idx_m, val_m in enumerate(manifest_col_values, start=1):
                                                if str(val_m).strip() == str(active_mnf):
                                                    row_idx = idx_m
                                                    break
                                            
                                            if row_idx:
                                                row_values = ws_m.row_values(row_idx)
                                                try:
                                                    current_total_box = int(float(row_values[tbox_idx - 1])) if len(row_values) >= tbox_idx and row_values[tbox_idx - 1] != '' else 0
                                                except:
                                                    current_total_box = int(box_tampilkan) if box_tampilkan.isdigit() else 1
                                                
                                                ws_m.update_cell(row_idx, tbox_idx, int(target_combined_box))
                                                
                                                st.success(f"✅ Berhasil menggabungkan ID ({', '.join(selected_ids_to_merge)}) menjadi total **{target_combined_box} box** pada manifest ini!")
                                                st.rerun()
                                            else:
                                                st.error("❌ Baris manifest tidak ditemukan di Google Sheets.")
                                        except Exception as e:
                                            st.error(f"❌ Gagal melakukan penggabungan box: {e}")

                        st.markdown("---")
                        
                        if not df_filtered.empty:
                            col_id_name = "ID" if "ID" in df_filtered.columns else ("id request" if "id request" in df_filtered.columns else None)
                            if col_id_name:
                                df_filtered["clean_id"] = df_filtered[col_id_name].astype(str).str.split('.').str[0].str.strip()
                                df_detail_manifest = df_filtered[df_filtered["clean_id"].isin(ids_in_manifest)].copy()
                                
                                if not df_detail_manifest.empty:
                                    st.markdown("##### List ID Request Manifest :")
                                    
                                    for col_num_check in ["Jumlah Box", "Progress", "clean_id"]:
                                        if col_num_check in df_detail_manifest.columns:
                                            df_detail_manifest[col_num_check] = df_detail_manifest[col_num_check].astype(str).str.split('.').str[0]
                                            
                                    if "clean_id" in df_detail_manifest.columns:
                                        df_detail_manifest = df_detail_manifest.drop(columns=["clean_id"])
                                        
                                    st.dataframe(df_detail_manifest, use_container_width=True, hide_index=True)
                                else:
                                    st.info("ℹ️ ID Terdaftar:")
                                    st.write(ids_in_manifest)
                        
                        if st.button("❌ Tutup Detail", key=f"close_detail_{wilayah}_{active_mnf}"):
                            st.session_state[f"active_detail_manifest_{wilayah}"] = None
                            st.rerun()
            else:
                st.info(f"Belum ada data Manifest yang dibuat untuk cabang {wilayah}.")
