import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import pandas as pd
from PIL import Image, ImageTk, ImageDraw
import random
import string
import shutil
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import gspread
import subprocess
import json

def git_push_changes(mensaje_commit="Actualización inventario"):
    try:
        # Agrega todos los archivos modificados, incluidos las imágenes
        subprocess.run(["git", "add", "."], check=True)

        # Hace commit con mensaje
        subprocess.run(["git", "commit", "-m", mensaje_commit], check=True)

        # Hace push a la rama principal (main)
        subprocess.run(["git", "push", "origin", "main"], check=True)

        print("Cambios subidos a GitHub correctamente.")
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar git: {e}")



def exportar_a_json(df):
    # Crear lista de productos en formato JSON
    productos = []
    for _, row in df.iterrows():
        productos.append({
            "codigo": row["Código"],
            "nombre": row["Nombre"],
            "descripcion": row["Descripción"],
            "precio_compra": row["Precio Compra"],
            "precio_venta": row["Precio Venta"],
            "stock": row["Stock"],
            "vendidos": row["Vendidos"],
            "imagen": f"imagenes/{row['Imagen']}" if row.get("Imagen") else ""
        })
    with open("productos.json", "w", encoding="utf-8") as f:
        json.dump(productos, f, ensure_ascii=False, indent=4)



CREDENCIALES_JSON = 'inventarioinfopar-d0cf52f91f49.json'
SPREADSHEET_ID = '1Cgo4C--ByZikIPyXvZJtnBsCjOM4W9fju_N3O9T-3V0'
SHEET_NAME = 'Inventario_Infopar'

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

class InventarioSheets:
    def __init__(self):
        creds = Credentials.from_service_account_file(CREDENCIALES_JSON, scopes=SCOPES)
        self.cliente = gspread.authorize(creds)
        self.hoja = self.cliente.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

    def leer_datos(self):
        return self.hoja.get_all_records()


FILE_PATH = "inventario.xlsx"
IMG_FOLDER = "imagenes"


if not os.path.exists(IMG_FOLDER):
    os.makedirs(IMG_FOLDER)

def generar_codigo_unico(df):
    while True:
        codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if codigo not in df["Código"].values:
            return codigo
        
def guardar_df(df):
    df.to_excel(FILE_PATH, index=False)
    try:
        subir_df_a_sheets(df)
    except Exception as e:
        print(f"Error al subir datos a Google Sheets: {e}")

    try:
        exportar_a_json(df)  # Genera y guarda productos.json
    except Exception as e:
        print(f"Error al exportar productos.json: {e}")

    # Finalmente sube todos los cambios a GitHub
    git_push_changes("Actualización automática del inventario, Google Sheets y productos.json")




def crear_imagen_generica(size=(230,230)):
    # Crear imagen gris claro de fondo
    img = Image.new("RGBA", size, (220, 220, 220, 255))
    draw = ImageDraw.Draw(img)
    # Dibujar un ícono simple de cámara en blanco/gris oscuro
    w, h = size
    # Cámara: rectángulo + círculo de lente
    rect_w, rect_h = w*0.7, h*0.5
    rect_x0 = (w - rect_w) // 2
    rect_y0 = (h - rect_h) // 2 + 20
    rect_x1 = rect_x0 + rect_w
    rect_y1 = rect_y0 + rect_h
    draw.rectangle([rect_x0, rect_y0, rect_x1, rect_y1], fill=(150,150,150,255), outline=(100,100,100))
    # Lente (círculo)
    lens_radius = rect_h * 0.3
    lens_center = (w//2, rect_y0 + rect_h//2)
    draw.ellipse([
        lens_center[0]-lens_radius,
        lens_center[1]-lens_radius,
        lens_center[0]+lens_radius,
        lens_center[1]+lens_radius
    ], fill=(200,200,200), outline=(120,120,120))
    # Flash (rectángulo pequeño)
    flash_w, flash_h = rect_w * 0.2, rect_h * 0.2
    flash_x0 = rect_x1 - flash_w - 10
    flash_y0 = rect_y0 - flash_h - 5
    flash_x1 = flash_x0 + flash_w
    flash_y1 = flash_y0 + flash_h
    draw.rectangle([flash_x0, flash_y0, flash_x1, flash_y1], fill=(180,180,180), outline=(120,120,120))
    return img

def subir_df_a_sheets(df):
    creds = Credentials.from_service_account_file(CREDENCIALES_JSON, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)

    values = [df.columns.to_list()] + df.values.tolist()
    body = {'values': values}

    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1",
        valueInputOption="RAW",
        body=body
    ).execute()



class InventarioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("INFOPAR PARAGUAY")

        # Centrar ventana en pantalla
        ancho_ventana = 900
        alto_ventana = 580
        ancho_pantalla = self.root.winfo_screenwidth()
        alto_pantalla = self.root.winfo_screenheight()
        x = (ancho_pantalla - ancho_ventana) // 2
        y = (alto_pantalla - alto_ventana) // 2
        self.root.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")

        self.root.resizable(False, False)

        main_frame = tk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=3)
        main_frame.grid_columnconfigure(1, weight=1)

        # === Formulario de datos del producto ===
        form_frame = tk.LabelFrame(main_frame, text="Datos del Producto", padx=10, pady=10)
        form_frame.grid(row=0, column=0, sticky="nsew")

        form_interno = tk.Frame(form_frame)
        form_interno.grid(row=0, column=0, columnspan=3)

        campos_frame = tk.Frame(form_interno)
        campos_frame.grid(row=0, column=0, columnspan=2, sticky="nw")

        labels = ["Nombre", "Descripción", "Precio Compra", "Precio Venta", "Stock", "Vendidos"]
        self.entries = {}

        for i, label in enumerate(labels):
           tk.Label(campos_frame, text=label, anchor="w", width=15).grid(row=i, column=0, sticky="w", pady=5, padx=(0,5))
           ent = tk.Entry(campos_frame, width=35)
           ent.grid(row=i, column=1, pady=5, sticky="w")
           self.entries[label] = ent

        # Campo para la ruta de la imagen
        tk.Label(campos_frame, text="Imagen", anchor="w", width=15).grid(row=len(labels), column=0, sticky="w", pady=5, padx=(0,5))
        self.imagen_path_var = tk.StringVar()
        self.lbl_imagen_path = tk.Label(campos_frame, textvariable=self.imagen_path_var, relief="sunken", width=35, anchor="w")
        self.lbl_imagen_path.grid(row=len(labels), column=1, sticky="w", pady=5)

        btn_sel_img = tk.Button(campos_frame, text="Seleccionar Imagen", command=self.seleccionar_imagen)
        btn_sel_img.grid(row=len(labels)+1, column=1, sticky="w", pady=(0,10))

        # Logo a la derecha
        logo_frame = tk.Frame(form_interno, height=180, width=180)
        logo_frame.grid(row=0, column=2, rowspan=6, padx=(10,0), sticky="n")
        logo_frame.grid_propagate(False)

        logo_path = "logo_infopar.jpg"
        try:
          logo_img = Image.open(logo_path)
          logo_img.thumbnail((200, 200))
          self.logo_tk = ImageTk.PhotoImage(logo_img)
          lbl_logo = tk.Label(logo_frame, image=self.logo_tk)
          lbl_logo.pack(expand=True)
          logo_frame.grid_rowconfigure(0, weight=1)
          logo_frame.grid_columnconfigure(0, weight=1)
        except Exception:
          lbl_logo = tk.Label(logo_frame, text="Logo\nno disponible", relief="ridge", width=15, height=6)
          lbl_logo.pack(expand=True)

        btn_frame = tk.Frame(form_interno)
        btn_frame.grid(row=1, column=0, columnspan=3, pady=10, sticky="w")

        self.btn_agregar = tk.Button(btn_frame, text="Agregar", width=12, command=self.agregar_producto)
        self.btn_agregar.grid(row=0, column=0, padx=(0,5))
        self.btn_editar = tk.Button(btn_frame, text="Editar", width=12, command=self.editar_producto, state="disabled")
        self.btn_editar.grid(row=0, column=1, padx=5)
        self.btn_eliminar = tk.Button(btn_frame, text="Eliminar", width=12, command=self.eliminar_producto, state="disabled")
        self.btn_eliminar.grid(row=0, column=2, padx=5)
        self.btn_limpiar = tk.Button(btn_frame, text="Limpiar", width=12, command=self.limpiar_campos)
        self.btn_limpiar.grid(row=0, column=3, padx=5)

        # === Imagen a la derecha del formulario ===
        self.right_frame = tk.Frame(main_frame, width=240, height=240)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=10)
        self.right_frame.grid_propagate(False)

        self.img_label = tk.Label(self.right_frame, text="Imagen del Producto", relief="groove")
        self.img_label.place(relx=0.5, rely=0.5, anchor="center", width=230, height=230)

        # Crear imagen genérica y guardarla en atributo
        img_generica_pil = crear_imagen_generica()
        self.img_generica_tk = ImageTk.PhotoImage(img_generica_pil)

        # === Abajo: buscador + tabla + vista ampliada ===
        bottom_frame = tk.Frame(root)
        bottom_frame.pack(fill="both", expand=True, padx=10, pady=10)

        search_frame = tk.LabelFrame(bottom_frame, text="Buscar Producto", padx=10, pady=10)
        search_frame.pack(fill="x", pady=(0,10))

        tk.Label(search_frame, text="Nombre o descripción:").pack(side="left")
        self.entry_buscar = tk.Entry(search_frame, width=30)
        self.entry_buscar.pack(side="left", padx=5)
        btn_buscar = tk.Button(search_frame, text="Buscar", command=self.buscar_producto)
        btn_buscar.pack(side="left", padx=5)
        btn_mostrar = tk.Button(search_frame, text="Mostrar Todo", command=lambda: self.llenar_tabla(pd.DataFrame(self.inventario_sheets.leer_datos())))
        btn_mostrar.pack(side="left", padx=5)

        table_frame = tk.Frame(bottom_frame)
        table_frame.pack(fill="both", expand=True)

        columnas = ("Código", "Nombre", "Descripción", "Precio Compra", "Precio Venta", "Stock", "Vendidos")
        self.tree = ttk.Treeview(table_frame, columns=columnas, show="headings", height=10)

        for col in columnas:
            if col == "Código":
                ancho = 70
                anchor = "w"
            elif col == "Nombre":
                ancho = 150
                anchor = "w"
            elif col == "Descripción":
                ancho = 250
                anchor = "w"
            else:
                ancho = 70
                anchor = "e"

            self.tree.heading(col, text=col)
            self.tree.column(col, width=ancho, anchor=anchor)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        hsb.pack(side="bottom", fill="x")
        self.tree.configure(xscrollcommand=hsb.set)

        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<Button-1>", self.bloquear_redimension_columnas)

        vista_frame = tk.LabelFrame(bottom_frame, text="Vista Ampliada", padx=10, pady=10)
        vista_frame.pack(fill="both", expand=False, pady=(5, 0))

        self.lbl_nombre_ampliado = tk.Label(vista_frame, text="Nombre: ", font=("Arial", 12, "bold"), anchor="w", justify="left")
        self.lbl_nombre_ampliado.pack(fill="x", pady=2)

        txt_scroll_frame = tk.Frame(vista_frame)
        txt_scroll_frame.pack(fill="both", expand=True)

        self.txt_descripcion_ampliada = tk.Text(txt_scroll_frame, height=5, font=("Arial", 11), wrap="word")
        self.txt_descripcion_ampliada.pack(side="left", fill="both", expand=True)

        scroll = tk.Scrollbar(txt_scroll_frame, command=self.txt_descripcion_ampliada.yview)
        scroll.pack(side="right", fill="y")

        self.txt_descripcion_ampliada.configure(yscrollcommand=scroll.set)
        self.txt_descripcion_ampliada.config(state="disabled")

        self.tree.bind("<<TreeviewSelect>>", self.on_fila_seleccionada)

        self.df = pd.DataFrame(columns=columnas + ("Imagen",))
        self.producto_seleccionado_codigo = None
        self.imagen_producto_actual = None

        self.inventario_sheets = InventarioSheets()
        self.df = pd.DataFrame(self.inventario_sheets.leer_datos())

        self.llenar_tabla(self.df)
        self.limpiar_campos()


    def bloquear_redimension_columnas(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "separator":
            return "break"

    def seleccionar_imagen(self):
        archivo = filedialog.askopenfilename(filetypes=[("Archivos de imagen", "*.jpg *.jpeg *.png")])
        if archivo:
            self.imagen_path_var.set(archivo)

    def llenar_tabla(self, df):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for _, fila in df.iterrows():
            valores = (
                fila["Código"],
                fila["Nombre"],
                fila["Descripción"],
                str(int(fila["Precio Compra"])),
                str(int(fila["Precio Venta"])),
                str(int(fila["Stock"])),
                str(int(fila["Vendidos"]))
            )
            self.tree.insert("", "end", values=valores)

    def limpiar_campos(self):
        for ent in self.entries.values():
            ent.delete(0, tk.END)
        self.imagen_path_var.set("")
        self.producto_seleccionado_codigo = None
        self.btn_editar.config(state="disabled")
        self.btn_eliminar.config(state="disabled")
        self.btn_agregar.config(state="normal")
        # Mostrar imagen genérica sin texto para que el tamaño no cambie
        self.img_label.config(image=self.img_generica_tk, text="")
        self.img_label.image = self.img_generica_tk  # evitar GC

        self.lbl_nombre_ampliado.config(text="Nombre: ")
        self.txt_descripcion_ampliada.config(state="normal")
        self.txt_descripcion_ampliada.delete(1.0, tk.END)
        self.txt_descripcion_ampliada.insert(tk.END, "Descripción:")
        self.txt_descripcion_ampliada.config(state="disabled")

    def agregar_producto(self):
        datos = {}
        for label, ent in self.entries.items():
            valor = ent.get().strip()
            if not valor:
                messagebox.showerror("Error", f"El campo {label} es obligatorio.")
                return
            datos[label] = valor

        try:
            datos["Precio Compra"] = int(datos["Precio Compra"])
            datos["Precio Venta"] = int(datos["Precio Venta"])
            datos["Stock"] = int(datos["Stock"])
            datos["Vendidos"] = int(datos["Vendidos"])
        except ValueError:
            messagebox.showerror("Error", "Precio y cantidades deben ser números enteros.")
            return

        if self.imagen_path_var.get() == "":
            messagebox.showerror("Error", "Debe seleccionar una imagen.")
            return

        codigo = generar_codigo_unico(self.df)

        ext = os.path.splitext(self.imagen_path_var.get())[1]
        nombre_imagen = f"{codigo}{ext}"
        destino = os.path.join(IMG_FOLDER, nombre_imagen)
        try:
            shutil.copy2(self.imagen_path_var.get(), destino)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo copiar la imagen: {e}")
            return

        nuevo_producto = {
            "Código": codigo,
            "Nombre": datos["Nombre"],
            "Descripción": datos["Descripción"],
            "Precio Compra": datos["Precio Compra"],
            "Precio Venta": datos["Precio Venta"],
            "Stock": datos["Stock"],
            "Vendidos": datos["Vendidos"],
            "Imagen": nombre_imagen
        }

        nuevo_df = pd.DataFrame([nuevo_producto])
        self.df = pd.concat([self.df, nuevo_df], ignore_index=True)

        guardar_df(self.df)
        self.llenar_tabla(self.df)
        self.limpiar_campos()
        messagebox.showinfo("Éxito", "Producto agregado correctamente.")

    def on_fila_seleccionada(self, event):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            codigo = item["values"][0]
            producto = self.df[self.df["Código"] == codigo].iloc[0]
            self.producto_seleccionado_codigo = codigo

            for label in self.entries:
                self.entries[label].delete(0, tk.END)
                self.entries[label].insert(0, producto[label])

            nombre_img = producto.get("Imagen", None)
            if nombre_img:
                ruta_img = os.path.join(IMG_FOLDER, nombre_img)
                if os.path.exists(ruta_img):
                    img = Image.open(ruta_img)
                    img.thumbnail((230, 230))
                    self.imagen_producto_actual = ImageTk.PhotoImage(img)
                    self.img_label.config(image=self.imagen_producto_actual, text="")
                    self.img_label.image = self.imagen_producto_actual
                else:
                    # Imagen no encontrada, mostrar genérica sin texto
                    self.img_label.config(image=self.img_generica_tk, text="")
                    self.img_label.image = self.img_generica_tk
            else:
                # Sin imagen, mostrar imagen genérica sin texto
                self.img_label.config(image=self.img_generica_tk, text="")
                self.img_label.image = self.img_generica_tk

            self.imagen_path_var.set("")
            self.btn_editar.config(state="normal")
            self.btn_eliminar.config(state="normal")
            self.btn_agregar.config(state="disabled")

            self.lbl_nombre_ampliado.config(text=f"Nombre: {producto['Nombre']}")
            self.txt_descripcion_ampliada.config(state="normal")
            self.txt_descripcion_ampliada.delete(1.0, tk.END)
            self.txt_descripcion_ampliada.insert(tk.END, producto["Descripción"])
            self.txt_descripcion_ampliada.config(state="disabled")

    def editar_producto(self):
        if not self.producto_seleccionado_codigo:
            messagebox.showerror("Error", "No hay producto seleccionado.")
            return

        datos = {}
        for label, ent in self.entries.items():
            valor = ent.get().strip()
            if not valor:
                messagebox.showerror("Error", f"El campo {label} es obligatorio.")
                return
            datos[label] = valor

        try:
            datos["Precio Compra"] = int(datos["Precio Compra"])
            datos["Precio Venta"] = int(datos["Precio Venta"])
            datos["Stock"] = int(datos["Stock"])
            datos["Vendidos"] = int(datos["Vendidos"])
        except ValueError:
            messagebox.showerror("Error", "Precio y cantidades deben ser números enteros.")
            return

        if self.imagen_path_var.get():
            ext = os.path.splitext(self.imagen_path_var.get())[1]
            nombre_imagen = f"{self.producto_seleccionado_codigo}{ext}"
            destino = os.path.join(IMG_FOLDER, nombre_imagen)
            try:
                shutil.copy2(self.imagen_path_var.get(), destino)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo copiar la imagen: {e}")
                return
            self.df.loc[self.df["Código"] == self.producto_seleccionado_codigo, "Imagen"] = nombre_imagen

        idx = self.df[self.df["Código"] == self.producto_seleccionado_codigo].index[0]
        self.df.at[idx, "Nombre"] = datos["Nombre"]
        self.df.at[idx, "Descripción"] = datos["Descripción"]
        self.df.at[idx, "Precio Compra"] = datos["Precio Compra"]
        self.df.at[idx, "Precio Venta"] = datos["Precio Venta"]
        self.df.at[idx, "Stock"] = datos["Stock"]
        self.df.at[idx, "Vendidos"] = datos["Vendidos"]

        guardar_df(self.df)
        self.llenar_tabla(self.df)
        self.limpiar_campos()
        messagebox.showinfo("Éxito", "Producto editado correctamente.")

    def eliminar_producto(self):
        if not self.producto_seleccionado_codigo:
            messagebox.showerror("Error", "No hay producto seleccionado.")
            return
        confirm = messagebox.askyesno("Confirmar", "¿Está seguro de eliminar el producto?")
        if confirm:
            producto = self.df[self.df["Código"] == self.producto_seleccionado_codigo].iloc[0]
            nombre_img = producto.get("Imagen", None)
            self.df = self.df[self.df["Código"] != self.producto_seleccionado_codigo]

            guardar_df(self.df)
            self.llenar_tabla(self.df)
            self.limpiar_campos()
            messagebox.showinfo("Éxito", "Producto eliminado correctamente.")

            if nombre_img:
                if nombre_img not in self.df["Imagen"].values:
                    ruta_img = os.path.join(IMG_FOLDER, nombre_img)
                    if os.path.exists(ruta_img):
                        try:
                            os.remove(ruta_img)
                        except Exception as e:
                            messagebox.showwarning("Advertencia", f"No se pudo eliminar la imagen física: {e}")

    def buscar_producto(self):
        texto = self.entry_buscar.get().strip().lower()
        if texto == "":
            messagebox.showerror("Error", "Ingrese un texto para buscar.")
            return
        df_filtrado = self.df[
            self.df["Nombre"].str.lower().str.contains(texto) | 
            self.df["Descripción"].str.lower().str.contains(texto)
        ]
        if df_filtrado.empty:
            messagebox.showinfo("Resultados", "No se encontraron productos que coincidan.")
        self.llenar_tabla(df_filtrado)


if __name__ == "__main__":
    root = tk.Tk()
    app = InventarioApp(root)
    root.mainloop()
