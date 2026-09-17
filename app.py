import streamlit as st

# Konfigurasi halaman agar menggunakan mode 'wide' (lebar) ala dashboard
st.set_page_config(page_title="V2 New Pre Load 2026", layout="wide")

# --- HEADER ---
col_head1, col_head2 = st.columns([4, 1])
with col_head1:
    st.markdown("### V2 New Pre Load 2026")
with col_head2:
    st.text("👤 Nama Pengguna\n🕒 18 Sep 2026, 03:00")
    if st.button("Logout"):
        st.warning("Anda telah logout.")

st.divider()

# --- SIDEBAR (Menu Vertikal: Wilayah / Tujuan Pengiriman) ---
st.sidebar.header("Tujuan Pengiriman")
wilayah = st.sidebar.radio(
    "Pilih Wilayah:",
    ["Jakarta Pusat", "Jakarta Barat", "Jakarta Utara", "Tangerang", "Cikupa", "Bandung", "Semarang", "Surabaya"]
)

st.title(f"Dashboard Operational - {wilayah}")

# --- TAB UTAMA (Horizontal Tabs) ---
tab_summary, tab_pick, tab_preload, tab_ondelivery = st.tabs([
    "Summary Status", "Pick", "Preload", "On Delivery"
])

with tab_summary:
    st.subheader(f"Summary Status untuk {wilayah}")
    st.info("Ringkasan data dan grafik status pengiriman akan tampil di sini.")

with tab_pick:
    st.subheader("Proses Pick")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Input ID Request (Ready by)")
    with col2:
        st.text_input("Input ID Request (Picking by)")
    
    # Contoh Tabel Data Interaktif
    st.markdown("##### Data Tabel Pick")
    data_dummy = {"ID Request": ["REQ-001", "REQ-002"], "Jumlah Box": [5, 12], "Status": ["Pending", "Process"]}
    st.data_editor(data_dummy)

with tab_preload:
    st.subheader("Proses Preload")
    st.text_input("Input ID Request (Preload By)")

with tab_ondelivery:
    st.subheader("Proses On Delivery")
    st.write("Centang kotak di bawah untuk menandai status pengiriman:")
    # Contoh checkbox interaktif
    delivery_data = [
        {"ID Request": "REQ-001", "Jumlah Box": 5, "Status": "Ready", "Mark as On Delivery": True},
        {"ID Request": "REQ-002", "Jumlah Box": 12, "Status": "Process", "Mark as On Delivery": False}
    ]
    st.dataframe(delivery_data)