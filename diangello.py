import streamlit as st
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

# ── Conexión a Google Sheets ──────────────────────────────────────────────────
def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open("citas_diangello").sheet1
    return sheet

# ── Header ────────────────────────────────────────────────────────────────────
st.image("diangelo.png", width=700, use_container_width=True)
st.title("Di'Angello Legend")
st.sub
