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
    return client.open("Citas_DiAngello").sheet1

def dia_valido(fecha):
    return fecha.weekday() not in [0, 6]   # lunes=0 domingo=6

st.image(
    "https://raw.githubusercontent.com/luigy2021-netizen/diangello-legend/main/diangello.png",
    width=180
)

st.title("Di'Angello Legend ✂️")

nombre = st.text_input("Nombre completo")
whatsapp = st.text_input("WhatsApp (10 dígitos)")

servicio = st.selectbox(
    "Servicio",
    [
        "Corte Caballero",
        "Corte Dama",
        "Tinte Completo",
        "Mechas / Highlights",
        "Corte + Tinte Caballero"
    ]
)

fecha = st.date_input(
    "Fecha",
    min_value=date.today()
)

hora = st.selectbox(
    "Hora",
    [
        "09:00 AM",
        "10:00 AM",
        "11:00 AM",
        "12:00 PM",
        "01:00 PM",
        "03:00 PM",
        "04:00 PM",
        "05:00 PM",
        "06:00 PM"
    ]
)

if st.button("Agendar cita"):

    whatsapp = "".join(filter(str.isdigit, whatsapp))

    if not nombre:
        st.error("Escribe tu nombre")

    elif len(whatsapp) != 10:
        st.error("WhatsApp debe tener 10 dígitos")

    elif not dia_valido(fecha):
        st.error("Di’Angello no trabaja domingos ni lunes")

    else:
        try:
sheet.append_row([
    datetime.now().strftime("%Y%m%d%H%M%S"),
    nombre,
    whatsapp,
    servicio,
    str(fecha),
    hora,
    notas

        except Exception as e:
            st.error(f"Error: {e}")
            url_whatsapp = f"https://wa.me/52{whatsapp}?text={mensaje_codificado}"

            st.markdown(
                f"[💬 Haz clic aquí para enviar la confirmación por WhatsApp]({url_whatsapp})"
            )

        except Exception as e:
            st.error(f"❌ Hubo un problema al guardar tu cita. Error: {e}")

