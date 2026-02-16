import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

# -------------------------------
# Configuración
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE_DIR, "productos.json")
CRED_FILE = os.path.join(BASE_DIR, "inventarioinfopar-d0cf52f91f49.json")  # tu archivo de credenciales
SHEET_NAME = "Inventario_Infopar"  # nombre de tu hoja de Google Sheets

print("BASE_DIR:", BASE_DIR)
print("CRED_FILE:", CRED_FILE)
print("Archivo existe:", os.path.exists(CRED_FILE))

# -------------------------------
# Autenticación con Google Sheets
# -------------------------------
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
credenciales = ServiceAccountCredentials.from_json_keyfile_name(CRED_FILE, scope)
gc = gspread.authorize(credenciales)

# Abrir la hoja
sh = gc.open(SHEET_NAME)
worksheet = sh.sheet1  # primera pestaña

# -------------------------------
# Leer productos.json
# -------------------------------
with open(JSON_FILE, "r", encoding="utf-8") as f:
    productos = json.load(f)

# -------------------------------
# Limpiar hoja actual
# -------------------------------
worksheet.clear()

# -------------------------------
# Encabezados
# -------------------------------
encabezados = ["Código", "Nombre", "Descripción", "Precio Compra", "Precio Venta",
               "Stock", "Vendidos", "Imagen", "Ganancia", "Inversión"]
worksheet.append_row(encabezados)

# -------------------------------
# Preparar todas las filas
# -------------------------------
filas = []
for p in productos:
    fila = [
        p.get("codigo", ""),
        p.get("nombre", ""),
        p.get("descripcion", ""),
        p.get("precio_compra", 0),
        p.get("precio_venta", 0),
        p.get("stock", 0),
        p.get("vendidos", 0),
        p.get("imagen", ""),
        p.get("ganancia", 0),
        p.get("inversion", 0)
    ]
    filas.append(fila)

# -------------------------------
# Subir todas las filas de una sola vez

print("Cantidad de productos que se van a subir:", len(filas))
print("Primera fila de datos:", filas[0])

# -------------------------------
worksheet.append_rows(filas, value_input_option="USER_ENTERED")

print("Productos subidos a Google Sheets correctamente.")

