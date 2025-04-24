# Bottone per salvare su Google Sheets
if st.button("💾 Salva su Google Sheets"):
    # Recupera i dati modificati da `st.data_editor`
    df_modificato = edited_df.copy()

    # Legge tutto il foglio e rimuove i dati dello stesso mese
    df_tutti = get_as_dataframe(sheet, evaluate_formulas=True)
    df_tutti["Data"] = pd.to_datetime(df_tutti["Data"], errors='coerce')
    df_tutti = df_tutti[~((df_tutti["Data"].dt.month == numero_mese) & (df_tutti["Data"].dt.year == anno))]

    # Aggiunge i dati nuovi
    df_modificato["Data"] = pd.to_datetime(df_modificato["Data"], errors='coerce')
    df_finale = pd.concat([df_tutti, df_modificato], ignore_index=True)
    df_finale = df_finale.sort_values("Data")

    # Salva su Google Sheets
    sheet.clear()
    set_with_dataframe(sheet, df_finale)
    st.success("Turni aggiornati correttamente su Google Sheets!")

    # Rileggi i dati aggiornati da Google Sheets
    df_updated = get_as_dataframe(sheet, evaluate_formulas=True)
    df_updated["Data"] = pd.to_datetime(df_updated["Data"], errors='coerce')
    df_updated = df_updated[(df_updated["Data"].dt.month == numero_mese) & (df_updated["Data"].dt.year == anno)]

    # Mostra i dati aggiornati nell'app
    edited_df = st.data_editor(
        df_updated,  # Carica i dati aggiornati
        column_config={
            "RSA_Madama": st.column_config.SelectboxColumn("RSA_Madama", options=turni),
            "RSA_AnniAzzurri": st.column_config.SelectboxColumn("RSA_AnniAzzurri", options=turni)
        },
        use_container_width=True,
        hide_index=True,
        num_rows="fixed"
    )
