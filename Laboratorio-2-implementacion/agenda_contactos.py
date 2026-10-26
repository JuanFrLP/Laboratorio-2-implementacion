import hashlib
import json
import os
import tkinter as tk
from tkinter import messagebox
import zipfile

ARCHIVO_DAT = "contactos.dat"
ARCHIVO_INDICE = "indice.json"
ARCHIVO_HASH = "contactos.sha256"
ARCHIVO_JSON = "contactos_exportados.json"
ARCHIVO_ZIP = "respaldo_contactos.zip"

TAM_ID = 10
TAM_NOMBRE = 30
TAM_TELEFONO = 15
TAM_CORREO = 35
TAM_CIUDAD = 20
TAM_REGISTRO = (
    TAM_ID + TAM_NOMBRE + TAM_TELEFONO + TAM_CORREO + TAM_CIUDAD + 1
)  # 111 bytes incluyendo salto de línea

indice = {}


# Limpia todos los campos de texto de la interfaz
def limpiar_campos():
    entry_id.delete(0, tk.END)
    entry_nombre.delete(0, tk.END)
    entry_telefono.delete(0, tk.END)
    entry_correo.delete(0, tk.END)
    entry_ciudad.delete(0, tk.END)


# Ajusta un texto a un tamaño exacto en bytes UTF-8 rellenando con espacios
def ajustar_campo(texto, tamano_bytes):
    datos = str(texto).encode("utf-8")[:tamano_bytes]
    while len(datos) > 0:
        try:
            datos.decode("utf-8")
            break
        except UnicodeDecodeError:
            datos = datos[:-1]
    return datos.ljust(tamano_bytes, b" ")


# Empaqueta los datos del contacto en un registro de tamaño fijo en bytes
def empaquetar_registro(id_c, nombre, telefono, correo, ciudad):
    b_id = ajustar_campo(id_c, TAM_ID)
    b_nom = ajustar_campo(nombre, TAM_NOMBRE)
    b_tel = ajustar_campo(telefono, TAM_TELEFONO)
    b_cor = ajustar_campo(correo, TAM_CORREO)
    b_ciu = ajustar_campo(ciudad, TAM_CIUDAD)
    return b_id + b_nom + b_tel + b_cor + b_ciu + b"\n"


# Desempaqueta una secuencia de bytes de tamaño fijo a un diccionario de contacto
def desempaquetar_registro(datos_bytes):
    i1 = TAM_ID
    i2 = i1 + TAM_NOMBRE
    i3 = i2 + TAM_TELEFONO
    i4 = i3 + TAM_CORREO
    i5 = i4 + TAM_CIUDAD

    return {
        "id": int(datos_bytes[0:i1].decode("utf-8", errors="ignore").strip()),
        "nombre": datos_bytes[i1:i2].decode("utf-8", errors="ignore").strip(),
        "telefono": datos_bytes[i2:i3].decode("utf-8", errors="ignore").strip(),
        "correo": datos_bytes[i3:i4].decode("utf-8", errors="ignore").strip(),
        "ciudad": datos_bytes[i4:i5].decode("utf-8", errors="ignore").strip(),
    }


# Carga el archivo de índice JSON en memoria
def cargar_indice():
    global indice
    if not os.path.exists(ARCHIVO_INDICE):
        indice = {}
        return
    try:
        with open(ARCHIVO_INDICE, "r", encoding="utf-8") as f:
            indice = json.load(f)
    except Exception as e:
        messagebox.showerror("Error", f"Error al leer el índice: {e}")
        indice = {}


# Guarda el diccionario de índice actual en el archivo JSON
def guardar_indice():
    try:
        with open(ARCHIVO_INDICE, "w", encoding="utf-8") as f:
            json.dump(indice, f, indent=4, ensure_ascii=False)
    except Exception as e:
        messagebox.showerror("Error", f"Error al guardar el índice: {e}")


# Calcula y devuelve el hash SHA-256 actual del archivo de contactos
def calcular_hash():
    if not os.path.exists(ARCHIVO_DAT):
        return None
    sha256 = hashlib.sha256()
    try:
        with open(ARCHIVO_DAT, "rb") as f:
            while bloque := f.read(4096):
                sha256.update(bloque)
        return sha256.hexdigest()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo calcular el hash: {e}")
        return None


# Guarda el hash SHA-256 actual en su archivo correspondiente
def actualizar_hash():
    hash_actual = calcular_hash()
    if hash_actual:
        try:
            with open(ARCHIVO_HASH, "w", encoding="utf-8") as f:
                f.write(hash_actual)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el hash: {e}")


# Compara el hash actual de contactos.dat con el hash almacenado
def verificar_integridad(mostrar_exito=True):
    if not os.path.exists(ARCHIVO_DAT):
        if mostrar_exito:
            messagebox.showinfo(
                "Integridad", "El archivo de contactos aún no existe."
            )
        return

    if not os.path.exists(ARCHIVO_HASH):
        messagebox.showwarning(
            "Integridad", "No se encontró el archivo hash de verificación."
        )
        return

    try:
        with open(ARCHIVO_HASH, "r", encoding="utf-8") as f:
            hash_guardado = f.read().strip()

        hash_actual = calcular_hash()

        if hash_actual == hash_guardado:
            if mostrar_exito:
                messagebox.showinfo(
                    "Integridad",
                    f"Integridad verificada correctamente.\nSHA-256: {hash_actual[:20]}...",
                )
        else:
            messagebox.showwarning(
                "Alerta de Seguridad",
                "¡El archivo de contactos fue modificado fuera de la aplicación!",
            )
    except Exception as e:
        messagebox.showerror("Error", f"Error al verificar integridad: {e}")


# Agrega un contacto al final de contactos.dat y actualiza el índice y el hash
def agregar_contacto():
    try:
        id_contacto = int(entry_id.get())
    except ValueError:
        messagebox.showerror("Error", "El ID debe ser un número entero.")
        return

    id_str = str(id_contacto)
    if id_str in indice:
        messagebox.showerror("Error", "Ya existe un contacto con ese ID.")
        return

    registro_bytes = empaquetar_registro(
        id_contacto,
        entry_nombre.get(),
        entry_telefono.get(),
        entry_correo.get(),
        entry_ciudad.get(),
    )

    try:
        modo = "r+b" if os.path.exists(ARCHIVO_DAT) else "w+b"
        with open(ARCHIVO_DAT, modo) as f:
            num_registro = len(indice)
            posicion = num_registro * TAM_REGISTRO
            f.seek(posicion)
            pos_actual = f.tell()
            f.write(registro_bytes)

        indice[id_str] = num_registro
        guardar_indice()
        actualizar_hash()

        messagebox.showinfo(
            "Éxito",
            f"Contacto guardado en el registro #{num_registro} (Byte {pos_actual}).",
        )
        limpiar_campos()
    except Exception as e:
        messagebox.showerror("Error", f"Error al guardar el contacto: {e}")


# Busca un contacto usando el índice y accede directamente a su posición con seek()
def buscar_contacto():
    try:
        id_buscar = int(entry_id.get())
    except ValueError:
        messagebox.showerror("Error", "El ID debe ser un número entero.")
        return

    id_str = str(id_buscar)
    if id_str not in indice:
        messagebox.showwarning(
            "No encontrado",
            "No se encontró ningún contacto con ese ID en el índice.",
        )
        return

    if not os.path.exists(ARCHIVO_DAT):
        messagebox.showerror("Error", f"No existe el archivo '{ARCHIVO_DAT}'.")
        return

    try:
        num_registro = indice[id_str]
        posicion = num_registro * TAM_REGISTRO

        with open(ARCHIVO_DAT, "rb") as f:
            f.seek(posicion)
            pos_actual = f.tell()
            datos_bytes = f.read(TAM_REGISTRO)

        if len(datos_bytes) < TAM_REGISTRO:
            messagebox.showerror(
                "Error", "El registro está incompleto o corrupto."
            )
            return

        c = desempaquetar_registro(datos_bytes)
        limpiar_campos()
        entry_id.insert(0, str(c["id"]))
        entry_nombre.insert(0, c["nombre"])
        entry_telefono.insert(0, c["telefono"])
        entry_correo.insert(0, c["correo"])
        entry_ciudad.insert(0, c["ciudad"])

        messagebox.showinfo(
            "Encontrado",
            f"Registro #{num_registro} leído desde el byte {pos_actual} (tell).",
        )
    except Exception as e:
        messagebox.showerror("Error", f"Error al leer el contacto: {e}")


# Sobrescribe únicamente el registro modificado en su posición exacta usando seek()
def modificar_contacto():
    try:
        id_modificar = int(entry_id.get())
    except ValueError:
        messagebox.showerror("Error", "El ID debe ser un número entero.")
        return

    id_str = str(id_modificar)
    if id_str not in indice:
        messagebox.showwarning(
            "No encontrado", "No se encontró ningún contacto con ese ID."
        )
        return

    if not os.path.exists(ARCHIVO_DAT):
        messagebox.showerror("Error", f"No existe el archivo '{ARCHIVO_DAT}'.")
        return

    try:
        num_registro = indice[id_str]
        posicion = num_registro * TAM_REGISTRO

        with open(ARCHIVO_DAT, "r+b") as f:
            f.seek(posicion)
            datos_actuales = f.read(TAM_REGISTRO)
            c = desempaquetar_registro(datos_actuales)

            nuevo_nombre = (
                entry_nombre.get() if entry_nombre.get() != "" else c["nombre"]
            )
            nuevo_telefono = (
                entry_telefono.get()
                if entry_telefono.get() != ""
                else c["telefono"]
            )
            nuevo_correo = (
                entry_correo.get() if entry_correo.get() != "" else c["correo"]
            )
            nueva_ciudad = (
                entry_ciudad.get() if entry_ciudad.get() != "" else c["ciudad"]
            )

            registro_nuevo = empaquetar_registro(
                id_modificar,
                nuevo_nombre,
                nuevo_telefono,
                nuevo_correo,
                nueva_ciudad,
            )

            f.seek(posicion)
            pos_actual = f.tell()
            f.write(registro_nuevo)

        actualizar_hash()
        messagebox.showinfo(
            "Éxito",
            f"Registro #{num_registro} sobrescrito in-place en el byte {pos_actual} (tell).",
        )
        limpiar_campos()
    except Exception as e:
        messagebox.showerror("Error", f"Error al modificar el contacto: {e}")


# Lee todos los registros de contactos.dat y los exporta a un archivo JSON
def exportar_json():
    if not os.path.exists(ARCHIVO_DAT):
        messagebox.showwarning(
            "Aviso", "No hay archivo de contactos para exportar."
        )
        return

    lista_exportar = []
    try:
        with open(ARCHIVO_DAT, "rb") as f:
            for id_str, num_reg in indice.items():
                f.seek(num_reg * TAM_REGISTRO)
                datos = f.read(TAM_REGISTRO)
                if len(datos) == TAM_REGISTRO:
                    lista_exportar.append(desempaquetar_registro(datos))

        with open(ARCHIVO_JSON, "w", encoding="utf-8") as f_json:
            json.dump(lista_exportar, f_json, indent=4, ensure_ascii=False)

        messagebox.showinfo(
            "Éxito", f"Contactos exportados en '{ARCHIVO_JSON}'."
        )
    except Exception as e:
        messagebox.showerror("Error", f"Error al exportar a JSON: {e}")


# Comprime el archivo de contactos y el índice dentro de un archivo .ZIP
def crear_respaldo_zip():
    if not os.path.exists(ARCHIVO_DAT) or not os.path.exists(ARCHIVO_INDICE):
        messagebox.showwarning(
            "Aviso", "Aún no existen los archivos necesarios para respaldar."
        )
        return

    try:
        with zipfile.ZipFile(
            ARCHIVO_ZIP, "w", zipfile.ZIP_DEFLATED
        ) as archivo_zip:
            archivo_zip.write(ARCHIVO_DAT)
            archivo_zip.write(ARCHIVO_INDICE)
        messagebox.showinfo("Éxito", f"Respaldo creado en '{ARCHIVO_ZIP}'.")
    except Exception as e:
        messagebox.showerror("Error", f"Error al crear el archivo ZIP: {e}")


# Muestra aviso temporal para la generación de PDF
def generar_pdf():
    messagebox.showinfo(
        "Pendiente", "Aquí se generará el reporte en formato PDF."
    )


# Muestra aviso temporal para la información del archivo
def info_archivo():
    messagebox.showinfo(
        "Pendiente",
        "Aquí se mostrará la información y metadatos del archivo.",
    )


# Muestra una ventana emergente con la información de ayuda del sistema
def mostrar_ayuda():
    texto_ayuda = (
        "Sistema de Gestión de Contactos (Tamaño Fijo e Índice).\n\n"
        f"• Tamaño fijo por registro: {TAM_REGISTRO} bytes.\n"
        "• Para buscar: Escriba el ID y presione 'Buscar por ID'.\n"
        "• Para modificar: Busque el contacto, edite los campos y presione 'Modificar'."
    )
    messagebox.showinfo("Ayuda del Sistema", texto_ayuda)


# Configura la ventana principal y coloca todos los elementos visuales
ventana = tk.Tk()
ventana.title("Gestión de Contactos")
ventana.geometry("420x500")
ventana.resizable(False, False)

frame_campos = tk.LabelFrame(ventana, text="Datos del Contacto", padx=10, pady=10)
frame_campos.pack(padx=15, pady=10, fill="x")

tk.Label(frame_campos, text="ID (Entero):").grid(
    row=0, column=0, sticky="w", pady=3
)
entry_id = tk.Entry(frame_campos, width=30)
entry_id.grid(row=0, column=1, pady=3, padx=5)

tk.Label(frame_campos, text="Nombre:").grid(row=1, column=0, sticky="w", pady=3)
entry_nombre = tk.Entry(frame_campos, width=30)
entry_nombre.grid(row=1, column=1, pady=3, padx=5)

tk.Label(frame_campos, text="Teléfono:").grid(
    row=2, column=0, sticky="w", pady=3
)
entry_telefono = tk.Entry(frame_campos, width=30)
entry_telefono.grid(row=2, column=1, pady=3, padx=5)

tk.Label(frame_campos, text="Correo:").grid(row=3, column=0, sticky="w", pady=3)
entry_correo = tk.Entry(frame_campos, width=30)
entry_correo.grid(row=3, column=1, pady=3, padx=5)

tk.Label(frame_campos, text="Ciudad:").grid(row=4, column=0, sticky="w", pady=3)
entry_ciudad = tk.Entry(frame_campos, width=30)
entry_ciudad.grid(row=4, column=1, pady=3, padx=5)

frame_contactos = tk.LabelFrame(ventana, text="Contactos", padx=10, pady=8)
frame_contactos.pack(padx=15, pady=5, fill="x")

tk.Button(
    frame_contactos, text="Agregar", width=16, command=agregar_contacto
).grid(row=0, column=0, padx=5, pady=3)
tk.Button(
    frame_contactos, text="Buscar por ID", width=16, command=buscar_contacto
).grid(row=0, column=1, padx=5, pady=3)
tk.Button(
    frame_contactos, text="Modificar", width=16, command=modificar_contacto
).grid(row=1, column=0, padx=5, pady=3)
tk.Button(
    frame_contactos, text="Limpiar Campos", width=16, command=limpiar_campos
).grid(row=1, column=1, padx=5, pady=3)

frame_exportar = tk.LabelFrame(ventana, text="Exportar", padx=10, pady=8)
frame_exportar.pack(padx=15, pady=5, fill="x")

tk.Button(
    frame_exportar, text="Exportar a JSON", width=16, command=exportar_json
).grid(row=0, column=0, padx=5, pady=3)
tk.Button(frame_exportar, text="Generar PDF", width=16, command=generar_pdf).grid(
    row=0, column=1, padx=5, pady=3
)

frame_herramientas = tk.LabelFrame(
    ventana, text="Herramientas y Ayuda", padx=10, pady=8
)
frame_herramientas.pack(padx=15, pady=5, fill="x")

tk.Button(
    frame_herramientas,
    text="Verificar Integridad",
    width=16,
    command=lambda: verificar_integridad(True),
).grid(row=0, column=0, padx=5, pady=3)
tk.Button(
    frame_herramientas,
    text="Crear Respaldo ZIP",
    width=16,
    command=crear_respaldo_zip,
).grid(row=0, column=1, padx=5, pady=3)
tk.Button(
    frame_herramientas, text="Info del Archivo", width=16, command=info_archivo
).grid(row=1, column=0, padx=5, pady=3)
tk.Button(
    frame_herramientas, text="Ayuda", width=16, command=mostrar_ayuda
).grid(row=1, column=1, padx=5, pady=3)

# Carga el índice y verifica la integridad del archivo automáticamente al abrir el programa
cargar_indice()
verificar_integridad(mostrar_exito=False)

ventana.mainloop()