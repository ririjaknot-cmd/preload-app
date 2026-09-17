import streamlit as st
import pandas as pd

# Konfigurasi halaman agar menggunakan mode 'wide' (lebar) ala dashboard
st.set_page_config(page_title="V2 Pre Load", layout="wide")

# --- HEADER ---
col_head1, col_head2 = st.columns([4, 1])
with col_head1:
    st.markdown("### V2 New Pre Load 2026")
with col_head2:
    st.text("👤 Uwa Tere\n🕒 18 Sep 2026, 03:00")
    if st.button("Logout"):
        st.warning("Anda telah logout.")

st.divider()

# --- SIDEBAR (Menu Vertikal: Wilayah / Tujuan Pengiriman) ---
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

st.title(f"Cabang - {wilayah}")

# --- TAB UTAMA (Horizontal Tabs) ---
tab_summary, tab_pick, tab_preload, tab_ondelivery = st.tabs([
    "Summary Status", "Picking", "Preload", "On Delivery"
])

with tab_summary:
    st.subheader(f"Summary Status untuk {wilayah}")
    st.info("Ringkasan data dan grafik status pengiriman akan tampil di sini.")

with tab_pick:
    st.subheader("Proses Picking")
    st.text_input("Input ID Request", key="input_picking")
    
    # Menggunakan Pandas DataFrame untuk st.data_editor
    st.markdown("##### Data Picking")
    df_pick = pd.DataFrame({
        "ID Request": ["REQ-001", "REQ-002"], 
        "Jumlah Box": [5, 12], 
        "Status": ["Pending", "Process"]
    })
    st.data_editor(df_pick, key="editor_picking")

with tab_preload:
    st.subheader("Proses Preload")
    st.text_input("Input ID Request", key="input_preload")

    # Menggunakan Pandas DataFrame untuk st.data_editor
    st.markdown("##### Data Picking")
    df_pick = pd.DataFrame({
        "ID Request": ["REQ-004", "REQ-003"], 
        "Jumlah Box": [4, 11], 
        "Status": ["Pending", "Process"]
    })
    st.data_editor(df_pick, key="editor_picking")

with tab_ondelivery:
    st.subheader("Proses On Delivery")
    st.write("Centang kotak di bawah untuk menandai status pengiriman:")
    
    # Menggunakan Pandas DataFrame untuk st.dataframe
    df_delivery = pd.DataFrame([
        {"ID Request": "REQ-001", "Jumlah Box": 5, "Status": "Ready", "Mark as On Delivery": True},
        {"ID Request": "REQ-002", "Jumlah Box": 12, "Status": "Process", "Mark as On Delivery": False}
    ])
    st.dataframe(df_delivery)
