import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe, get_as_dataframe
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- CONFIGURAZIONE GOOGLE SHEETS ---
SPREADSHEET_ID = "1WTVrHQP7NulYX5gLBS-9DZfhwxY9RVZTcaR3P79rNlA"
WORKSHEET_NAME = "Dati"

# Autenticazione Google Sheets da secrets
SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
credentials = Credentials.from_service_account_info(dict(creds_dict), scopes=SCOPES)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)

# Giorni della settimana in italiano
giorni_settimana = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

# Calcolo delle ore e guadagni per ogni turno
turni_ore = {
    "M1": 7, "M2": 6, "P1": 7, "P2": 6, "N": 10
}
turni_tariffa = {
    "M1": 10, "M2": 9, "P1": 10, "P2": 9, "N": 12
}

# --- INTERFACCIA STREAMLIT ---
st.title("Gestione Turni - Dipendente Unico")

# Aggiungi tab di navigazione
tab = st.selectbox("Seleziona una pagina", ["Turni", "Riepilogo Economico"])

# --- Pagina Turni ---
if tab == "Turni":
    st.subheader("Gestione Turni")
    
    # Selezione mese e anno
    oggi = datetime.today()
    mese = st.selectbox("Seleziona mese", list(calendar.month_name[1:]), index=oggi.month-1)
    anno = st.number_input("Anno", min_value=2020, max_value=2100, value=oggi.year, step=1)

    # Generazione giorni del mese
    numero_mese = list(calendar.month_name).index(mese)
    numero_giorni = calendar.monthrange(anno, numero_mese)[1]
    date_list = [datetime(anno, numero_mese, giorno).date() for giorno in range(1, numero_giorni + 1)]

    # Turni disponibili
    turni = ["", "M1", "M2", "P1", "P2", "N"]

    # --- CARICAMENTO DATI DA GOOGLE SHEET ---
    df_sheet = get_as_dataframe(sheet, evaluate_formulas=True)

    # Conversione colonna Data in datetime
    if "Data" in df_sheet.columns:
        df_sheet["Data"] = pd.to_datetime(df_sheet["Data"], errors='coerce')
    else:
        df_sheet = pd.DataFrame(columns=["Data", "Giorno", "RSA_Madama", "RSA_AnniAzzurri"])

    # Filtro per mese e anno selezionati
    df_filtered = df_sheet[(df_sheet["Data"].dt.month == numero_mese) & (df_sheet["Data"].dt.year == anno)]
    df_filtered = df_filtered.sort_values("Data")

    # Se mancano giorni, li aggiungiamo
    df = pd.DataFrame({
        "Data": date_list,
        "Giorno": [giorni_settimana[data.weekday()] for data in date_list],
        "RSA_Madama": ["" for _ in range(numero_giorni)],
        "RSA_AnniAzzurri": ["" for _ in range(numero_giorni)]
    })

    # Aggiorna la tabella con i dati esistenti (merge)
    for i, row in df.iterrows():
        giorno_data = row["Data"]
        match = df_filtered[df_filtered["Data"] == giorno_data]
        if not match.empty:
            df.at[i, "RSA_Madama"] = match.iloc[0].get("RSA_Madama", "")
            df.at[i, "RSA_AnniAzzurri"] = match.iloc[0].get("RSA_AnniAzzurri", "")

    # Visualizza la tabella
    st.subheader("Tabella dei Turni")
    st.write(df)

    # Funzione per modificare il turno
    def modifica_turno(row_index):
        selected_row = df.iloc[row_index]
        st.subheader(f"Modifica il turno per {selected_row['Data']}")
        
        # Form per modificare i dati
        rsa_madama = st.selectbox("RSA_Madama", ["", "M1", "M2", "P1", "P2", "N"], index=["", "M1", "M2", "P1", "P2", "N"].index(selected_row["RSA_Madama"]))
        rsa_anni_azzurri = st.selectbox("RSA_AnniAzzurri", ["", "M1", "M2", "P1", "P2", "N"], index=["", "M1", "M2", "P1", "P2", "N"].index(selected_row["RSA_AnniAzzurri"]))
        
        if st.button("Salva modifiche"):
            # Salva i dati modificati
            df.at[row_index, "RSA_Madama"] = rsa_madama
            df.at[row_index, "RSA_AnniAzzurri"] = rsa_anni_azzurri
            st.success(f"Turno del {selected_row['Data']} aggiornato!")

            # Aggiorna il Google Sheet
            df["Data"] = pd.to_datetime(df["Data"], errors='coerce')
            set_with_dataframe(sheet, df)
            st.write(df)  # Ritorna la tabella aggiornata

    # Aggiungi il pulsante "Modifica" per ogni riga
    for i in range(len(df)):
        if st.button(f"Modifica {df['Data'][i]}"):
            modifica_turno(i)

# --- Pagina Riepilogo Economico ---
if tab == "Riepilogo Economico":
    st.subheader("Riepilogo Economico")

    # Carica i dati da Google Sheets
    df_sheet = get_as_dataframe(sheet, evaluate_formulas=True)
    df_sheet["Data"] = pd.to_datetime(df_sheet["Data"], errors='coerce')
    
    # Calcola il totale ore e guadagno per ogni turno
    df_sheet["Ore_Madama"] = df_sheet["RSA_Madama"].map(turni_ore)
    df_sheet["Ore_AnniAzzurri"] = df_sheet["RSA_AnniAzzurri"].map(turni_ore)
    df_sheet["Guadagno_Madama"] = df_sheet["RSA_Madama"].map(turni_tariffa) * df_sheet["Ore_Madama"]
    df_sheet["Guadagno_AnniAzzurri"] = df_sheet["RSA_AnniAzzurri"].map(turni_tariffa) * df_sheet["Ore_AnniAzzurri"]

    # Totale ore e guadagno
    total_ore_madama = df_sheet["Ore_Madama"].sum()
    total_ore_anni_azzurri = df_sheet["Ore_AnniAzzurri"].sum()
    total_guadagno_madama = df_sheet["Guadagno_Madama"].sum()
    total_guadagno_anni_azzurri = df_sheet["Guadagno_AnniAzzurri"].sum()

    # Visualizza il riepilogo
    st.write(f"**Totale Ore RSA Madama**: {total_ore_madama} ore")
    st.write(f"**Totale Ore RSA Anni Azzurri**: {total_ore_anni_azzurri} ore")
    st.write(f"**Totale Guadagno RSA Madama**: € {total_guadagno_madama:.2f}")
    st.write(f"**Totale Guadagno RSA Anni Azzurri**: € {total_guadagno_anni_azzurri:.2f}")

    # Mostra il riepilogo in una tabella
    st.write(df_sheet[["Data", "RSA_Madama", "Guadagno_Madama", "RSA_AnniAzzurri", "Guadagno_AnniAzzurri"]])
