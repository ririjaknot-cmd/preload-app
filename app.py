import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components
import datetime
import gspread
import io
import re
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

def hitung_sisa_box(row):
    try:
        jb = int(float(str(row.get("Jumlah Box") or 0).split('.')[0]))
    except:
        jb = 0
    try:
        pr = int(float(str(row.get("Progress") or 0).split('.')[0]))
    except:
        pr = 0
    return max(0, jb - pr)

def parse_zona_mezzanine(zona_str, total_progress=0):
    """Membaca format tunggal ('A1'), koma ('A1, A2'), maupun rincian ('A1(2 Box), A2(3 Box)')"""
    if not zona_str or str(zona_str).strip().lower() in ["nan", "none", "nat", "", "-"]:
        return {}
    
    zona_str = str(zona_str).strip()
    result = {}
    
    pattern = r'([A-Za-z0-9\s]+?)\s*\(\s*(\d+)(?:\s*[Bb]ox)?\s*\)'
    matches = re.findall(pattern, zona_str)
    
    if matches:
        for z_name, count in matches:
            z_clean = z_name.strip()
            result[z_clean] = result.get(z_clean, 0) + int(count)
    else:
        zones = [z.strip() for z in zona_str.split(",") if z.strip()]
        if zones:
            per_zone_box = max(1, total_progress // len(zones)) if total_progress > 0 else 1
            for z in zones:
                result[z] = result.get(z, 0) + per_zone_box
                
    return result

def format_zona_output(zone_dict):
    valid_zones = {z: b for z, b in zone_dict.items() if b > 0 and z.strip() != ""}
    if not valid_zones:
        return ""
    if len(valid_zones) == 1:
        return list(valid_zones.keys())[0]
    return ", ".join([f"{z}({b} Box)" for z, b in valid_zones.items()])

def tentukan_status_id(current_prog, max_box, status_manifest_saat_ini="", status_saat_ini=""):
    """
    Aturan status ID:
    - Jika sudah 'Delivered' penuh dan kuota terpenuhi -> 'Delivered'
    - Jika progress <= 0 -> 'Pending'
    - Jika progress < max_box:
        - Jika sudah pernah masuk manifest / berstatus 'On Delivery' -> 'On Delivery'
        - Jika masih tahap preload -> 'Not Completed'
    - Jika progress >= max_box (max_box > 0):
        - Jika manifest sudah 'Delivered' -> 'Delivered'
        - Jika manifest masih 'On Delivery' -> 'On Delivery' (menunggu konfirmasi/kelengkapan)
        - Default selesai preload -> 'Completed'
    """
    try:
        p = int(float(str(current_prog or 0).split('.')[0]))
        max_b = int(float(str(max_box or 0).split('.')[0]))
    except:
        p, max_b = 0, 0

    st_curr_lower = str(status_saat_ini).strip().lower()
    st_mnf_lower = str(status_manifest_saat_ini).strip().lower()

    if st_curr_lower == "delivered" and max_b > 0 and p >= max_b:
        return "Delivered"

    if p <= 0:
        return "Pending"

    if max_b > 0 and p < max_b:
        if "on delivery" in st_curr_lower or "on delivery" in st_mnf_lower or "delivered" in st_mnf_lower:
            return "On Delivery"
        return "Not Completed"

    # p >= max_b (atau max_b <= 0)
    if "delivered" in st_mnf_lower:
        return "Delivered"
    elif "on delivery" in st_mnf_lower:
        return "On Delivery"
    else:
        return "Completed"

def format_status_dengan_ikon(progress, jumlah_box, status_manifest=""):
    st_text = tentukan_status_id(progress, jumlah_box, status_manifest)
    if "Delivered" in st_text:
        return "🟢 Delivered"
    elif "On Delivery" in st_text:
        return "🔵 On Delivery"
    elif "Completed" in st_text:
        return "🟢 Completed"
    elif "Not Completed" in st_text:
        return "🟡 Not Completed"
    else:
        return "🔴 Pending"

def generate_manifest_excel(mnf_num, wilayah, creator_name, waktu_buat, df_items):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Manifest {mnf_num}"
    
    ws.views.sheetView[0].showGridLines = True

    font_bold = Font(name="Calibri", size=11, bold=True)
    font_title = Font(name="Calibri", size=12, bold=True)
    font_normal = Font(name="Calibri", size=11, bold=False)
    
    border_thin = Border(
        left=Side(style='thin', color='000000'),
        right=Side(style='thin', color='000000'),
        top=Side(style='thin', color='000000'),
        bottom=Side(style='thin', color='000000')
    )
    
    header_info = [
        ("Pengirim", f"{creator_name}"),
        ("Cabang", f"{wilayah}"),
        ("Tanggal Kirim", f"{waktu_buat}"),
        ("Penerima", "")
    ]
    
    for idx, (label, val) in enumerate(header_info, start=2):
        ws[f'A{idx}'] = label
        ws[f'A{idx}'].font = font_bold
        ws[f'A{idx}'].border = border_thin
        
        ws[f'B{idx}'] = val
        ws[f'B{idx}'].font = font_normal
        ws[f'B{idx}'].border = border_thin
        ws.merge_cells(start_row=idx, start_column=2, end_row=idx, end_column=3)
    
    headers = ["No", "ID REQUEST", "JUMLAH BOX TERKIRIM", "JUMLAH BOX DITERIMA"]
    ws.row_dimensions[7].height = 25
    
    for col_idx, h_text in enumerate(headers, start=1):
        cell = ws.cell(row=7, column=col_idx, value=h_text)
        cell.font = font_title
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border_thin
        
    current_row = 8
    total_box = 0
    
    for i, row_item in enumerate(df_items.iterrows(), start=1):
        _, data = row_item
        r_id = str(data.get("ID") or data.get("id request") or data.get("clean_id") or "").split('.')[0].strip()
        try:
            box_qty = int(float(data.get("Jumlah Box") or data.get("Progress") or 1))
        except:
            box_qty = 1
            
        total_box += box_qty
        
        ws.row_dimensions[current_row].height = 20
        
        c_no = ws.cell(row=current_row, column=1, value=i)
        c_no.alignment = Alignment(horizontal="center", vertical="center")
        c_no.font = font_normal
        c_no.border = border_thin
        
        c_id = ws.cell(row=current_row, column=2, value=r_id)
        c_id.alignment = Alignment(horizontal="center", vertical="center")
        c_id.font = font_normal
        c_id.border = border_thin
        
        c_box = ws.cell(row=current_row, column=3, value=box_qty)
        c_box.alignment = Alignment(horizontal="center", vertical="center")
        c_box.font = font_normal
        c_box.border = border_thin
        
        c_terima = ws.cell(row=current_row, column=4, value="")
        c_terima.alignment = Alignment(horizontal="center", vertical="center")
        c_terima.border = border_thin
        
        current_row += 1
        
    ws.row_dimensions[current_row].height = 22
    ws.cell(row=current_row, column=1, value="").border = border_thin
    
    c_tot_label = ws.cell(row=current_row, column=2, value="TOTAL")
    c_tot_label.font = font_title
    c_tot_label.alignment = Alignment(horizontal="center", vertical="center")
    c_tot_label.border = border_thin
    
    c_tot_val = ws.cell(row=current_row, column=3, value=total_box)
    c_tot_val.font = font_title
    c_tot_val.alignment = Alignment(horizontal="center", vertical="center")
    c_tot_val.border = border_thin
    
    ws.cell(row=current_row, column=4, value="").border = border_thin
    
    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 25
    ws.column_dimensions['C'].width = 28
    ws.column_dimensions['D'].width = 28
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output

st.set_page_config(page_title="V2 Pre Load", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "user_nama" not in st.session_state:
    st.session_state.user_nama = ""

def tampilkan_halaman_login():
    st.markdown("<h2 style='text-align: center;'>🔐 Login Pre Load</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Silakan masukkan Username terdaftar dan PIN Anda.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("form_login"):
            username_input = st.text_input("Nama Pengguna").strip().lower()
            pin_input = st.text_input("PIN / Password", type="password")
            submit_btn = st.form_submit_button("Masuk (Login)", use_container_width=True)
        
        if submit_btn:
            if not username_input or not pin_input:
                st.warning("⚠️ Masukkan Username dan PIN terlebih dahulu.")
            else:
                try:
                    creds_dict = dict(st.secrets["connections"]["gsheets"])
                    gc = gspread.service_account_from_dict(creds_dict)
                    spreadsheet_name = st.secrets["connections"]["gsheets"].get("spreadsheet")
                    sh = gc.open_by_url(spreadsheet_name) if spreadsheet_name.startswith("http") else gc.open(spreadsheet_name)
                    
                    ws_users = sh.worksheet("Data User")
                    records = ws_users.get_all_records()
                    
                    login_berhasil = False
                    nama_user = ""
                    
                    for row in records:
                        db_user = str(row.get("Username", "")).strip().lower()
                        db_pin = str(row.get("Pin / Password", "")).strip() or str(row.get("Pin", "")).strip() or str(row.get("Password", "")).strip()
                        db_nama = str(row.get("Nama", "")).strip()
                        
                        if db_user == username_input and db_pin == pin_input.strip():
                            login_berhasil = True
                            nama_user = db_nama
                            break
                    
                    if login_berhasil:
                        st.session_state.logged_in = True
                        st.session_state.user_email = username_input
                        st.session_state.user_nama = nama_user
                        st.success(f"Login berhasil! Selamat datang, {st.session_state.user_nama}")
                        st.rerun()
                    else:
                        st.error("❌ Username atau PIN salah.")
                except Exception as e:
                    st.error(f"❌ Gagal memuat data login dari database: {e}")

conn = st.connection("gsheets", type=GSheetsConnection)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.success("Cache dibersihkan, memuat data terbaru...")
    st.rerun()

@st.cache_data(ttl=300, show_spinner="Memuat database...")
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

if not st.session_state.logged_in:
    tampilkan_halaman_login()
else:
    col_head1, col_head2 = st.columns([4, 1])
    with col_head1:
        st.markdown("### Pre Load Shipment Cabang ")
    with col_head2:
        st.markdown(f"""
            <div style="text-align: right; font-family: sans-serif; line-height: 1.4; margin-bottom: 8px;">
                <span style="font-size: 14px; font-weight: bold; color: #FFFFFF;">👨🏻‍💼 {st.session_state.user_nama}</span><br>
            </div>
        """, unsafe_allow_html=True)

        components.html("""
        <div style="font-family: sans-serif; font-size: 12px; color: #A0A0A0; text-align: right; margin-top: -10px;">
            🕑<span id="live-clock">Loading...</span>
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
            const elem = document.getElementById('live-clock');
            if (elem) elem.innerText = timeString;
        }
        setInterval(updateClock, 1000);
        updateClock();
        </script>
        """, height=25)

        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col1:
            with st.popover("Password", use_container_width=True):
                st.markdown("##### 🔐 Ubah Password")
                with st.form(key=f"form_ubah_pin_{st.session_state.user_email}", clear_on_submit=True):
                    old_pin = st.text_input("Password Lama:", type="password")
                    new_pin = st.text_input("Password Baru:", type="password")
                    confirm_pin = st.text_input("Konfirmasi Password Baru:", type="password")
                    
                    btn_save_pin = st.form_submit_button("Simpan", type="primary", use_container_width=True)
                    
                    if btn_save_pin:
                        if not old_pin or not new_pin or not confirm_pin:
                            st.warning("⚠️ Semua kolom harus diisi.")
                        elif new_pin != confirm_pin:
                            st.error("❌ Password baru tidak cocok.")
                        else:
                            try:
                                with st.spinner("⏳ Memperbarui..."):
                                    creds_dict = dict(st.secrets["connections"]["gsheets"])
                                    gc = gspread.service_account_from_dict(creds_dict)
                                    spreadsheet_name = st.secrets["connections"]["gsheets"].get("spreadsheet")
                                    sh = gc.open_by_url(spreadsheet_name) if spreadsheet_name.startswith("http") else gc.open(spreadsheet_name)
                                    
                                    ws_users = sh.worksheet("Data User")
                                    header_users = ws_users.row_values(1)
                                    
                                    user_col_i = header_users.index("Username") + 1 if "Username" in header_users else 1
                                    pin_col_i = header_users.index("Pin / Password") + 1 if "Pin / Password" in header_users else (header_users.index("Pin") + 1 if "Pin" in header_users else 3)
                                    
                                    usernames_list = ws_users.col_values(user_col_i)
                                    pins_list = ws_users.col_values(pin_col_i)
                                    
                                    current_user = str(st.session_state.user_email).strip()
                                    target_row = None
                                    
                                    for idx_u, u_val in enumerate(usernames_list, start=1):
                                        if str(u_val).strip().lower() == current_user:
                                            target_row = idx_u
                                            stored_pin = str(pins_list[idx_u - 1]).strip() if (idx_u - 1) < len(pins_list) else ""
                                            if stored_pin != old_pin.strip():
                                                st.error("❌ Password lama salah!")
                                                target_row = None
                                            break
                                    
                                    if target_row:
                                        ws_users.update_cell(target_row, pin_col_i, new_pin.strip())
                                        st.success("✅ Berhasil! Gunakan password baru saat login.")
                            except Exception as e:
                                st.error(f"❌ Gagal: {e}")

        with btn_col2:
            if st.button("Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user_email = ""
                st.session_state.user_nama = ""
                st.rerun()

    st.divider()

    try:
        df_database = load_cached_database()
    except Exception as e:
        st.error("❌ Gagal terhubung ke database. Detail Error:")
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
                df_filtered = df_filtered[df_filtered["Status"].astype(str).str.strip().str.lower() != "Delivered"]
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
            if not keyword_cari or not str(keyword_cari).strip():
                if "Status" in df_display.columns:
                    df_display = df_display[
                        df_display["Status"].astype(str).str.strip().str.lower() != "delivered"
                    ].copy()
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
                                    st.warning(f"**Status ID {m_id} : On Delivery** (Terkirim sebagian / dalam proses pengiriman).")
                                elif m_status == "delivered":
                                    st.success(f"**Status ID {m_id} : Delivered** (Seluruh box sudah terkirim lengkap).")
                            
                            if not df_display.empty:
                                status_formatted_list = []
                                for _, row in df_preload_display.iterrows():
                                    try:
                                        jb = row.get("Jumlah Box") or 0
                                        pr = row.get("Progress") or 0
                                        raw_st = str(row.get("Status", "")).strip().lower()
                            
                                        st_formatted = format_status_dengan_ikon(pr, jb)
                                        if raw_st == "on delivery":
                                            st_formatted = "🔵 On Delivery"
                                        elif raw_st == "delivered":
                                            st_formatted = "🟢 Delivered"
                                        status_formatted_list.append(st_formatted)
                                    except Exception:
                                        status_formatted_list.append("🔴 Pending")
                            
                                if len(status_formatted_list) == len(df_preload_display):
                                    df_preload_display["Status"] = status_formatted_list
                            
                                for col in ["Jam Proses Scan", "Tanggal Proses Scan"]:
                                    if col in df_preload_display.columns:
                                        df_preload_display = df_preload_display.drop(columns=[col])
                            
                                id_col_tampil = "ID" if "ID" in df_preload_display.columns else "id request"
                                cols_tampil = [
                                    id_col_tampil,
                                    "Tujuan Pengiriman",
                                    "Jumlah Box",
                                    "Progress",
                                    "Sisa Box",
                                    "Zona Mezzanine",
                                    "Loader",
                                    "Waktu Preload",
                                    "Status",
                                ]
                                kolom_tersedia = [c for c in cols_tampil if c in df_preload_display.columns]
                                sisa_kolom = [c for c in df_preload_display.columns if c not in kolom_tersedia]
                            
                                st.dataframe(
                                    df_preload_display[kolom_tersedia + sisa_kolom],
                                    use_container_width=True,
                                    hide_index=True,
                                )
                            else:
                                st.info("Belum ada data preload aktif pada cabang ini.")
        
        with tab_preload:
            st.subheader(f"Proses Preload & Zona Mezzanine - {wilayah}")
        
            local_df_key = f"local_df_preload_{wilayah}"
            changes_key = f"has_unsaved_changes_{wilayah}"
            scanned_ids_key = f"session_scanned_ids_{wilayah}"
            session_boxes_key = f"session_box_added_{wilayah}"
            base_zona_key = f"session_base_zona_{wilayah}"
        
            if scanned_ids_key not in st.session_state:
                st.session_state[scanned_ids_key] = []
            if session_boxes_key not in st.session_state:
                st.session_state[session_boxes_key] = {}
            if base_zona_key not in st.session_state:
                st.session_state[base_zona_key] = {}
        
            if local_df_key not in st.session_state or st.sidebar.button("🔄 Reset Draft", key=f"reset_{wilayah}"):
                df_lokal = df_filtered.copy()
                st.session_state[local_df_key] = df_lokal
                st.session_state[changes_key] = False
                st.session_state[scanned_ids_key] = []
                st.session_state[session_boxes_key] = {}
                st.session_state[base_zona_key] = {}
            else:
                df_lokal = st.session_state[local_df_key]
            
            if not df_lokal.empty and "Status" in df_lokal.columns:
                df_lokal = df_lokal[
                    df_lokal["Status"].astype(str).str.strip().str.lower() != "delivered"
                ].copy()
            
            st.session_state[local_df_key] = df_lokal
            df_lokal = st.session_state[local_df_key]
            id_col_name = 'ID' if 'ID' in df_lokal.columns else 'id request'
        
            for col_teks in ["Status", "Loader", "Waktu Preload", "Zona Mezzanine"]:
                if col_teks in df_lokal.columns:
                    df_lokal[col_teks] = df_lokal[col_teks].astype(str).replace({"nan": "", "None": ""})
            if "Progress" in df_lokal.columns:
                df_lokal["Progress"] = pd.to_numeric(df_lokal["Progress"], errors="coerce").fillna(0)
        
            daftar_zona_mezzanine = [
                "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "A11",
                "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9",
                "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C11",
                "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11",
                "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9",
                "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9",
                "SC 1", "SC 2"
            ]
        
            form_input_key = f"form_input_preload_{wilayah}"
            with st.form(key=form_input_key, clear_on_submit=True):
                col_f1, col_f2 = st.columns([3, 1])
                with col_f1:
                    input_id_val = st.text_input("📷 Scan / Masukkan ID Request:", placeholder="Arahkan scanner atau ketik ID...")
                with col_f2:
                    jumlah_box_val = st.number_input("Jumlah Box:", min_value=1, value=1, step=1)
                
                submit_input = st.form_submit_button("Proses Preload", type="primary", use_container_width=True)
        
            if submit_input:
                target_id = input_id_val.strip().split('.')[0] if input_id_val else ""
                
                import time, random
                current_ts = f"{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
                
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
                
                        st.session_state[local_df_key] = df_lokal
                        
                        row_status = str(row.get("Status", "")).strip().lower()
                        if row_status == "delivered":
                            st.session_state[f"last_msg_{wilayah}"] = ("error", f"❌ ID **{target_id}** sudah berstatus **Delivered**.")
                            st.session_state[f"sound_effect_{wilayah}"] = ("error", current_ts)
                            st.rerun()
                        else:
                            try:
                                max_box = int(float(str(row.get("Jumlah Box", 0))))
                                current_prog = int(float(row.get("Progress", 0))) if pd.notna(row.get("Progress")) else 0
                            except:
                                max_box, current_prog = 0, 0
                            sisa_kuota = max(0, max_box - current_prog)

                            if current_prog >= max_box and max_box > 0 and row_status != "on delivery":
                                st.session_state[f"last_msg_{wilayah}"] = ("error", f"⚠️ ID **{target_id}** sudah selesai diproses.")
                                st.session_state[f"sound_effect_{wilayah}"] = ("error", current_ts)
                                st.rerun()
                            elif sisa_kuota <= 0:
                                st.session_state[f"last_msg_{wilayah}"] = ("error", f"⚠️ ID **{target_id}** sudah mencapai batas kuota ({max_box} box).")
                                st.session_state[f"sound_effect_{wilayah}"] = ("error", current_ts)
                                st.rerun()
                            elif int(jumlah_box_val) > sisa_kuota:
                                st.session_state[f"last_msg_{wilayah}"] = ("error", f"❌ Jumlah box melebihi sisa kuota (Sisa: {sisa_kuota} dari {max_box} box).")
                                st.session_state[f"sound_effect_{wilayah}"] = ("error", current_ts)
                                st.rerun()
                            else:
                                if target_id not in st.session_state[base_zona_key]:
                                    existing_z = str(row.get("Zona Mezzanine", "")).strip()
                                    st.session_state[base_zona_key][target_id] = parse_zona_mezzanine(existing_z, total_progress=current_prog)
                        
                                new_prog = current_prog + int(jumlah_box_val)
                                new_status = tentukan_status_id(new_prog, max_box, row_status)
                                now_str = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
                                
                                df_lokal.at[idx, "Progress"] = new_prog
                                df_lokal.at[idx, "Status"] = new_status
                                df_lokal.at[idx, "Loader"] = str(st.session_state.get("user_nama", "Admin"))
                                df_lokal.at[idx, "Waktu Preload"] = now_str
                                
                                if target_id not in st.session_state[scanned_ids_key]:
                                    st.session_state[scanned_ids_key].append(target_id)
                                
                                st.session_state[session_boxes_key][target_id] = st.session_state[session_boxes_key].get(target_id, 0) + int(jumlah_box_val)
                                
                                st.session_state[changes_key] = True
                                st.session_state[f"last_msg_{wilayah}"] = ("success", f"✅ ID **{target_id}** berhasil ditambahkan (+{int(jumlah_box_val)} Box). Progress: **{new_prog}/{max_box}**")
                                st.session_state[f"sound_effect_{wilayah}"] = ("success", current_ts)
                                st.rerun()
        
            if f"last_msg_{wilayah}" in st.session_state:
                m_type, m_text = st.session_state[f"last_msg_{wilayah}"]
                if m_type == "success":
                    st.success(m_text)
                else:
                    st.error(m_text)
                del st.session_state[f"last_msg_{wilayah}"]
                
            sound_effect_key = f"sound_effect_{wilayah}"
            audio_data = st.session_state.get(sound_effect_key)
            
            if audio_data is not None:
                if isinstance(audio_data, (list, tuple)) and len(audio_data) == 2:
                    sound_type, timestamp_id = audio_data
                    local_audio_path = "assets/Sukses.mp3" if sound_type == "success" else "assets/Gagal.mp3"
                    
                    import base64
                    import streamlit.components.v1 as components
                    try:
                        with open(local_audio_path, "rb") as f:
                            audio_bytes = f.read()
                        audio_base64 = base64.b64encode(audio_bytes).decode()
                        unique_audio_id = f"audio_{timestamp_id}"
                        
                        audio_html = f'''
                            <audio id="{unique_audio_id}" preload="auto">
                                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mpeg">
                            </audio>
                            <script>
                                var audio = document.getElementById("{unique_audio_id}");
                                if (audio) {{
                                    audio.volume = 1.0;
                                    var playPromise = audio.play();
                                    if (playPromise !== undefined) {{
                                        playPromise.catch(function(error) {{
                                            console.log("Autoplay dicegah browser: ", error);
                                        }});
                                    }}
                                }}
                            </script>
                        '''
                        components.html(audio_html, height=0, width=0)
                        
                    except Exception as e:
                        st.error(f"⚠️ Gagal memuat file audio: {e}")
                        
                del st.session_state[sound_effect_key]
        
            st.markdown("---")
            if not df_lokal.empty and st.session_state.get(scanned_ids_key, []):
        
                df_aktif = df_lokal.copy()
                df_aktif["_id_clean"] = df_aktif[id_col_name].astype(str).str.split('.').str[0].str.strip()
                df_aktif = df_aktif[df_aktif["_id_clean"].isin(st.session_state[scanned_ids_key])]
        
                if not df_aktif.empty:
                    selected_batch_zona = st.selectbox(
                        "Pilih Zona Mezzanine untuk ID di List Ini:",
                        options=["-- Pilih Zona --"] + daftar_zona_mezzanine,
                        key=f"batch_zona_select_{wilayah}"
                    )
        
                    session_box_dict = st.session_state.get(session_boxes_key, {})
                    base_zona_dict = st.session_state.get(base_zona_key, {})
                    
                    # 1. Gabungkan zona lama (base_zona_dict) dengan zona & box baru di sesi ini
                    if selected_batch_zona != "-- Pilih Zona --":
                        for idx_l, r_l in df_lokal.iterrows():
                            r_id_check = str(r_l.get(id_col_name)).split('.')[0].strip()
                            if r_id_check in st.session_state[scanned_ids_key]:
                                # Salin rincian zona lama sebelum sesi ini
                                merged_map = dict(base_zona_dict.get(r_id_check, {}))
                                added_boxes = session_box_dict.get(r_id_check, 0)
                                
                                # Tambahkan box sesi ini ke zona yang baru dipilih
                                merged_map[selected_batch_zona] = merged_map.get(selected_batch_zona, 0) + added_boxes
                                
                                # Format hasil (1 zona -> 'A1', >1 zona -> 'A1(2 Box), A2(3 Box)')
                                df_lokal.at[idx_l, "Zona Mezzanine"] = format_zona_output(merged_map)
        
                    # 2. Hitung ringkasan hanya dari box yang baru di-input pada sesi ini
                    zona_box_counts = {}
                    for c_id_str in st.session_state[scanned_ids_key]:
                        b_count = session_box_dict.get(c_id_str, 0)
                        if selected_batch_zona != "-- Pilih Zona --" and b_count > 0:
                            zona_box_counts[selected_batch_zona] = zona_box_counts.get(selected_batch_zona, 0) + b_count
        
                    summary_zona_html = ""
                    if zona_box_counts:
                        summary_items = [f"• <b>({z_name}) {int(total_b)} Box</b>" for z_name, total_b in sorted(zona_box_counts.items())]
                        summary_zona_html = "<br>".join(summary_items)
                    else:
                        summary_zona_html = "<i>Belum ada zona mezzanine yang dipilih.</i>"
        
                    st.markdown(
                        f"""
                        <div style='background-color: #1e1e2e; padding: 10px 14px; border-radius: 8px; border: 1px solid #313244; margin-bottom: 12px; font-size: 14px;'>
                            <b>Jumlah Box (Sesi Ini):</b><br>{summary_zona_html}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        
                    ids_to_remove = None
                    
                    # Refresh df_aktif setelah update zona di df_lokal
                    df_aktif_updated = df_lokal[df_lokal[id_col_name].astype(str).str.split('.').str[0].str.strip().isin(st.session_state[scanned_ids_key])]
                    
                    for idx_row, row_item in df_aktif_updated.iterrows():
                        current_id_str = str(row_item[id_col_name]).split('.')[0].strip()
                        current_prog = int(float(str(row_item.get("Progress", 0)).split('.')[0]))
                        max_b = int(float(str(row_item.get("Jumlah Box", 0)).split('.')[0]))
                        z_display = str(row_item.get("Zona Mezzanine", "")).strip()
        
                        cols_row = st.columns([2, 2, 3, 1])
                        with cols_row[0]:
                            st.markdown(f"**ID:** `{current_id_str}`")
                        with cols_row[1]:
                            st.markdown(f"Box: **{current_prog}/{max_b}**")
                        with cols_row[2]:
                            st.markdown(f"Zona: `{z_display if z_display else '-'}`")
                        with cols_row[3]:
                            if st.button("🗑️ Hapus", key=f"del_scan_{wilayah}_{current_id_str}", use_container_width=True):
                                ids_to_remove = current_id_str
        
                    if ids_to_remove:
                        if ids_to_remove in st.session_state[scanned_ids_key]:
                            st.session_state[scanned_ids_key].remove(ids_to_remove)
                        
                        removed_boxes = st.session_state[session_boxes_key].pop(ids_to_remove, 0)
                        orig_z_map = st.session_state[base_zona_key].pop(ids_to_remove, {})
                        
                        for idx_r, r_it in df_lokal.iterrows():
                            r_id_chk = str(r_it.get(id_col_name)).split('.')[0].strip()
                            if r_id_chk == ids_to_remove:
                                restored_prog = max(0, int(float(str(r_it.get("Progress", 0)).split('.')[0])) - removed_boxes)
                                df_lokal.at[idx_r, "Progress"] = restored_prog
                                if restored_prog == 0:
                                    df_lokal.at[idx_r, "Status"] = "Pending"
                                elif restored_prog < int(float(str(r_it.get("Jumlah Box", 0)).split('.')[0])):
                                    df_lokal.at[idx_r, "Status"] = "Not Completed"
                                
                                # Kembalikan zona ke kondisi awal sebelum sesi ini
                                df_lokal.at[idx_r, "Zona Mezzanine"] = format_zona_output(orig_z_map)
                                break
                        
                        st.toast(f"🗑️ ID {ids_to_remove} berhasil dibatalkan dari sesi ini.", icon="ℹ️")
                        st.rerun()
        
                    st.markdown("")
                    
                    if st.button("💾 Simpan Perubahan & Zona ke Database", type="primary", use_container_width=True, key=f"btn_save_batch_mz_{wilayah}"):
                        if selected_batch_zona == "-- Pilih Zona --":
                            st.warning("⚠️ Harap tentukan **Zona Mezzanine** terlebih dahulu sebelum menyimpan!")
                        else:
                            try:
                                with st.spinner("⏳ Menyimpan data preload & zona ke database..."):
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
                                    zona_col_i = header_main.index("Zona Mezzanine") + 1 if "Zona Mezzanine" in header_main else 9
                                    status_col_i = header_main.index("Status") + 1 if "Status" in header_main else 10
        
                                    cell_updates = []
                                    for _, row in df_lokal.iterrows():
                                        r_id = str(row.get("ID") or row.get("id request") or "").split('.')[0].strip()
                                        p_val = row.get("Progress")
                                        l_val = row.get("Loader")
                                        w_val = row.get("Waktu Preload")
                                        z_val = row.get("Zona Mezzanine")
                                        s_val = row.get("Status")
        
                                        if r_id in st.session_state[scanned_ids_key]:
                                            for r_idx, r_val in enumerate(records_main, start=2):
                                                sheet_id_str = str(r_val.get("ID") or r_val.get("id request") or "").split('.')[0].strip()
                                                if sheet_id_str == r_id:
                                                    cell_updates.append(gspread.Cell(r_idx, prog_col_i, int(float(str(p_val).split('.')[0])) if pd.notna(p_val) else 0))
                                                    cell_updates.append(gspread.Cell(r_idx, loader_col_i, str(l_val)))
                                                    cell_updates.append(gspread.Cell(r_idx, waktu_col_i, str(w_val)))
                                                    cell_updates.append(gspread.Cell(r_idx, zona_col_i, str(z_val)))
                                                    cell_updates.append(gspread.Cell(r_idx, status_col_i, str(s_val)))
                                                    break
        
                                    if cell_updates:
                                        ws.update_cells(cell_updates)
                                        
                                        st.session_state[scanned_ids_key] = []
                                        st.session_state[session_boxes_key] = {}
                                        st.session_state[base_zona_key] = {}
                                        st.session_state[changes_key] = False
                                        if local_df_key in st.session_state:
                                            del st.session_state[local_df_key]
                                            
                                        st.cache_data.clear()
                                        st.success("✅ Seluruh data preload dan zona mezzanine berhasil disimpan ke database!")
                                        st.rerun()
        
                            except Exception as e:
                                st.error(f"❌ Gagal menyimpan ke database: {e}")
        
            st.markdown("---")
            st.markdown(f"##### Data Preload Cabang: {wilayah}")
            if not df_lokal.empty:
                df_preload_display = df_lokal.copy()
                def _hitung_sisa(r):
                    try:
                        jb = int(float(str(r.get("Jumlah Box") or 0).split('.')[0]))
                    except:
                        jb = 0
                    try:
                        pr = int(float(str(r.get("Progress") or 0).split('.')[0]))
                    except:
                        pr = 0
                    return max(0, jb - pr)
            
                df_preload_display["Sisa Box"] = df_preload_display.apply(_hitung_sisa, axis=1)
                
                zona_sisa_map = {}
                for _, r in df_preload_display.iterrows():
                    st_row = str(r.get("Status", "")).strip().lower()
                    if st_row == "delivered":
                        continue
            
                    sisa_b = int(r.get("Sisa Box") or 0)
                    if sisa_b > 0:
                        z_text = str(r.get("Zona Mezzanine", "")).strip()
                        zona_list = [part.split("(")[0].strip() for part in z_text.split(",") if part.strip()]
                        if zona_list:
                            if len(zona_list) == 1:
                                z_name = zona_list[0]
                                zona_sisa_map[z_name] = zona_sisa_map.get(z_name, 0) + sisa_b
                            else:
                                for idx_z, z_name in enumerate(zona_list):
                                    tambahan = sisa_b // len(zona_list) + (1 if idx_z < (sisa_b % len(zona_list)) else 0)
                                    if tambahan > 0:
                                        zona_sisa_map[z_name] = zona_sisa_map.get(z_name, 0) + tambahan
            
                if zona_sisa_map:
                    summary_items = [f"({z}) {cnt} Box" for z, cnt in sorted(zona_sisa_map.items())]
                    st.info(f"**Summary Zona & Total Box Cabang:** • {' • '.join(summary_items)}")
                else:
                    st.info("**Summary Zona & Total Box Cabang:** • Tidak ada sisa box aktif")
                # Hitung Summary Zona Cabang menggunakan parser universal (aman untuk format tunggal & multi-zona)
                branch_zona_counts = {}
                for _, r_item in df_preload_display.iterrows():
                    z_val = str(r_item.get("Zona Mezzanine", "")).strip()
                    if z_val and z_val.lower() not in ["nan", "none", "nat", ""]:
                        try:
                            b_val = int(float(str(r_item.get("Progress", 0) or 0).split('.')[0]))
                        except:
                            b_val = 0
                        
                        parsed_z = parse_zona_mezzanine(z_val, total_progress=b_val)
                        for sz, cnt in parsed_z.items():
                            branch_zona_counts[sz] = branch_zona_counts.get(sz, 0) + cnt
        
                summary_branch_html = ""
                if branch_zona_counts:
                    branch_summary_items = [f"• <b>({z})</b> {cnt} Box" for z, cnt in sorted(branch_zona_counts.items())]
                    summary_branch_html = " | ".join(branch_summary_items)
                else:
                    summary_branch_html = "<i>Belum ada zona mezzanine yang tercatat pada data cabang ini.</i>"
        
                st.markdown(
                    f"""
                    <div style='background-color: #1e1e2e; padding: 8px 12px; border-radius: 6px; border: 1px solid #313244; margin-bottom: 10px; font-size: 13px; color: #fff;'>
                        <b>Summary Zona & Total Box Cabang:</b> {summary_branch_html}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
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
            
                cols_tampil = [
                    "ID" if "ID" in df_preload_display.columns else "id request", 
                    "Tujuan Pengiriman", 
                    "Jumlah Box", 
                    "Progress",
                    "Sisa Box",
                    "Zona Mezzanine", 
                    "Loader", 
                    "Waktu Preload", 
                    "Status"
                ]
                kolom_tersedia = [c for c in cols_tampil if c in df_preload_display.columns]
                sisa_kolom = [c for c in df_preload_display.columns if c not in kolom_tersedia]
            
                st.dataframe(
                    df_preload_display[kolom_tersedia + sisa_kolom],
                    use_container_width=True,
                    hide_index=True,
                )
                df_editor_clean = df_preload_display.drop(columns=["Sisa Box"], errors="ignore").copy()
                # Menggunakan TextColumn agar format gabungan seperti "A1(2 Box), A2(3 Box)" bisa tampil & diedit dengan bebas
                edited_preload_df = st.data_editor(
                    df_editor_clean,
                    column_config={
                        "Zona Mezzanine": st.column_config.TextColumn(
                            "Zona Mezzanine",
                            help="Contoh format: A1 atau A1(2 Box), A2(3 Box)",
                            required=False,
                        ),
                    },
                    disabled=[c for c in cols_tersedia if c != "Zona Mezzanine"],
                    use_container_width=True,
                    hide_index=True,
                    key=f"editor_preload_{wilayah}"
                )
                
                def normalize_zone(val):
                    if val is None:
                        return ""
                    s = str(val).strip()
                    return "" if s.lower() in ["nan", "none", "nat", ""] else s
                
                orig_zone_map = {
                    str(r[id_col_key]).split('.')[0].strip(): normalize_zone(r.get("Zona Mezzanine", ""))
                    for _, r in df_editor_clean.iterrows()
                }
                
                has_zone_changes = False
                for _, row_edited in edited_preload_df.iterrows():
                    curr_id = str(row_edited.get(id_col_key, "")).split('.')[0].strip()
                    ed_zona = normalize_zone(row_edited.get("Zona Mezzanine", ""))
                    orig_zona = orig_zone_map.get(curr_id, "")
                    
                    if orig_zona != ed_zona:
                        has_zone_changes = True
                        break
                
                if has_zone_changes:
                    if st.button("💾 Simpan Perubahan", type="primary", key=f"btn_save_preload_zona_{wilayah}"):
                        try:
                            with st.spinner("⏳ Menyimpan perubahan ke database..."):
                                creds_dict = dict(st.secrets["connections"]["gsheets"])
                                gc = gspread.service_account_from_dict(creds_dict)
                                spreadsheet_name = st.secrets["connections"]["gsheets"].get("spreadsheet")
                                sh = gc.open_by_url(spreadsheet_name) if spreadsheet_name.startswith("http") else gc.open(spreadsheet_name)
                                ws = sh.worksheet("Database log")
            
                                records_main = ws.get_all_records()
                                header_main = ws.row_values(1)
            
                                zona_col_i = header_main.index("Zona Mezzanine") + 1 if "Zona Mezzanine" in header_main else 9
            
                                cell_updates = []
                                for _, row_edited in edited_preload_df.iterrows():
                                    e_id = str(row_edited.get(id_col_key, "")).split('.')[0].strip()
                                    e_zona = normalize_zone(row_edited.get("Zona Mezzanine", ""))
            
                                    for r_idx, r_val in enumerate(records_main, start=2):
                                        sheet_id_str = str(r_val.get("ID") or r_val.get("id request") or "").split('.')[0].strip()
                                        if sheet_id_str == e_id:
                                            old_zona = normalize_zone(r_val.get("Zona Mezzanine", ""))
                                                
                                            if old_zona != e_zona:
                                                cell_updates.append(gspread.Cell(r_idx, zona_col_i, e_zona))
                                            break
            
                                if cell_updates:
                                    ws.update_cells(cell_updates)
                                    st.session_state[scanned_ids_key] = []
                                    st.session_state[session_boxes_key] = {}
                                    st.session_state[base_zona_key] = {}
                                    st.session_state[changes_key] = False
                                    if local_df_key in st.session_state:
                                        del st.session_state[local_df_key]
                                            
                                    st.cache_data.clear()
                                    st.success("✅ Seluruh data preload dan zona mezzanine berhasil disimpan ke database!")
                                    st.rerun()
            
                        except Exception as e:
                            st.error(f"❌ Gagal menyimpan zona: {e}")
            else:
                st.info("Belum ada data preload untuk ditampilkan pada cabang ini.")

        with tab_manifest:
            st.subheader(f" Manifest Pengiriman - {wilayah}")
        
            id_current_progress = {}
            id_max_box = {}
            
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
                        for _, r_z in df_filtered.iterrows():
                            z_str = str(r_z.get("Zona Mezzanine", "")).strip()
                            if z_str and z_str.lower() not in ["none", "", "nan"]:
                                parsed_z_map = parse_zona_mezzanine(z_str)
                                for clean_z in parsed_z_map.keys():
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
                                if str(row.get("Status", "")).strip().lower() == "delivered":
                                    continue
                                row_zona = str(row.get("Zona Mezzanine", "")).strip()
                                r_id = str(row.get("ID") or row.get("id request") or "").split('.')[0].strip()
                                curr_p = id_current_progress.get(r_id, 0)
                                
                                parsed_row_zones = parse_zona_mezzanine(row_zona, total_progress=curr_p)
                                box_in_selected_zones = 0
                                for sel_z in selected_zones_manifest:
                                    for p_z, p_cnt in parsed_row_zones.items():
                                        if sel_z.strip().lower() == p_z.strip().lower():
                                            box_in_selected_zones += p_cnt
        
                                if box_in_selected_zones > 0 and r_id and r_id not in matched_ids:
                                    matched_ids.append(r_id)
                                    id_box_added_map[r_id] = box_in_selected_zones
                                    total_box_manifest += box_in_selected_zones
        
                            if not matched_ids:
                                st.warning("⚠️ Tidak ada ID Request atau progress box pada zona mezzanine yang dipilih.")
                            else:
                                now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
                                nomor_manifest = f"MNF-{now.strftime('%Y%m%d-%H%M%S')}"
                                
                                creds_dict = dict(st.secrets["connections"]["gsheets"])
                                gc = gspread.service_account_from_dict(creds_dict)
                                spreadsheet_name = st.secrets["connections"]["gsheets"].get("spreadsheet")
                                sh = gc.open_by_url(spreadsheet_name) if spreadsheet_name.startswith("http") else gc.open(spreadsheet_name)
                                
                                ws_manifest = sh.worksheet("Manifest log")
                                ws_main = sh.worksheet("Database log")
        
                                dibuat_oleh = str(st.session_state.user_nama)
                                waktu_buat = now.strftime("%Y-%m-%d %H:%M:%S")
                                status_manifest = "On Delivery" # Status awal manifest baru dibuat
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
        
                                # Perbarui status ID terkait di Database log menjadi 'On Delivery'
                                records_main = ws_main.get_all_records()
                                header_main = ws_main.row_values(1)
                                id_col_i = header_main.index("ID") + 1 if "ID" in header_main else header_main.index("id request") + 1
                                status_col_i = header_main.index("Status") + 1 if "Status" in header_main else header_main.index("status") + 1
                                prog_col_i = header_main.index("Progress") + 1 if "Progress" in header_main else 6
                                box_col_i = header_main.index("Jumlah Box") + 1 if "Jumlah Box" in header_main else 3
        
                                batch_updates = []
                                for r_idx, r_val in enumerate(records_main, start=2):
                                    r_id_str = str(r_val.get("ID") or r_val.get("id request") or "").split('.')[0].strip()
                                    if r_id_str in matched_ids:
                                        p_val = r_val.get("Progress", 0)
                                        m_val = r_val.get("Jumlah Box", 0)
                                        
                                        # Cek apakah sudah delivered penuh atau masih on delivery
                                        final_st = tentukan_status_id(p_val, m_val, status_manifest_saat_ini="On Delivery")
                                        batch_updates.append(gspread.Cell(r_idx, status_col_i, final_st))
        
                                if batch_updates:
                                    ws_main.update_cells(batch_updates)
        
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
        
            if df_manifest_wilayah.empty:
                st.info(f"Belum ada data Manifest yang dibuat untuk cabang {wilayah}.")
            else:
                for idx, m_row in df_manifest_wilayah.iterrows():
                    mnf_num = str(m_row.get("Nomor Manifest", ""))
                    zona_raw = str(m_row.get("Zona Mezzanine", ""))
                    box_total = str(m_row.get("Jumlah Box", "0")).split('.')[0]
                    m_status = str(m_row.get("Status Manifest", "") or m_row.get("Status", "Manifested"))

                    m_creator = str(
                        m_row.get("Dibuat Oleh") or  
                        "-"
                    )
                    if m_creator.lower() in ["nan", "none", ""]:
                        m_creator = "-"
                
                    m_time = str(m_row.get("Waktu Buat", "") or m_row.get("Timestamp", ""))

                    list_zona_split = [z.strip() for z in zona_raw.split(",") if z.strip()]
                    manifest_id_list = [i.strip().split('.')[0] for i in str(m_row.get("ID List", "")).split(",") if i.strip()]
                    
                    # 3. Tooltip rincian zona akurat menggunakan parser
                    tooltip_lines = []
                    if list_zona_split and not df_filtered.empty:
                        col_id_name = "ID" if "ID" in df_filtered.columns else ("id request" if "id request" in df_filtered.columns else None)
                        
                        if col_id_name:
                            df_temp = df_filtered.copy()
                            df_temp["clean_id"] = df_temp[col_id_name].astype(str).str.split('.').str[0].str.strip()
                            df_mnf_items = df_temp[df_temp["clean_id"].isin(manifest_id_list)]
                            
                            for z in list_zona_split:
                                box_count = 0
                                for _, row_item in df_mnf_items.iterrows():
                                    val_p = row_item.get("Progress") or row_item.get("Jumlah Box") or 1
                                    try:
                                        p_int = int(float(str(val_p).split('.')[0]))
                                    except:
                                        p_int = 1
                                    
                                    parsed_item_z = parse_zona_mezzanine(str(row_item.get("Zona Mezzanine", "")), total_progress=p_int)
                                    for pz_name, pz_qty in parsed_item_z.items():
                                        if z.strip().lower() == pz_name.strip().lower():
                                            box_count += pz_qty
                                    
                                tooltip_lines.append(f"<div style='padding: 2px 0;'>• <b>({z})</b> {box_count} Box</div>")
                            
                            tooltip_items_html = "".join(tooltip_lines)
                        else:
                            tooltip_items_html = "".join([f"<div style='padding: 2px 0;'>• <b>({z})</b> 1 Box</div>" for z in list_zona_split])
                    else:
                        tooltip_items_html = "".join([f"<div style='padding: 2px 0;'>• <b>({z})</b> 1 Box</div>" for z in list_zona_split]) if list_zona_split else "<div>Tidak ada zona</div>"
                
                    clean_css_id = re.sub(r'[^a-zA-Z0-9_-]', '_', str(mnf_num)) if mnf_num else str(idx)
                    
                    manifest_info_html = f"""
                    <style>
                    .tooltip-container-{clean_css_id} {{
                      position: relative;
                      display: inline-block;
                      cursor: pointer;
                      color: #ff4b4b;
                      font-weight: bold;
                    }}
                    .tooltip-container-{clean_css_id} .tooltip-text {{
                      visibility: hidden;
                      width: 150px;
                      background-color: #262730;
                      color: #fff;
                      text-align: left;
                      border-radius: 6px;
                      padding: 8px 10px;
                      position: absolute;
                      z-index: 1000;
                      bottom: 135%;
                      left: 50%;
                      transform: translateX(-50%);
                      opacity: 0;
                      transition: opacity 0.3s;
                      font-size: 13px;
                      box-shadow: 0px 4px 12px rgba(0,0,0,0.4);
                      border: 1px solid #46485f;
                    }}
                    .tooltip-container-{clean_css_id}:hover .tooltip-text {{
                      visibility: visible;
                      opacity: 1;
                    }}
                    </style>
                
                    <div style="font-size: 14px; color: #fafafa; line-height: 1.6;">
                      <div>
                        <b>No. Manifest:</b> <code>{mnf_num}</code> &nbsp;|&nbsp; 
                        <div class="tooltip-container-{clean_css_id}">
                          Zona
                          <div class="tooltip-text">
                            {tooltip_items_html}
                          </div>
                        </div> 
                        &nbsp;|&nbsp; <b>Jumlah Box:</b> {box_total}
                      </div>
                      <div style="color: #b0b0b0; font-size: 13px;">
                        <b>Status:</b> <span style="background-color: #262730; padding: 2px 6px; border-radius: 4px; border: 1px solid #46485f; color: #fff;">{m_status}</span> 
                        &nbsp;|&nbsp; <b>Oleh:</b> {m_creator} ({m_time})
                      </div>
                    </div>
                    """
              
                    col_info, col_action = st.columns([2.6, 1.4])
                    
                    with col_info:
                        st.markdown(manifest_info_html, unsafe_allow_html=True)
                    
                    with col_action:
                        c_btn1, c_btn2, c_btn3 = st.columns([2, 2, 1])
                        
                        with c_btn1:
                            btn_key = f"detail_mnf_{wilayah}_{mnf_num}_{idx}"
                            if st.button("🔍 Detail", key=btn_key, use_container_width=True):
                                st.session_state[f"active_detail_manifest_{wilayah}"] = mnf_num
                                st.rerun()
                                
                        with c_btn2:
                            btn_od_key = f"od_mnf_{wilayah}_{mnf_num}_{idx}"
                            # Tombol ubah status menjadi Delivered penuh jika pengiriman selesai
                            if m_status.lower() != "delivered":
                                btn_label = "Delivered" if m_status.lower() == "on delivery" else "Set Delivered"
                                if st.button(btn_label, key=btn_od_key, use_container_width=True, type="primary"):
                                    try:
                                        creds_dict = dict(st.secrets["connections"]["gsheets"])
                                        gc = gspread.service_account_from_dict(creds_dict)
                                        spreadsheet_name = st.secrets["connections"]["gsheets"].get("spreadsheet")
                                        sh = gc.open_by_url(spreadsheet_name) if spreadsheet_name.startswith("http") else gc.open(spreadsheet_name)
                                        
                                        ws_m = sh.worksheet("Manifest log")
                                        ws_main = sh.worksheet("Database log")
                                        
                                        header_m = ws_m.row_values(1)
                                        status_m_idx = header_m.index("Status Manifest") + 1 if "Status Manifest" in header_m else 8
                                        mnf_col_idx = header_m.index("Nomor Manifest") + 1 if "Nomor Manifest" in header_m else 1
                                        
                                        manifest_col_values = ws_m.col_values(mnf_col_idx)
                                        row_idx_m = None
                                        for idx_m, val_m in enumerate(manifest_col_values, start=1):
                                            if str(val_m).strip() == str(mnf_num):
                                                row_idx_m = idx_m
                                                break
                                        
                                        if row_idx_m:
                                            ws_m.update_cell(row_idx_m, status_m_idx, "Delivered")
                                            
                                            records_main = ws_main.get_all_records()
                                            header_main = ws_main.row_values(1)
                                            status_col_i = header_main.index("Status") + 1 if "Status" in header_main else 10
                                            box_col_i = header_main.index("Jumlah Box") + 1 if "Jumlah Box" in header_main else None
                                            prog_col_i = header_main.index("Progress") + 1 if "Progress" in header_main else None
                                            
                                            batch_cell_updates = []
                                            for r_i, r_v in enumerate(records_main, start=2):
                                                r_id_str = str(r_v.get("ID") or r_v.get("id request") or "").split('.')[0].strip()
                                                if r_id_str in manifest_id_list:
                                                    try:
                                                        p_val = int(float(str(r_v.get("Progress") or 0).split('.')[0]))
                                                    except:
                                                        p_val = 0
                                                    try:
                                                        m_val = int(float(str(r_v.get("Jumlah Box") or 0).split('.')[0]))
                                                    except:
                                                        m_val = 0
                                                    
                                                    if m_val > 0 and 0 < p_val < m_val:
    
                                                        batch_cell_updates.append(gspread.Cell(r_i, status_col_i, "On Delivery"))
                                                        
                                                    else:
                                                        # Sudah lengkap / penuh
                                                        batch_cell_updates.append(gspread.Cell(r_i, status_col_i, "Delivered"))
                                            
                                            if batch_cell_updates:
                                                ws_main.update_cells(batch_cell_updates)
                                            
                                            st.cache_data.clear()
                                            for k in list(st.session_state.keys()):
                                                if "local_df_preload" in k or "has_unsaved_changes" in k:
                                                    del st.session_state[k]
                                            
                                            st.success(f"✅ Manifest `{mnf_num}` diproses! ID lengkap menjadi **Delivered**, ID parsial tetap **On Delivery**.")
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Gagal merubah status Delivered: {e}")
                            else:
                                st.markdown("*Delivered*")
                
                        with c_btn3:
                            btn_del_key = f"del_mnf_{wilayah}_{mnf_num}_{idx}"
                            if st.button("🗑️", key=btn_del_key, help=f"Hapus Manifest {mnf_num} ", use_container_width=True):
                                try:
                                    with st.spinner(f"⏳ Menghapus manifest {mnf_num} "):
                                        creds_dict = dict(st.secrets["connections"]["gsheets"])
                                        gc = gspread.service_account_from_dict(creds_dict)
                                        spreadsheet_name = st.secrets["connections"]["gsheets"].get("spreadsheet")
                                        sh = gc.open_by_url(spreadsheet_name) if spreadsheet_name.startswith("http") else gc.open(spreadsheet_name)
                                        
                                        ws_m = sh.worksheet("Manifest log")
                                        ws_main = sh.worksheet("Database log")
                                        
                                        header_m = ws_m.row_values(1)
                                        mnf_col_idx = header_m.index("Nomor Manifest") + 1 if "Nomor Manifest" in header_m else 1
                                        idlist_m_idx = header_m.index("ID List") + 1 if "ID List" in header_m else 4
                                        
                                        manifest_col_values = ws_m.col_values(mnf_col_idx)
                                        row_idx_m = None
                                        ids_to_restore = []
                                        
                                        for idx_m, val_m in enumerate(manifest_col_values, start=1):
                                            if str(val_m).strip() == str(mnf_num):
                                                row_idx_m = idx_m
                                                row_vals_m = ws_m.row_values(idx_m)
                                                if len(row_vals_m) >= idlist_m_idx:
                                                    ids_to_restore = [i.strip().split('.')[0] for i in row_vals_m[idlist_m_idx - 1].split(",") if i.strip()]
                                                break
                                        
                                        if row_idx_m:
                                            ws_m.delete_rows(row_idx_m)
                                            
                                            records_main = ws_main.get_all_records()
                                            header_main = ws_main.row_values(1)
                                            
                                            status_col_i = header_main.index("Status") + 1 if "Status" in header_main else (header_main.index("status") + 1 if "status" in header_main else 10)
                                            
                                            if ids_to_restore:
                                                batch_restore_updates = []
                                                for r_i, r_v in enumerate(records_main, start=2):
                                                    r_id_str = str(r_v.get("ID") or r_v.get("id request") or "").split('.')[0].strip()
                                                    if r_id_str in ids_to_restore:
                                                        batch_restore_updates.append(gspread.Cell(r_i, status_col_i, "Completed"))
                                                
                                                if batch_restore_updates:
                                                    ws_main.update_cells(batch_restore_updates)
                                            
                                            if st.session_state.get(f"active_detail_manifest_{wilayah}") == mnf_num:
                                                del st.session_state[f"active_detail_manifest_{wilayah}"]
                                                
                                            st.cache_data.clear()
                                            for k in list(st.session_state.keys()):
                                                if "local_df_preload" in k or "has_unsaved_changes" in k:
                                                    del st.session_state[k]
                                                    
                                            st.success(f"✅ Manifest `{mnf_num}` berhasil dihapus dan status **Completed**!")
                                            st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Gagal menghapus manifest: {e}")
                    
                    st.markdown("---")

            active_mnf = st.session_state.get(f"active_detail_manifest_{wilayah}")
            if active_mnf and not df_manifest_wilayah.empty:
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
                                        with st.spinner("⏳ Menambahkan ID ke Manifest & memperbarui data..."):
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
                                                status_col_i = header_main.index("Status") + 1 if "Status" in header_main else (header_main.index("status") + 1 if "status" in header_main else None)
                                                
                                                actual_added = 0
                                                if id_col_i and prog_col_i:
                                                    for r_idx, r_val in enumerate(records_main, start=2):
                                                        r_id_str = str(r_val.get("ID") or r_val.get("id request") or "").split('.')[0].strip()
                                                        if r_id_str == clean_new_id:
                                                            old_p = int(float(r_val.get("Progress", 0))) if r_val.get("Progress") not in [None, "", "nan"] else 0
                                                            new_p = min(max_b, old_p + int(added_box_input))
                                                            actual_added = new_p - old_p
                                                            
                                                            ws_main.update_cell(r_idx, prog_col_i, new_p)
                                                            if status_col_i:
                                                                ws_main.update_cell(r_idx, status_col_i, "Manifested")
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
                                                    
                                                    st.cache_data.clear()
                                                    for k in list(st.session_state.keys()):
                                                        if "local_df_preload" in k or "has_unsaved_changes" in k:
                                                            del st.session_state[k]
                                                            
                                                    st.success(f"✅ Berhasil menambahkan ID `{clean_new_id}` sebanyak {added_box_input} box ke manifest!")
                                                    st.rerun()
                                                else:
                                                    st.error("❌ Baris manifest tidak ditemukan di database.")
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
                                    with st.spinner("⏳ Mengeluarkan ID dari Manifest & memperbarui data..."):
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
                                            status_col_i = header_main.index("Status") + 1 if "Status" in header_main else (header_main.index("status") + 1 if "status" in header_main else None)
                                            
                                            sisa_progress = 0
                                            if id_col_i and prog_col_i:
                                                for r_idx, r_val in enumerate(records_main, start=2):
                                                    r_id_str = str(r_val.get("ID") or r_val.get("id request") or "").split('.')[0].strip()
                                                    if r_id_str == clean_out_id:
                                                        old_p = int(float(r_val.get("Progress", 0))) if r_val.get("Progress") not in [None, "", "nan"] else 0
                                                        sisa_progress = max(0, old_p - int(removed_box_input))
                                                        
                                                        
                                                        ws_main.update_cell(r_idx, prog_col_i, sisa_progress)
                                                        if sisa_progress == 0 and status_col_i:
                                                            ws_main.update_cell(r_idx, status_col_i, "Completed")
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
                                                
                                                st.cache_data.clear()
                                                for k in list(st.session_state.keys()):
                                                    if "local_df_preload" in k or "has_unsaved_changes" in k:
                                                        del st.session_state[k]
                                                        
                                                st.success(f"✅ Berhasil mengeluarkan {removed_box_input} box dari ID `{clean_out_id}` di manifest!")
                                                st.rerun()
                                            else:
                                                st.error("❌ Baris manifest tidak ditemukan di database.")
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
                                    with st.spinner("⏳ Menggabungkan ID & memperbarui data..."):
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
                                                ws_m.update_cell(row_idx, tbox_idx, int(target_combined_box))
                                                
                                                st.cache_data.clear()
                                                for k in list(st.session_state.keys()):
                                                    if "local_df_preload" in k or "has_unsaved_changes" in k:
                                                        del st.session_state[k]
                                                        
                                                st.success(f"✅ Berhasil menggabungkan ID ({', '.join(selected_ids_to_merge)}) menjadi total **{target_combined_box} box** pada manifest ini!")
                                                st.rerun()
                                            else:
                                                st.error("❌ Baris manifest tidak ditemukan di database.")
                                        except Exception as e:
                                            st.error(f"❌ Gagal melakukan penggabungan box: {e}")
                    
                    st.markdown("---")
                    
                    if not df_filtered.empty:
                        col_id_name = "ID" if "ID" in df_filtered.columns else ("id request" if "id request" in df_filtered.columns else None)
                        if col_id_name:
                            df_filtered["clean_id"] = df_filtered[col_id_name].astype(str).str.split('.').str[0].str.strip()
                            df_detail_manifest = df_filtered[df_filtered["clean_id"].isin(ids_in_manifest)].copy()
                            
                            for col_num_check in ["Jumlah Box", "Progress", "clean_id"]:
                                if col_num_check in df_detail_manifest.columns:
                                    df_detail_manifest[col_num_check] = df_detail_manifest[col_num_check].astype(str).str.split('.').str[0]
                                    
                            if "clean_id" in df_detail_manifest.columns:
                                df_detail_manifest = df_detail_manifest.drop(columns=["clean_id"])
                        else:
                            df_detail_manifest = pd.DataFrame()
                    else:
                        df_detail_manifest = pd.DataFrame()
                
                    if not df_detail_manifest.empty:
                        creator_val = row_info.get("Dibuat Oleh") or row_info.get("Oleh") or str(st.session_state.get("user_nama", "Admin"))
                        time_val = row_info.get("Waktu Buat") or row_info.get("Timestamp") or "-"
                        
                        excel_data = generate_manifest_excel(
                            mnf_num=active_mnf,
                            wilayah=wilayah,
                            creator_name=creator_val,
                            waktu_buat=time_val,
                            df_items=df_detail_manifest
                        )
                        
                        st.download_button(
                            label="📥Download Xls",
                            data=excel_data,
                            file_name=f"{active_mnf}_{wilayah}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # Diperbaiki dari chssheet
                            key=f"dl_excel_{active_mnf}",
                            use_container_width=True
                        )
                
                    st.markdown("##### List ID Request Manifest :")
                    if not df_detail_manifest.empty:
                        st.dataframe(df_detail_manifest, use_container_width=True, hide_index=True)
                    else:
                        st.info("ℹ️ ID Terdaftar:")
                        st.write(ids_in_manifest)
                
                    if st.button("❌ Tutup Detail", key=f"close_detail_{wilayah}_{active_mnf}"):
                        st.session_state[f"active_detail_manifest_{wilayah}"] = None
                        st.rerun()
