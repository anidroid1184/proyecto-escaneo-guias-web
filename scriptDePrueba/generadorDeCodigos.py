import os
import pandas as pd
import qrcode
import barcode
from barcode.writer import ImageWriter
import random
import string

# === Función para generar código aleatorio único ===


def generar_codigo_unico(existing_codes, length=12):
    while True:
        code = ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=length))
        if code not in existing_codes:
            existing_codes.add(code)
            return code

# === Funciones para generar QR y código de barras ===


def generar_qr(data, filename):
    if pd.notna(data):
        img = qrcode.make(str(data))
        img.save(filename)


def generar_barcode(data, filename):
    if pd.notna(data):
        code128 = barcode.get('code128', str(data), writer=ImageWriter())
        code128.save(filename)


# === Cargar archivo Excel ===
df = pd.read_excel("ProyectoEscaneopaquetes.xlsx")

# === Crear carpetas de salida ===
os.makedirs("output_file/output_qr", exist_ok=True)
os.makedirs("output_file/output_barcode", exist_ok=True)
os.makedirs("output_random/output_qr", exist_ok=True)
os.makedirs("output_random/output_barcode", exist_ok=True)

# === Generar códigos reales (del Excel) en output_file ===
for idx, row in df.iterrows():
    tracking = row.get("TRACKING")
    guia = row.get("GUIA INTERNACIONAL")

    # QR
    generar_qr(tracking, f"output_file/output_qr/{idx}_tracking_qr.png")
    generar_qr(guia, f"output_file/output_qr/{idx}_guia_qr.png")

    # Código de barras
    generar_barcode(
        tracking, f"output_file/output_barcode/{idx}_tracking_barcode")
    generar_barcode(guia, f"output_file/output_barcode/{idx}_guia_barcode")

# === Generar códigos aleatorios en output_random ===
# Guardar todos los códigos originales para evitar repeticiones
codigos_existentes = set(df["TRACKING"].dropna().astype(str).tolist() +
                         df["GUIA INTERNACIONAL"].dropna().astype(str).tolist())

for idx, _ in df.iterrows():
    # Generar dos códigos aleatorios por fila
    codigo_random_1 = generar_codigo_unico(codigos_existentes)
    codigo_random_2 = generar_codigo_unico(codigos_existentes)

    # QR
    generar_qr(codigo_random_1,
               f"output_random/output_qr/{idx}_codigo1_qr.png")
    generar_qr(codigo_random_2,
               f"output_random/output_qr/{idx}_codigo2_qr.png")

    # Código de barras
    generar_barcode(codigo_random_1,
                    f"output_random/output_barcode/{idx}_codigo1_barcode")
    generar_barcode(codigo_random_2,
                    f"output_random/output_barcode/{idx}_codigo2_barcode")

print("✅ Códigos generados correctamente en 'output_file' (reales) y 'output_random' (aleatorios).")
