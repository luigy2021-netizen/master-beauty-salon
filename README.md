# Agenda Master Beauty Salon

MVP de una agenda hecha con Streamlit y Google Sheets. Guarda citas, respeta el
horario de comida y evita ofrecer espacios que se empalmen con citas existentes.
Incluye catálogo de servicios, banner promocional, sección de novedades y un
llamado comercial de Kroniq al final de la experiencia.

## 1. Configurar el proyecto de Google Cloud

Puedes reutilizar el proyecto de Google Cloud que pertenecía a la agenda
anterior. No es necesario consumir un proyecto adicional: cambia su nombre a
`Master Beauty Salon` y conserva la cuenta de servicio existente.

1. Entra a [Google Cloud Console](https://console.cloud.google.com/).
2. Selecciona el proyecto que vas a reutilizar.
3. Ve a **APIs y servicios > Biblioteca** y confirma que estén habilitadas **Google Sheets API** y
   **Google Drive API**.
4. En **APIs y servicios > Credenciales**, reutiliza la cuenta de servicio.
5. Si ya no conservas su clave, abre la cuenta, entra a **Claves**, elige
   **Agregar clave > Crear clave nueva > JSON** y descarga el archivo.
6. No publiques ni subas ese JSON a GitHub.

## 2. Crear y compartir Google Sheets

1. Crea una hoja de cálculo llamada `Agenda Master Beauty Salon`.
2. Renombra la pestaña inferior como `Citas`.
3. En la primera fila escribe exactamente estas siete columnas, una por celda:
   `Fecha`, `Hora`, `Servicio`, `Duración`, `Nombre`, `WhatsApp`, `Estado`.
4. Abre el JSON descargado y copia el valor de `client_email`.
5. Comparte la hoja de cálculo con ese correo y dale permiso de **Editor**.

La app también puede crear la pestaña y los encabezados si el archivo ya está
compartido y la pestaña todavía no existe.

## 3. Configurar Secrets localmente

1. Dentro de `master_beauty_agenda`, crea la carpeta `.streamlit` si no existe.
2. Copia `.streamlit/secrets.toml.example` como
   `.streamlit/secrets.toml`.
3. Copia en ese archivo los valores equivalentes del JSON de la cuenta de
   servicio. Conserva los `\n` de `private_key` tal como aparecen en el ejemplo.
4. Cambia `spreadsheet_name` si usaste otro nombre para el archivo y
   `worksheet_name` si usaste otro nombre para la pestaña.

`secrets.toml` y los archivos JSON están excluidos por `.gitignore`.

## 4. Ejecutar localmente

Abre PowerShell en la carpeta que contiene el proyecto y ejecuta:

```powershell
cd master_beauty_agenda
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Streamlit mostrará una dirección local, normalmente `http://localhost:8501`.

## 5. Subir a Streamlit Community Cloud

1. Crea un repositorio en GitHub y sube la carpeta del proyecto. Confirma antes
   que ni el JSON ni `.streamlit/secrets.toml` estén incluidos.
2. Entra a [Streamlit Community Cloud](https://share.streamlit.io/) e inicia
   sesión con GitHub.
3. Pulsa **Create app**, selecciona el repositorio, la rama y usa
   `master_beauty_agenda/app.py` como ruta del archivo principal si subiste todo el
   workspace. Si el contenido de esta carpeta está en la raíz del repositorio,
   usa `app.py`.
4. Abre **Advanced settings > Secrets** y pega todo el contenido de tu archivo
   local `.streamlit/secrets.toml`.
5. Guarda y despliega. Streamlit instalará automáticamente `requirements.txt`.

## Reglas implementadas

- Atención de martes a sábado, de 10:00 a 17:30.
- Comida de 14:00 a 15:00.
- Horarios cada 30 minutos.
- La cita debe terminar antes de las 17:30 y no puede tocar la comida.
- Las citas confirmadas bloquean toda su duración.
- Las filas cuyo estado sea `Cancelada` o `Cancelado` liberan su horario.
- El WhatsApp debe tener exactamente 10 dígitos.
