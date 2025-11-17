#!/usr/bin/env python3
"""
name2exif.py
Extracts a date from the filename, writes it into EXIF (via exiftool),
and moves files into a YYYY/MM folder structure.
Logs output into organize_by_date.log.

Usage:
    python3 name2exif.py /path/to/folder [exclude_folder] [--dry-run] [--organize]
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

parser = argparse.ArgumentParser()
parser.add_argument("dir", help="Directory to process")
parser.add_argument("exclude", nargs="?", default=None,
                    help="Folder to exclude (relative or absolute path)")
parser.add_argument("--organize", action="store_true",
                    help="Organize files into YYYY/MM (default: only update EXIF)")
parser.add_argument("--dry-run", action="store_true",
                    help="Simulate without moving files or writing metadata")
args = parser.parse_args()

DIR = Path(args.dir)
EXCLUDE = Path(args.exclude) if args.exclude else None
MOVE = args.organize
DRY_RUN = args.dry_run

if not DIR.is_dir():
    print(f"Error: {DIR} is not a valid directory")
    sys.exit(1)

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
log.info("Organizing files by date extracted from filename")
log.info(f"Source folder: {DIR}")
if EXCLUDE:
    log.info(f"Excluding folder: {EXCLUDE}")
if DRY_RUN:
    log.info("DRY-RUN MODE — No files will be moved or modified")
log.info(f"Log: {LOG_FILE.resolve()}")
log.info("-" * 60)
log.info("")

def valid_year(y):
    try:
        y_i = int(y)
        return 1980 <= y_i <= 2050
    except Exception:
        return False

def convert_to_jpeg(path):
    new_path = path.with_suffix(".jpg")
    with Image.open(path) as img:
        rgb = img.convert("RGB")
        rgb.save(new_path, "JPEG")
    log.info(f"   → Converted to JPEG: {new_path.name}")
    return new_path

def should_move_file(path, year, month):
    parent_parts = path.parent.parts[-2:]
    return (
        len(parent_parts) != 2
        or parent_parts[0] != year
        or parent_parts[1] != month
    )
def move_file(path, dest_dir):
    dest_dir.mkdir(parents=True, exist_ok=True)
    try:
        path.rename(dest_dir / path.name)
        log.info(f"   → Moved to {dest_dir}")
    except Exception as e:
        log.warning(f"   Failed to move {path}: {e}")
        
def normalize_basename(base):
    return re.sub(r'(\(\d+\)|-EFFECTS.*)$', '', base)

def write_exif_photo(path, exif_date):
    subprocess.run([
        "exiftool", "-overwrite_original",
        f"-DateTimeOriginal={exif_date}",
        f"-CreateDate={exif_date}",
        f"-ModifyDate={exif_date}",
        str(path)
    ], check=True)
    
def write_mtime(path, timestamp):
    os.utime(path, (timestamp, timestamp))
def build_timestamp(year, month, day, time_str):
    return datetime.strptime(
        f"{year}-{month}-{day} {time_str}", "%Y-%m-%d %H:%M:%S"
    ).timestamp()
    
def apply_photo_metadata(path, exif_date, timestamp):
    try:
        write_exif_photo(path, exif_date)
        write_mtime(path, timestamp)
        return path

    except subprocess.CalledProcessError:
        if path.suffix.lower() != ".png":
            return None

        new_path = convert_to_jpeg(path)
        try:
            write_exif_photo(new_path, exif_date)
            write_mtime(new_path, timestamp)
            return new_path
        except subprocess.CalledProcessError:
            return None


PATTERNS = [
    (re.compile(
        r'^(?:IMG|VID|PANO|AR_EFFECT|IMG_)?[_-]?'
        r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})'
        r'(?:[-_]?(\d{2})(\d{2})(\d{2}))?'
    ),
     lambda m: (
         m.group(1), m.group(2), m.group(3),
         f"{m.group(4) or '12'}:{m.group(5) or '00'}:{m.group(6) or '00'}",
         "GENERIC_YYYYMMDD[_HHMMSS]")),

    (re.compile(
        r'^(?:Screenshot|Screenrecorder)[-_]?'
        r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})'
        r'(?:[-_]?(\d{2})[-_]?(\d{2})[-_]?(\d{2}))?'
    ),
     lambda m: (
         m.group(1), m.group(2), m.group(3),
         f"{m.group(4) or '12'}:{m.group(5) or '00'}:{m.group(6) or '00'}",
         "Screenshot/Screenrecorder_YYYYMMDD[_HHMMSS]")),

    (re.compile(r'^(?:IMG|VID|null)-(\d{4})(\d{2})(\d{2})-WA'),
     lambda m: (m.group(1), m.group(2), m.group(3), "12:00:00", "IMG/VID/null-YYYYMMDD-WA")),

    (re.compile(r'^[PV](\d{8})[-_]?(\d{6})(?:[-_].*)?$'),
     lambda m: (m.group(1)[:4], m.group(1)[4:6], m.group(1)[6:8],
                f"{m.group(2)[:2]}:{m.group(2)[2:4]}:{m.group(2)[4:6]}",
                "P/VYYYYMMDD-HHMMSS")),

    (re.compile(r'^[PV]([0-9])([0-9]{2})([0-9]{2})[-_]?([0-9]{2})([0-9]{2})([0-9]{2})(?:[-_].*)?$'),
     lambda m: (str(2010 + int(m.group(1))), m.group(2), m.group(3),
                f"{m.group(4)}:{m.group(5)}:{m.group(6)}", "P/V8MMDD-HHMMSS")),

    (re.compile(r'^(20[01][0-9]|202[0-5])[-_. ]?([0-1][0-9])[-_. ]?([0-3][0-9])'
                r'(?:[_ .-]?([0-2][0-9])[-_.:]?([0-5][0-9])[-_.:]?([0-5][0-9]))?'),
     lambda m: (m.group(1), m.group(2), m.group(3),
                f"{m.group(4) or '12'}:{m.group(5) or '00'}:{m.group(6) or '00'}",
                "YYYY[sep]MM[sep]DD[HHMMSS]")),
]



NO_DATE_FILE = Path(__file__).parent / "sin_fecha.txt"

all_files = [p for p in DIR.rglob("*") if p.is_file()]
total_files = len(all_files)
pattern_hits: dict[str, int] = {}
total_recognized = 0
total_unrecognized = 0
PHOTOS_VALID_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.heic', '.heif',
    '.tif', '.tiff', '.webp', '.bmp', '.gif'
}
VIDEOS_VALID_EXTENSIONS = {
    '.mp4', '.mov', '.mkv', '.avi', '.wmv',
    '.flv', '.webm', '.3gp'
}


for i, path in enumerate(all_files, start=1):
    log.info(f"[{i}/{total_files}] Processing: {path.name}")
    
    ext = path.suffix.lower()

    is_photo = ext in PHOTOS_VALID_EXTENSIONS
    is_video = ext in VIDEOS_VALID_EXTENSIONS

    if not (is_photo or is_video):
        log.info(f"   → Ignored (unsupported extension): {path.name}")
        continue

    if EXCLUDE:
        try:
            exclude_resolved = EXCLUDE.resolve()
            if any(parent == exclude_resolved for parent in path.parents):
                continue
        except Exception:
            if str(EXCLUDE) in str(path):
                continue

    name = path.name
    base = path.stem
    clean_base = normalize_basename(base)
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
        pattern_hits[patname] = pattern_hits.get(patname, 0) + 1

        log.info(f"📂 File: {name}")
        log.info(f"   → Date detected: {pretty} ({patname})")

        # --- EXIF ---
        if DRY_RUN:
            log.info(f"   [Dry-run] exiftool -overwrite_original ... '{path}'")
        else:
                ts = build_timestamp(year, month, day, time_str)
                if is_photo:
                    if DRY_RUN:
                        log.info(f"   [Simulación] exiftool -overwrite_original ... '{path}'")
                    else:
                            result_path = apply_photo_metadata(path, exif_date, ts)
                            if result_path:
                                path = result_path

                else :
                    if DRY_RUN:
                        log.info(f"   [Dry-run] os.utime('{path}', {ts})")
                    else:
                        write_mtime(path, ts)
                        log.info(f"   mtime updated: {path}")

        if MOVE and should_move_file(path, year, month):
            if DRY_RUN:
                log.info(f"   [Dry-run] mv '{path}' '{dest_dir}/'")
            else:
                move_file(path, dest_dir)
        elif MOVE:
            log.info(f"   [Skipped] Already in {year}/{month}, not moving")

        log.info("")
        break

    if not detected:
        total_unrecognized += 1
        log.info(f"⚠️  No recognizable date: {name}\n")
        with open(NO_DATE_FILE, "a", encoding="utf-8") as sf:
            sf.write(str(path) + "\n")


log.info("-" * 60)
log.info("Pattern summary:")
for pat, count in pattern_hits.items():
    log.info(f"   {pat}: {count} file(s)")

log.info(f"Recognized: {total_recognized}")
log.info(f"Unrecognized: {total_unrecognized}")
log.info(f"Log saved at: {LOG_FILE.resolve()}")
log.info(f"Unrecognized files listed at: {NO_DATE_FILE.resolve()}")
log.info("-" * 60)