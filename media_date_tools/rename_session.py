#!/usr/bin/env python3
"""
rename_session.py
Renombra fotos sin fecha reconocible usando una fecha base, manteniendo orden numérico y actualizando mtime.
Uso:
    python3 rename_session.py /ruta/a/carpeta YYYY-MM-DD-hh-mm-ss [--dry-run]
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import argparse

# --- Args ---
parser = argparse.ArgumentParser()
parser.add_argument("folder", help="Carpeta a procesar")
parser.add_argument("datetime", help="Fecha y hora base YYYY-MM-DD-hh-mm-ss")
parser.add_argument("--dry-run", action="store_true", help="Simular renombrado sin modificar archivos")
args = parser.parse_args()

folder = Path(args.folder)
if not folder.is_dir():
    print(f"Error: {folder} no es un directorio válido")
    sys.exit(1)

try:
    base_datetime = datetime.strptime(args.datetime, "%Y-%m-%d-%H-%M-%S")
except ValueError:
    print("Error: la fecha debe tener formato YYYY-MM-DD-hh-mm-ss")
    sys.exit(1)

# Obtener solo archivos dentro del directorio (no recursivo), ordenados por nombre
files = sorted([f for f in folder.iterdir() if f.is_file()])

# Renombrar y actualizar mtime
for i, f in enumerate(files):
    new_dt = base_datetime + timedelta(seconds=i)
    new_name = new_dt.strftime("%Y%m%d_%H%M%S") + f.suffix.lower()
    new_path = folder / new_name

    if new_path.exists():
        print(f"⚠️  Saltado, ya existe: {new_name}")
        continue

    if args.dry_run:
        print(f"[Simulación] {f.name} -> {new_name} (mtime: {new_dt})")
    else:
        f.rename(new_path)
        ts = new_dt.timestamp()
        os.utime(new_path, (ts, ts))
        print(f"{f.name} -> {new_name} (mtime actualizado)")

