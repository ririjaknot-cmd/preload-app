# Tab diubah dari On Delivery menjadi Manifest
        tab_id, tab_preload, tab_manifest = st.tabs([
            "ID Request", "Preload (Scan & Manifest)", "Manifest"
        ])

        # ... (kode tab_id dan tab_preload yang sudah ada sebelumnya tetap di sini) ...

        with tab_manifest:
            st.subheader(f"📦 Manajemen Manifest Pengiriman - {wilayah}")
            st.markdown("Kelola surat jalan / manifest pengiriman untuk cabang ini.")

            # Tombol untuk memunculkan form Buat Manifest Baru
            with st.expander("➕ Buat Manifest Baru", expanded=False):
                with st.form(key=f"form_buat_manifest_{wilayah}", clear_on_submit=True):
                    st.markdown("Pilih ID Request yang berstatus **Completed** untuk dimasukkan ke dalam Manifest.")
                    
                    # Ambil data ID yang sudah Completed dan sesuai wilayah
                    list_id_completed = []
                    if not df_filtered.empty:
                        for idx, row in df_filtered.iterrows():
                            jb = row.get("Jumlah Box") or 0
                            pr = row.get("Progress")
                            status_cek = format_status_dengan_ikon(pr, jb)
                            if "Completed" in status_cek: # Hanya ambil yang sudah Completed
                                r_id = str(row.get("ID") or row.get("id request") or "").split('.')[0].strip()
                                if r_id:
                                    list_id_completed.append(r_id)

                    selected_ids_manifest = st.multiselect(
                        "Pilih ID Request (Status Completed):",
                        options=list_id_completed,
                        placeholder="Pilih satu atau beberapa ID..."
                    )
                    
                    submit_manifest = st.form_submit_button("🚀 Generate Manifest Baru", type="primary")

                if submit_manifest:
                    if not selected_ids_manifest:
                        st.warning("⚠️ Pilih minimal satu ID Request yang berstatus Completed.")
                    else:
                        try:
                            # Generate Nomor Manifest Otomatis (Contoh: MNF-YYYYMMDD-HHMMSS)
                            now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
                            nomor_manifest = f"MNF-{now.strftime('%Y%m%d-%H%M%S')}"
                            
                            creds_dict = dict(st.secrets["connections"]["gsheets"])
                            gc = gspread.service_account_from_dict(creds_dict)
                            spreadsheet_name = st.secrets["connections"]["gsheets"].get("spreadsheet")
                            sh = gc.open_by_url(spreadsheet_name) if spreadsheet_name.startswith("http") else gc.open(spreadsheet_name)
                            
                            # Pastikan ada sheet bernama 'Manifest log', jika belum buat atau gunakan try-except
                            try:
                                ws_manifest = sh.worksheet("Manifest log")
                            except gspread.exceptions.WorksheetNotFound:
                                ws_manifest = sh.add_worksheet(title="Manifest log", rows=100, cols=10)
                                ws_manifest.append_row(["Nomor Manifest", "Tujuan Pengiriman", "ID List", "Total Box", "Dibuat Oleh", "Waktu Buat", "Status Manifest"])

                            # Hitung total box dari ID yang dipilih
                            total_box_manifest = 0
                            for target_id in selected_ids_manifest:
                                match_row = df_filtered[df_filtered["ID"].astype(str).str.contains(target_id)]
                                if not match_row.empty:
                                    total_box_manifest += int(match_row.iloc[0].get("Jumlah Box", 0))

                            dibuat_oleh = str(st.session_state.user_nama)
                            waktu_buat = now.strftime("%Y-%m-%d %H:%M:%S")
                            status_manifest = "Manifested"

                            # Simpan ke Google Sheets 'Manifest log'
                            ws_manifest.append_row([
                                nomor_manifest,
                                wilayah,
                                ", ".join(selected_ids_manifest),
                                total_box_manifest,
                                dibuat_oleh,
                                waktu_buat,
                                status_manifest
                            ])

                            st.success(f"✅ Berhasil membuat Manifest baru dengan Nomor: **{nomor_manifest}**!")
                            st.session_state[f"sound_effect_{wilayah}"] = "success"
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Gagal membuat manifest: {e}")

            st.markdown("---")
            st.markdown(f"##### 📋 Daftar Manifest Cabang: {wilayah}")

            # Membaca data dari sheet 'Manifest log' untuk ditampilkan
            try:
                creds_dict = dict(st.secrets["connections"]["gsheets"])
                gc = gspread.service_account_from_dict(creds_dict)
                spreadsheet_name = st.secrets["connections"]["gsheets"].get("spreadsheet")
                sh = gc.open_by_url(spreadsheet_name) if spreadsheet_name.startswith("http") else gc.open(spreadsheet_name)
                ws_manifest = sh.worksheet("Manifest log")
                data_manifest = ws_manifest.get_all_records()
                df_manifest_all = pd.DataFrame(data_manifest)
            except Exception:
                df_manifest_all = pd.DataFrame()

            # Filter manifest berdasarkan wilayah aktif
            if not df_manifest_all.empty and "Tujuan Pengiriman" in df_manifest_all.columns:
                df_manifest_wilayah = df_manifest_all[df_manifest_all["Tujuan Pengiriman"] == wilayah].copy()
            else:
                df_manifest_wilayah = pd.DataFrame()

            if not df_manifest_wilayah.empty:
                st.dataframe(df_manifest_wilayah, use_container_width=True, hide_index=True)

                # Tombol Edit Manifest (Pilih nomor manifest yang ingin diedit)
                st.markdown(:tools: **Edit / Kelola Manifest**)
                manifest_list_options = df_manifest_wilayah["Nomor Manifest"].tolist()
                selected_mnf_to_edit = st.selectbox("Pilih Nomor Manifest untuk dikelola:", options=manifest_list_options)

                if st.button("🔍 Detail / Edit Manifest Ini"):
                    st.info(f"Fitur edit untuk manifest **{selected_mnf_to_edit}** siap dikonfigurasi sesuai kebutuhan penambahan/pengurangan ID.")
            else:
                st.info("Belum ada data Manifest yang dibuat untuk cabang ini.")
