import streamlit as st
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# 1. Configuración de la página e interfaz limpia
st.set_page_config(page_title="Di'Angello Legend", page_icon="✂️", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_style_allowed=True)

# Conexión con Google Sheets usando tu lógica con gspread
def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # Buscamos el archivo de credenciales que ya tienes en tu carpeta
    creds = Credentials.from_service_account_file("credenciales.json", scopes=scopes)
    client = gspread.authorize(creds)
    # Abre la hoja que creamos en tu Drive
    sheet = client.open("Citas_DiAngello").sheet1
    return sheet

# 2. Encabezado principal
st.title("Di'Angello Legend")
st.subheader("✂️ Salón de Belleza & Barbería")
st.markdown("---")

# 3. Diccionario con tus servicios y precios reales fijos
SERVICIOS = {
    "Corte Caballero": 250,
    "Corte Dama": 350,       
    "Tinte Completo": 600,
    "Mechas / Highlights": 800,
    "Corte + Tinte Caballero": 450
}

# 4. Mostrar la lista de precios de manera elegante
st.markdown("### 📋 Nuestros Servicios y Precios")
cols = st.columns(2)
for i, (servicio, precio) in enumerate(SERVICIOS.items()):
    col_actual = cols[0] if i % 2 == 0 else cols[1]
    col_actual.markdown(f"**{servicio}** — `${precio} MXN`")

st.markdown("---")

# 5. Formulario de Citas
st.markdown("### 📅 Agenda tu cita")

with st.form("formulario_cita", clear_on_submit=True):
    nombre = st.text_input("Tu nombre completo:")
    whatsapp = st.text_input("Tu WhatsApp (a 10 dígitos):", max_chars=10)
    servicio_seleccionado = st.selectbox("Selecciona el servicio:", list(SERVICIOS.keys()))
    fecha = st.date_input("Fecha de tu cita:", min_value=datetime.today())
    
    horas_disponibles = ["09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "01:00 PM", 
                         "03:00 PM", "04:00 PM", "05:00 PM", "06:00 PM", "07:00 PM"]
    hora = st.selectbox("Hora de tu cita:", horas_disponibles)
    notas = st.text_area("Notas adicionales (opcional):")
    
    boton_agendar = st.form_submit_button("Agendar Cita")

# 6. Lógica de registro al presionar el botón
if boton_agendar:
    if not nombre or not whatsapp or len(whatsapp) < 10:
        st.error("⚠️ Por favor, llena los campos obligatorios. El WhatsApp debe tener 10 dígitos.")
    else:
        try:
            precio_final = SERVICIOS[servicio_seleccionado]
            
            # Conectar a la base de datos de Google Sheets
            sheet = get_sheet()
            
            # Generar un ID único basado en el tiempo actual para identificar la cita
            id_cita = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # Creamos la fila exactamente en el orden de las columnas de tu Sheets:
            # ID_Cita | Cliente | WhatsApp | Servicio | Precio | Fecha | Hora | Estado | Calificacion | Notas
            nueva_fila = [
                id_cita, 
                nombre, 
                whatsapp, 
                servicio_seleccionado, 
                precio_final, 
                str(fecha), 
                hora, 
                "Pendiente", 
                "", 
                notas
            ]
            
            # Insertar los datos en la hoja de cálculo
            sheet.append_row(nueva_fila)
            
            st.success(f"¡Gracias {nombre}! Tu cita para **{servicio_seleccionado}** (${precio_final} MXN) el día {fecha} a las {hora} ha sido agendada con éxito.")
            
            # --- Sistema de Confirmación por WhatsApp ---
            # Creamos el texto del mensaje para el negocio o el cliente
            mensaje_wa = f"¡Hola! Confirmación de cita en Di'Angello Legend:\n\n👤 Cliente: {nombre}\n✂️ Servicio: {servicio_seleccionado}\n💵 Precio: ${precio_final} MXN\n📅 Fecha: {fecha}\n⏰ Hora: {hora}"
            # Codificamos el texto para que sea válido en un enlace web
            mensaje_codificado = mensaje_wa.replace(" ", "%20").replace("\n", "%0A")
            
            # Creamos un botón interactivo para abrir WhatsApp
            url_whatsapp = f"https://wa.me/52{whatsapp}?text={mensaje_codificado}"
            st.markdown(f"[💬 Haz clic aquí para enviar la confirmación por WhatsApp]({url_whatsapp})")
            
        except Exception as e:
            st.error(f"❌ Hubo un problema al guardar tu cita. Error: {e}")

