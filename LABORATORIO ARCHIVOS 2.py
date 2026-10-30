import os
import stat
import json
import hashlib
import zipfile
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog, ttk

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

ID_LEN = 10
NOMBRE_LEN = 30
TEL_LEN = 15
CORREO_LEN = 35
CIUDAD_LEN = 20
RECORD_LEN = ID_LEN + NOMBRE_LEN + TEL_LEN + CORREO_LEN + CIUDAD_LEN  

DATA_FILE = "contactos.dat"
INDEX_FILE = "indice.json"
HASH_FILE = "contactos.sha256"

class AgendaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Agenda de Contactos")
        self.root.geometry("650x550")
        
        self.verificar_integridad_inicial()
        self.crear_interfaz()
        self.cargar_indice()

    def actualizar_hash(self):
        if os.path.exists(DATA_FILE):
            sha256_hash = hashlib.sha256()
            with open(DATA_FILE, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            with open(HASH_FILE, "w", encoding="utf-8") as f:
                f.write(sha256_hash.hexdigest())

    def verificar_integridad_inicial(self):
        if os.path.exists(DATA_FILE) and os.path.exists(HASH_FILE):
            sha256_hash = hashlib.sha256()
            with open(DATA_FILE, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            current_hash = sha256_hash.hexdigest()
            
            with open(HASH_FILE, "r", encoding="utf-8") as f:
                saved_hash = f.read().strip()
                
            if current_hash != saved_hash:
                messagebox.showwarning(
                    "Alerta de Integridad", 
                    "¡Advertencia! El archivo de contactos fue modificado fuera de la aplicación."
                )

    def cargar_indice(self):
        if os.path.exists(INDEX_FILE):
            try:
                with open(INDEX_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def guardar_indice(self, indice):
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(indice, f, indent=4)

    def crear_interfaz(self):
        menubar = tk.Menu(self.root)
        
        menu_contactos = tk.Menu(menubar, tearoff=0)
        menu_contactos.add_command(label="Agregar / Modificar", command=self.guardar_contacto)
        menu_contactos.add_command(label="Buscar por ID", command=self.buscar_contacto)
        menubar.add_cascade(label="Contactos", menu=menu_contactos)
        
        menu_exportar = tk.Menu(menubar, tearoff=0)
        menu_exportar.add_command(label="Exportar a JSON y PDF", command=self.exportar_datos)
        menubar.add_cascade(label="Exportar", menu=menu_exportar)
        
        menu_herramientas = tk.Menu(menubar, tearoff=0)
        menu_herramientas.add_command(label="Verificar Integridad", command=self.verificar_integridad_manual)
        menu_herramientas.add_command(label="Crear Respaldo ZIP", command=self.crear_respaldo)
        menu_herramientas.add_command(label="Información del Archivo", command=self.mostrar_info_archivo)
        menubar.add_cascade(label="Herramientas", menu=menu_herramientas)
        
        menu_ayuda = tk.Menu(menubar, tearoff=0)
        menu_ayuda.add_command(label="Acerca de", command=lambda: messagebox.showinfo("Ayuda", "Agenda de Contactos"))
        menubar.add_cascade(label="Ayuda", menu=menu_ayuda)
        
        self.root.config(menu=menubar)

        frame = tk.LabelFrame(self.root, text=" Datos del Contacto ", padx=15, pady=15)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        labels = ["ID:", "Nombre:", "Teléfono:", "Correo:", "Ciudad:"]
        self.entries = {}

        for i, text in enumerate(labels):
            tk.Label(frame, text=text).grid(row=i, column=0, sticky="w", pady=5)
            e = tk.Entry(frame, width=35)
            e.grid(row=i, column=1, pady=5)
            self.entries[text] = e

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Guardar/Actualizar", command=self.guardar_contacto, bg="#4CAF50", fg="white", width=15).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Buscar ID", command=self.buscar_contacto, bg="#2196F3", fg="white", width=15).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Limpiar", command=self.limpiar_campos, width=10).grid(row=0, column=2, padx=5)

    def limpiar_campos(self):
        for e in self.entries.values():
            e.delete(0, tk.END)

    def empaquetar_registro(self, cid, nombre, telefono, correo, ciudad):
        return (
            str(cid).ljust(ID_LEN)[:ID_LEN] +
            str(nombre).ljust(NOMBRE_LEN)[:NOMBRE_LEN] +
            str(telefono).ljust(TEL_LEN)[:TEL_LEN] +
            str(correo).ljust(CORREO_LEN)[:CORREO_LEN] +
            str(ciudad).ljust(CIUDAD_LEN)[:CIUDAD_LEN]
        )

    def guardar_contacto(self):
        cid = self.entries["ID:"].get().strip()
        nombre = self.entries["Nombre:"].get().strip()
        telefono = self.entries["Teléfono:"].get().strip()
        correo = self.entries["Correo:"].get().strip()
        ciudad = self.entries["Ciudad:"].get().strip()

        if not cid.isdigit():
            messagebox.showerror("Error", "El ID debe ser un número entero válido.")
            return

        registro_str = self.empaquetar_registro(cid, nombre, telefono, correo, ciudad)
        indice = self.cargar_indice()

        try:
            mode = "r+b" if os.path.exists(DATA_FILE) else "w+b"
            with open(DATA_FILE, mode) as f:
                if cid in indice:
                    reg_num = indice[cid]
                    f.seek(reg_num * (RECORD_LEN + 1))
                    print(f"Posición actual: {f.tell()}") 
                    f.write((registro_str + "\n").encode("utf-8"))
                    messagebox.StatusOK = messagebox.showinfo("Éxito", f"Contacto con ID {cid} actualizado correctamente.")
                else:
                    f.seek(0, os.SEEK_END)
                    reg_num = f.tell() // (RECORD_LEN + 1)
                    f.write((registro_str + "\n").encode("utf-8"))
                    indice[cid] = reg_num
                    self.guardar_indice(indice)
                    messagebox.showinfo("Éxito", f"Contacto agregado exitosamente en el registro {reg_num}.")
            
            self.actualizar_hash()
            self.limpiar_campos()
        except Exception as e:
            messagebox.showerror("Error de Archivo", f"Ocurrió un error al guardar: {e}")

    def buscar_contacto(self):
        cid = self.entries["ID:"].get().strip()
        if not cid.isdigit():
            messagebox.showerror("Error", "Ingrese un ID válido para buscar.")
            return

        indice = self.cargar_indice()
        if cid not in indice:
            messagebox.showwarning(f"El ID {cid} no existe en la agenda.")
            return

        reg_num = indice[cid]
        try:
            with open(DATA_FILE, "rb") as f:
                f.seek(reg_num * (RECORD_LEN + 1))
                print(f"Búsqueda con seek - Posición: {f.tell()}") 
                linea = f.read(RECORD_LEN).decode("utf-8")

            r_id = linea[0:ID_LEN].strip()
            r_nombre = linea[ID_LEN:ID_LEN+NOMBRE_LEN].strip()
            r_tel = linea[ID_LEN+NOMBRE_LEN:ID_LEN+NOMBRE_LEN+TEL_LEN].strip()
            r_correo = linea[ID_LEN+NOMBRE_LEN+TEL_LEN:ID_LEN+NOMBRE_LEN+TEL_LEN+CORREO_LEN].strip()
            r_ciudad = linea[ID_LEN+NOMBRE_LEN+TEL_LEN+CORREO_LEN:].strip()

            self.limpiar_campos()
            self.entries["ID:"].insert(0, r_id)
            self.entries["Nombre:"].insert(0, r_nombre)
            self.entries["Teléfono:"].insert(0, r_tel)
            self.entries["Correo:"].insert(0, r_correo)
            self.entries["Ciudad:"].insert(0, r_ciudad)

            messagebox.showinfo("Búsqueda Exitosa", f"Contacto encontrado en el registro #{reg_num}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer el archivo: {e}")

    def exportar_datos(self):
        indice = self.cargar_indice()
        if not indice:
            messagebox.showwarning("No hay contactos para exportar")
            return

        contactos_lista = []
        try:
            with open(DATA_FILE, "rb") as f:
                for cid, reg_num in indice.items():
                    f.seek(reg_num * (RECORD_LEN + 1))
                    linea = f.read(RECORD_LEN).decode("utf-8")
                    contactos_lista.append({
                        "id": linea[0:ID_LEN].strip(),
                        "nombre": linea[ID_LEN:ID_LEN+NOMBRE_LEN].strip(),
                        "telefono": linea[ID_LEN+NOMBRE_LEN:ID_LEN+NOMBRE_LEN+TEL_LEN].strip(),
                        "correo": linea[ID_LEN+NOMBRE_LEN+TEL_LEN:ID_LEN+NOMBRE_LEN+TEL_LEN+CORREO_LEN].strip(),
                        "ciudad": linea[ID_LEN+NOMBRE_LEN+TEL_LEN+CORREO_LEN:].strip()
                    })

            json_filename = "contactos_exportados.json"
            with open(json_filename, "w", encoding="utf-8") as jf:
                json.dump(contactos_lista, jf, indent=4, ensure_ascii=False)

            pdf_filename = "reporte_contactos.pdf"
            c = canvas.Canvas(pdf_filename, pagesize=letter)
            width, height = letter

            c.drawString(50, height - 50, "Reporte de Agenda de Contactos")
            c.drawString(50, height - 70, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            y = height - 110
            for cto in contactos_lista:
                if y < 50:
                    c.showPage()
                    y = height - 50
                texto = f"ID: {cto['id']} | Nombre: {cto['nombre']} | Tel: {cto['telefono']} | Correo: {cto['correo']} | Ciudad: {cto['ciudad']}"
                c.drawString(50, y, texto)
                y -= 20

            c.save()
            messagebox.showinfo("Exportación Exitosa", f"Archivos generados:\n- {json_filename}\n- {pdf_filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Error en la exportación: {e}")

    def verificar_integridad_manual(self):
        if not os.path.exists(DATA_FILE) or not os.path.exists(HASH_FILE):
            messagebox.showwarning("Faltan archivos de datos.")
            return

        sha256_hash = hashlib.sha256()
        with open(DATA_FILE, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        current_hash = sha256_hash.hexdigest()

        with open(HASH_FILE, "r", encoding="utf-8") as f:
            saved_hash = f.read().strip()

        if current_hash == saved_hash:
            messagebox.showinfo("Integridad Válida")
        else:
            messagebox.showerror("El archivo de contactos fue alterado manualmente fuera de la aplicación")

    def crear_respaldo(self):
        zip_filename = "respaldo_agenda.zip"
        try:
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if os.path.exists(DATA_FILE):
                    zipf.write(DATA_FILE)
                if os.path.exists(INDEX_FILE):
                    zipf.write(INDEX_FILE)

            orig_size = os.path.getsize(DATA_FILE) if os.path.exists(DATA_FILE) else 0
            zip_size = os.path.getsize(zip_filename)
            
            messagebox.showinfo(
                "Respaldo Creado",
                f"Respaldo ZIP generado con éxito:\n\n- Archivo: {zip_filename}\n- Tamaño original: {orig_size} bytes\n- Tamaño comprimido: {zip_size} bytes"
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el respaldo: {e}")

    def mostrar_info_archivo(self):
        if not os.path.exists(DATA_FILE):
            messagebox.showwarning("El archivo de contactos aún no ha sido creado")
            return

        file_stat = os.stat(DATA_FILE)
        size = file_stat.st_size
        mod_time = datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        readable = os.access(DATA_FILE, os.R_OK)
        writable = os.access(DATA_FILE, os.W_OK)

        info = (
            f"Archivo: {DATA_FILE}\n"
            f"Tamaño: {size} bytes\n"
            f"Última modificación: {mod_time}\n"
            f"Permiso de lectura: {'Sí' if readable else 'No'}\n"
            f"Permiso de escritura: {'Sí' if writable else 'No'}"
        )
        messagebox.showinfo("Información del Archivo", info)

if __name__ == "__main__":
    root = tk.Tk()
    app = AgendaApp(root)
    root.mainloop()