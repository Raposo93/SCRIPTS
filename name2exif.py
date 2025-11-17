#!/usr/bin/env python3
"""
name2exif.py
Extrae fecha del nombre, la escribe en EXIF (exiftool) y mueve a YYYY/MM.
Registra salida en organize_by_date.log.

Uso:
    python3 name2exif.py /ruta/a/carpeta [excluir_carpeta] [--dry-run]
"""

import re
import sys
import os
import subprocess
from pathlib import Path
import logging
from PIL import Image
from datetime import datetime
import argparse

# --- Args ---
parser = argparse.ArgumentParser()
parser.add_argument("dir", help="Carpeta a procesar")
parser.add_argument("exclude", nargs="?", default=None, help="Carpeta a excluir (ruta relativa o absoluta)")
parser.add_argument("--move", action="store_true", help="Mover los archivos a YYYY/MM (por defecto solo actualiza EXIF)")
parser.add_argument("--dry-run", action="store_true", help="Simular sin mover ni escribir metadatos")
args = parser.parse_args()

DIR = Path(args.dir)
EXCLUDE = Path(args.exclude) if args.exclude else None
MOVE = args.move
DRY_RUN = args.dry_run

if not DIR.is_dir():
    print(f"Error: {DIR} no es un directorio válido")
    sys.exit(1)

# --- Logging (archivo + consola) ---
LOG_FILE = Path(__file__).parent / "organize_by_date.log"
LOG_FILE.write_text("", encoding="utf-8")
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger()

log.info("-" * 60)
log.info("Organizando archivos por fecha extraída del nombre")
log.info(f"Carpeta origen: {DIR}")
if EXCLUDE:
    log.info(f"Excluyendo carpeta: {EXCLUDE}")
if DRY_RUN:
    log.info("MODO PRUEBA — No se moverá ni modificará nada")
log.info(f"Log: {LOG_FILE.resolve()}")
log.info("-" * 60)
log.info("")



# --- Helpers ---
def valid_year(y):
    try:
        y_i = int(y)
        return 2001 <= y_i <= 2025
    except Exception:
        return False

def should_move_file(path, year, month):
    """Devuelve True si el archivo no está ya en su carpeta YYYY/MM."""
    parent_parts = path.parent.parts[-2:]
    return not (len(parent_parts) == 2 and parent_parts[0] == year and parent_parts[1] == month)

def move_file(path, dest_dir):
    """Mueve el archivo a dest_dir. Crea carpetas si es necesario."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    try:
        path.rename(dest_dir / path.name)
        log.info(f"   → Movido a {dest_dir}")
    except Exception as e:
        log.warning(f"   ⚠️ No se pudo mover {path}: {e}")

def convert_to_jpeg(path):
    """Convierte un archivo a JPEG y devuelve la nueva ruta."""
    new_path = path.with_suffix(".jpg")
    with Image.open(path) as img:
        rgb = img.convert("RGB")
        rgb.save(new_path, "JPEG")
    log.info(f"   → Convertido a JPEG: {new_path.name}")
    return new_path

def should_move_file(path, year, month):
    """Devuelve True si el archivo no está ya en su carpeta YYYY/MM."""
    parent_parts = path.parent.parts[-2:]
    return not (len(parent_parts) == 2 and parent_parts[0] == year and parent_parts[1] == month)

def move_file(path, dest_dir):
    """Mueve el archivo a dest_dir. Crea carpetas si es necesario."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    try:
        path.rename(dest_dir / path.name)
        log.info(f"   → Movido a {dest_dir}")
    except Exception as e:
        log.warning(f"   ⚠️ No se pudo mover {path}: {e}")
# --- Patrones ---
PATTERNS = [
    # 1) Genérico IMG/VID/PANO/AR_EFFECT con fecha y hora opcional
    (re.compile(
        r'^(?:IMG|VID|PANO|AR_EFFECT|IMG_)?[_-]?'
        r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})'      # YYYY MM DD
        r'(?:[-_]?(\d{2})(\d{2})(\d{2}))?'      # HH MM SS opcional
    ),
     lambda m: (
         m.group(1), m.group(2), m.group(3),
         f"{m.group(4) or '12'}:{m.group(5) or '00'}:{m.group(6) or '00'}",
         "GENERIC_YYYYMMDD[_HHMMSS]")),

    # 2) Screenshots / Screenrecorders con guiones o guion bajo
    (re.compile(
        r'^(?:Screenshot|Screenrecorder)[-_]?'
        r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})'         # YYYY MM DD
        r'(?:[-_]?(\d{2})[-_]?(\d{2})[-_]?(\d{2}))?' # HH MM SS opcional
    ),
     lambda m: (
         m.group(1), m.group(2), m.group(3),
         f"{m.group(4) or '12'}:{m.group(5) or '00'}:{m.group(6) or '00'}",
         "Screenshot/Screenrecorder_YYYYMMDD[_HHMMSS]")),

    # 3) IMG-YYYYMMDD-WA o null-YYYYMMDD-WA
    (re.compile(r'^(?:IMG|VID|null)-(\d{4})(\d{2})(\d{2})-WA'),
     lambda m: (m.group(1), m.group(2), m.group(3), "12:00:00", "IMG/VID/null-YYYYMMDD-WA")),

    # 4) P/V YYYYMMDD-HHMMSS y variantes cortas
    (re.compile(r'^[PV](\d{8})[-_]?(\d{6})(?:[-_].*)?$'),
     lambda m: (m.group(1)[:4], m.group(1)[4:6], m.group(1)[6:8],
                f"{m.group(2)[:2]}:{m.group(2)[2:4]}:{m.group(2)[4:6]}",
                "P/VYYYYMMDD-HHMMSS")),

    (re.compile(r'^[PV]([0-9])([0-9]{2})([0-9]{2})[-_]?([0-9]{2})([0-9]{2})([0-9]{2})(?:[-_].*)?$'),
     lambda m: (str(2010 + int(m.group(1))), m.group(2), m.group(3),
                f"{m.group(4)}:{m.group(5)}:{m.group(6)}", "P/V8MMDD-HHMMSS")),

    # 5) Flexible fechas con separadores y hora opcional
    (re.compile(r'^(20[01][0-9]|202[0-5])[-_. ]?([0-1][0-9])[-_. ]?([0-3][0-9])'
                r'(?:[_ .-]?([0-2][0-9])[-_.:]?([0-5][0-9])[-_.:]?([0-5][0-9]))?'),
     lambda m: (m.group(1), m.group(2), m.group(3),
                f"{m.group(4) or '12'}:{m.group(5) or '00'}:{m.group(6) or '00'}",
                "YYYY[sep]MM[sep]DD[HHMMSS]")),
]





# --- Procesar archivos ---
SIN_FECHA_FILE = Path(__file__).parent / "sin_fecha.txt"
SIN_FECHA_FILE.write_text("", encoding="utf-8")  # limpiar previo

all_files = [p for p in DIR.rglob("*") if p.is_file()]
total_files = len(all_files)
pattern_hits = {}
total_recognized = 0
total_unrecognized = 0
# VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic', '.tif', '.tiff', '.webp', '.bmp', '.gif'}
PHOTOS_VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.tif', '.tiff', '.webp', '.bmp', '.gif'}
VIDEOS_VALID_EXTENSIONS = {'.mp4', '.mov', '.mkv', '.avi', '.wmv', '.flv', '.webm', '.3gp'}



# --- Procesar archivos ---
for i, path in enumerate(all_files, start=1):
    print(f"[{i}/{total_files}] Procesando: {path.name}")
    
    ext = path.suffix.lower()

    is_photo = ext in PHOTOS_VALID_EXTENSIONS
    is_video = ext in VIDEOS_VALID_EXTENSIONS

    if not (is_photo or is_video):
        log.info(f"   → Ignorado (extensión no soportada): {path.name}")
        continue

    # Excluir carpeta
    if EXCLUDE:
        try:
            if EXCLUDE.resolve() in [p.resolve() for p in path.parents]:
                continue
        except Exception:
            if str(EXCLUDE) in str(path):
                continue

    name = path.name
    base = path.stem
    clean_base = re.sub(r'(\(\d+\)|-EFFECTS.*)$', '', base)
    detected = False

    for pattern, func in PATTERNS:
        m = pattern.match(clean_base)
        if not m:
            continue
        try:
            year, month, day, time_str, patname = func(m)
        except Exception:
            continue

        if not (valid_year(year) and 1 <= int(month) <= 12 and 1 <= int(day) <= 31):
            continue

        current_dir_name = DIR.name

        if current_dir_name == year:
            dest_dir = DIR / month
        else:
            dest_dir = DIR / year / month

        detected = True
        total_recognized += 1
        exif_date = f"{year}:{month}:{day} {time_str}"
        pretty = f"{year}-{month}-{day} {time_str}"

        log.info(f"📂 Archivo: {name}")
        log.info(f"   → Fecha detectada: {pretty} ({patname})")

        # --- EXIF ---
        if DRY_RUN:
            log.info(f"   [Simulación] exiftool -overwrite_original ... '{path}'")
        else:
            try:
                # subprocess.run([
                #     "exiftool", "-overwrite_original",
                #     f"-DateTimeOriginal={exif_date}",
                #     f"-CreateDate={exif_date}",
                #     f"-ModifyDate={exif_date}",
                #     str(path)
                # ], check=True)
                # log.info(f"   ✅ EXIF modificado con éxito: {path}")
                # --- FOTO: modificar EXIF ---
                if is_photo:
                    if DRY_RUN:
                        log.info(f"   [Simulación] exiftool -overwrite_original ... '{path}'")
                    else:
                        try:
                            subprocess.run([
                                "exiftool", "-overwrite_original",
                                f"-DateTimeOriginal={exif_date}",
                                f"-CreateDate={exif_date}",
                                f"-ModifyDate={exif_date}",
                                str(path)
                            ], check=True)
                            log.info(f"   EXIF modificado con éxito: {path}")

                        except subprocess.CalledProcessError:
                            log.warning(f"   exiftool falló en {path}")

                            # Intento de reconversión PNG -> JPEG si aplica
                            if ext == ".png":
                                new_path = convert_to_jpeg(path)
                                try:
                                    subprocess.run([
                                        "exiftool", "-overwrite_original",
                                        f"-DateTimeOriginal={exif_date}",
                                        f"-CreateDate={exif_date}",
                                        f"-ModifyDate={exif_date}",
                                        str(new_path)
                                    ], check=True)
                                    log.info(f"   EXIF modificado con éxito: {new_path}")
                                except subprocess.CalledProcessError as e2:
                                    log.warning(f"   exiftool también falló en {new_path}: {e2}")
                                    continue
                                
                # --- VÍDEO: actualizar mtime usando la fecha del filename ---
                elif is_video:
                    ts = datetime.strptime(f"{year}-{month}-{day} {time_str}", "%Y-%m-%d %H:%M:%S").timestamp()

                    if DRY_RUN:
                        log.info(f"   [Simulación] os.utime('{path}', {ts})")
                    else:
                        os.utime(path, (ts, ts))
                        log.info(f"   mtime actualizado: {path}")


            except subprocess.CalledProcessError:
                log.warning(f"   ⚠️ exiftool falló en {path}")
                # Intentar convertir PNG a JPEG si falla
                if path.suffix.lower() == ".png":
                    new_path = convert_to_jpeg(path)
                    try:
                        log.debug(f"   📂 exiftool segundo intento {path}")
                        subprocess.run([
                            "exiftool", "-overwrite_original",
                            f"-DateTimeOriginal={exif_date}",
                            f"-CreateDate={exif_date}",
                            f"-ModifyDate={exif_date}",
                            str(new_path)
                        ], check=True)
                        log.info(f"   ✅ EXIF modificado con éxito: {new_path}")
                    except subprocess.CalledProcessError as e2:
                        log.warning(f"   ⚠️ exiftool también falló en {new_path}: {e2}")
                        continue

        # --- Movimiento ---
        if MOVE and should_move_file(path, year, month):
            if DRY_RUN:
                log.info(f"   [Simulación] mv '{path}' '{dest_dir}/'")
            else:
                move_file(path, dest_dir)
        elif MOVE:
            log.info(f"   [Omitido] Ya está en {year}/{month}, no se mueve.")

        log.info("")
        break  # salir del bucle de patrones si se detecta fecha

    if not detected:
        total_unrecognized += 1
        log.info(f"⚠️  Sin fecha reconocible: {name}\n")
        with open(SIN_FECHA_FILE, "a", encoding="utf-8") as sf:
            sf.write(str(path) + "\n")


# --- Resumen final ---
log.info("-" * 60)
log.info("📊 Resumen de patrones detectados:")
for pat, count in pattern_hits.items():
    log.info(f"   {pat}: {count} archivo(s)")

log.info(f"✅ Total reconocidos: {total_recognized}")
log.info(f"❌ Total no reconocidos: {total_unrecognized}")
log.info(f"Log guardado en: {LOG_FILE.resolve()}")
log.info(f"Sin fecha listado en: {SIN_FECHA_FILE.resolve()}")
log.info("-" * 60)




#while IFS= read -r filename; do find /media/gonzalo/r21/photos -type f -name "${filename//[$'\r\n']}" -exec cp -t /media/gonzalo/r21/photos/test {} +; done < lista_archivos.txt