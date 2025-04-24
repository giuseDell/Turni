import streamlit as st
import pandas as pd
import calendar
from datetime import datetime
import gspread
from gspread_dataframe import set_with_dataframe, get_as_dataframe
from google.oauth2.service_account import Credentials
import json

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

# --- INTERFACCIA STREAMLIT ---
st.title("Gestione Turni - Dipendente Unico")

# Selezione mese e anno
oggi = datetime.today()
mese = st.selectbox("Seleziona mese", list(calendar.month_name)[1:], index=oggi.month-1)
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

# Evidenzia weekend (Sabato e Domenica)
def evidenzia_giorni(row):
    if row["Giorno"] in ["Sabato", "Domenica"]:
        return ["background-color: #ff4b4b; color: white"]*len(row)
    else:
        return [""]*len(row)

st.subheader(f"Turni per {mese} {anno}")

# Dropdown nelle colonne turni
st.write("Modifica i turni direttamente nella tabella:")

edited_df = st.data_editor(
    df,
    column_config={
        "RSA_Madama": st.column_config.SelectboxColumn("RSA_Madama", options=turni),
        "RSA_AnniAzzurri": st.column_config.SelectboxColumn("RSA_AnniAzzurri", options=turni)
    },
    use_container_width=True,
    hide_index=True,
    num_rows="fixed"
)

# Bottone per salvare su Google Sheets
if st.button("💾 Salva su Google Sheets"):
    # Legge tutto il foglio e rimuove i dati dello stesso mese
    df_tutti = get_as_dataframe(sheet, evaluate_formulas=True)
    df_tutti["Data"] = pd.to_datetime(df_tutti["Data"], errors='coerce')
    df_tutti = df_tutti[~((df_tutti["Data"].dt.month == numero_mese) & (df_tutti["Data"].dt.year == anno))]

    # Aggiunge i dati nuovi
    edited_df["Data"] = pd.to_datetime(edited_df["Data"], errors='coerce')
    df_finale = pd.concat([df_tutti, edited_df], ignore_index=True)
    df_finale = df_finale.sort_values("Data")

    # Salva su Google Sheets
    sheet.clear()
    set_with_dataframe(sheet, df_finale)
    st.success("Turni aggiornati correttamente su Google Sheets!")
