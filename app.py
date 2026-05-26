import streamlit as st
import gspread
from datetime import datetime, date
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Di'Angello Legend", page_icon="✂️")

def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=scopes
    )

    client = gspread.authorize(creds)

    return client.open_by_key(
        "1N3QAuNXO0EckAOk5lb6ULmbk4nvs654dDJln-huHC1Q"
    ).sheet1

def dia_valido(fecha):
    return fecha.weekday() not in [0, 6]

st.image(
    "https://raw.githubusercontent.com/luigy2021-netizen/diangello-legend/main/diangello.png",
    width=180
)

st.title("Di'Angello Legend ✂️")

with st.form("formulario_cita"):
    nombre = st.text_input("Nombre completo")
    whatsapp = st.text_input("WhatsApp (10 dígitos)", max_chars=10)
    servicio = st.selectbox("Servicio", ["Corte Caballero", "Corte Dama", "Tinte Completo", "Mechas / Highlights", "Corte + Tinte Caballero"])
    fecha = st.date_input("Fecha", min_value=date.today())
    hora = st.selectbox("Hora", ["09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "01:00 PM", "03:00 PM", "04:00 PM", "05:00 PM", "06:00 PM"])
    notas = st.text_area("Comentarios adicionales")
    enviar = st.form_submit_button("Agendar cita")

if enviar:
    nombre = nombre.strip()
    whatsapp = whatsapp.strip()

    if not nombre:
        st.error("Escribe tu nombre")
    elif len(whatsapp) != 10:
        st.error(f"WhatsApp debe tener 10 dígitos. Tiene {len(whatsapp)}")
    elif not dia_valido(fecha):
        st.error("Di’Angello no trabaja domingos ni lunes")
    else:
        try:
            sheet = get_sheet()
            sheet.append_row([
                datetime.now().strftime("%Y%m%d%H%M%S"),
                nombre,
                whatsapp,
                servicio,
                str(fecha),
                hora,
                notas
            ])
            st.success("✅ Cita guardada correctamente")
        except Exception as e:
            st.error(f"Error: {e}")
