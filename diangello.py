import streamlit as st
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(
        "credenciales.json", scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet = client.open("citas_diangello").sheet1
    return sheet

st.title("Di'Angello Legend")
st.subheader("✂️ Salón de Belleza & Barbería")
st.write("---")
st.header("Nuestros Servicios")
st.write("✂️ **Corte caballero** — $250 MXN")
st.write("✂️ **Corte dama** — Consultar precio")
st.write("🎨 **Tinte completo** — Consultar precio")
st.write("🎨 **Mechas/Highlights** — Consultar precio")
st.write("✂️ **Corte + tinte caballero** — Consultar precio")
st.write("---")
st.header("📅 Agenda tu cita")
nombre = st.text_input("Tu nombre completo")
telefono = st.text_input("Tu WhatsApp")
servicio = st.selectbox("Servicio", ["Corte caballero $250","Corte dama","Tinte completo","Mechas/Highlights","Corte + tinte caballero"])
fecha = st.date_input("Fecha de tu cita")
hora = st.selectbox("Hora", ["9:00am","10:00am","11:00am","12:00pm","1:00pm","3:00pm","4:00pm","5:00pm"])
notas = st.text_area("Notas adicionales (opcional)")

if st.button("✅ Confirmar cita"):
    if nombre and telefono:
        try:
            sheet = get_sheet()
            registros = sheet.get_all_values()
            horario_ocupado = any(len(r) >= 6 and str(fecha) in r[4] and hora in r[5] for r in registros[1:])
            if horario_ocupado:
                st.error(f"⚠️ El horario {hora} del {fecha} ya está ocupado.")
            else:
                sheet.append_row([datetime.now().strftime("%d/%m/%Y %H:%M"), nombre, telefono, servicio, str(fecha), hora, notas])
                st.success(f"¡Cita confirmada, {nombre}! Te esperamos el {fecha} a las {hora} ✅")
                st.info("📱 Te contactaremos al WhatsApp para confirmar.")
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.error("⚠️ Por favor llena tu nombre y WhatsApp")

st.write("---")
st.caption("Di'Angello Legend ©️ 2026")
