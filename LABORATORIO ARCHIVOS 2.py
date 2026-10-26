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
        self.root.title("Agenda de Contactos con Acceso Aleatorio")
        self.root.geometry("650x550")
        
        self.verificar_integridad_inicial()
        self.crear_interfaz()
        self.cargar_indice()

    def actualizar_hash(self):
        """Calcula y guarda el hash SHA-256 del archivo de contactos."""
        if os.path.exists(DATA_FILE):
            sha256_hash = hashlib.sha256()
            with open(DATA_FILE, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            with open(HASH_FILE, "w", encoding="utf-8") as f:
                f.write(sha256_hash.hexdigest())

    def verificar_integridad_inicial(self):
        """Verifica la integridad del archivo usando SHA-256 al iniciar."""
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
        """Carga el índice primario en JSON."""
        if os.path.exists(INDEX_FILE):
            try:
                with open(INDEX_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def guardar_indice(self, indice):
        """Guarda el índice primario en formato JSON[cite: 2]."""
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
        menu_ayuda.add_command(label="Acerca de", command=lambda: messagebox.showinfo("Ayuda", "Agenda de Contactos con Acceso Aleatorio."))
        menubar.add_cascade(label="Ayuda", menu=menu_ayuda)
        
        self.root.config(menu=menubar)

        frame = tk.LabelFrame(self.root, text=" Datos del Contacto ", padx=15, pady=15)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        labels = ["ID (entero):", "Nombre:", "Teléfono:", "Correo:", "Ciudad:"]
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
        """Rellena los campos con espacios hasta su largo máximo (Tamaño Fijo)[cite: 1]."""
        return (
            str(cid).ljust(ID_LEN)[:ID_LEN] +
            str(nombre).ljust(NOMBRE_LEN)[:NOMBRE_LEN] +
            str(telefono).ljust(TEL_LEN)[:TEL_LEN] +
            str(correo).ljust(CORREO_LEN)[:CORREO_LEN] +
            str(ciudad).ljust(CIUDAD_LEN)[:CIUDAD_LEN]
        )

    def guardar_contacto(self):
        """Agrega o modifica un contacto utilizando acceso aleatorio (seek, tell)[cite: 1, 2]."""
        cid = self.entries["ID (entero):"].get().strip()
        nombre = self.entries["Nombre:"].get().strip()
        telefono = self.entries["Teléfono:"].get().strip()
        correo = self.entries["Correo:"].get().strip()
        ciudad = self.entries["Ciudad:"].get().strip()

        if not cid.isdigit():
            messagebox.showerror("Error", "El ID debe ser un número entero válido[cite: 1, 2].")
            return

        registro_str = self.empaquetar_registro(cid, nombre, telefono, correo, ciudad)
        indice = self.cargar_indice()

        try:
            mode = "r+b" if os.path.exists(DATA_FILE) else "w+b"
            with open(DATA_FILE, mode) as f:
                if cid in indice:
                    reg_num = indice[cid]
                    f.seek(reg_num * (RECORD_LEN + 1))
                    print(f"Posición actual (tell): {f.tell()}") 
                    f.write((registro_str + "\n").encode("utf-8"))
                    messagebox.StatusOK = messagebox.showinfo("Éxito", f"Contacto con ID {cid} actualizado correctamente en el lugar.")
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
            messagebox.showerror("Error de Archivo", f"Ocurrió un error al guardar: {e}[cite: 2]")

    def buscar_contacto(self):
        """Busca un contacto consultando primero el índice JSON y luego usando seek()[cite: 1, 2]."""
        cid = self.entries["ID (entero):"].get().strip()
        if not cid.isdigit():
            messagebox.showerror("Error", "Ingrese un ID válido para buscar[cite: 1, 2].")
            return

        indice = self.cargar_indice()
        if cid not in indice:
            messagebox.showwarning("No encontrado", f"El ID {cid} no existe en la agenda[cite: 2].")
            return

        reg_num = indice[cid]
        try:
            with open(DATA_FILE, "rb") as f:
                f.seek(reg_num * (RECORD_LEN + 1))
                print(f"Búsqueda con seek - Posición (tell): {f.tell()}") 
                linea = f.read(RECORD_LEN).decode("utf-8")

            r_id = linea[0:ID_LEN].strip()
            r_nombre = linea[ID_LEN:ID_LEN+NOMBRE_LEN].strip()
            r_tel = linea[ID_LEN+NOMBRE_LEN:ID_LEN+NOMBRE_LEN+TEL_LEN].strip()
            r_correo = linea[ID_LEN+NOMBRE_LEN+TEL_LEN:ID_LEN+NOMBRE_LEN+TEL_LEN+CORREO_LEN].strip()
            r_ciudad = linea[ID_LEN+NOMBRE_LEN+TEL_LEN+CORREO_LEN:].strip()

            self.limpiar_campos()
            self.entries["ID (entero):"].insert(0, r_id)
            self.entries["Nombre:"].insert(0, r_nombre)
            self.entries["Teléfono:"].insert(0, r_tel)
            self.entries["Correo:"].insert(0, r_correo)
            self.entries["Ciudad:"].insert(0, r_ciudad)

            messagebox.showinfo("Búsqueda Exitosa", f"Contacto encontrado en el registro #{reg_num}[cite: 1, 2].")
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer el archivo: {e}[cite: 2]")
