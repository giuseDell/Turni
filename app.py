import streamlit as st
import pandas as pd
import calendar
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder
import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials

# --- CONFIGURAZIONE GOOGLE SHEETS ---
# Sostituisci con il nome del tuo Google Sheet
GOOGLE_SHEET_NAME = "TurniDipendente"
WORKSHEET_NAME = "Dati"

# Percorso al file JSON con le credenziali
CREDENTIALS_FILE = "credenziali.json"
SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Autenticazione Google Sheets
credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
client = gspread.authorize(credentials)
sheet = client.open(GOOGLE_SHEET_NAME).worksheet(WORKSHEET_NAME)

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

# Creazione DataFrame
df = pd.DataFrame({
    "Data": date_list,
    "Giorno": [calendar.day_name[data.weekday()] for data in date_list],
    "RSA_Madama": ["" for _ in range(numero_giorni)],
    "RSA_AnniAzzurri": ["" for _ in range(numero_giorni)]
})

# Configurazione AgGrid
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_column("RSA_Madama", editable=True, cellEditor='agSelectCellEditor', cellEditorParams={'values': turni})
gb.configure_column("RSA_AnniAzzurri", editable=True, cellEditor='agSelectCellEditor', cellEditorParams={'values': turni})
gb.configure_column("Data", editable=False)
gb.configure_column("Giorno", editable=False)
grid_options = gb.build()

st.subheader(f"Turni per {mese} {anno}")
grid_response = AgGrid(
    df,
    gridOptions=grid_options,
    update_mode="MODEL_CHANGED",
    fit_columns_on_grid_load=True,
    theme="material"
)

# Bottone per salvare su Google Sheets
if st.button("💾 Salva su Google Sheets"):
    df_modificato = grid_response["data"]
    set_with_dataframe(sheet, df_modificato)
    st.success("Turni salvati correttamente su Google Sheets!")
