#!/bin/bash

# ============================================
# Backup data with Proxmox Backup Client
# Logs results and sends email notification
# ============================================

set -a
source /path/to/.env
set +a

: > "$LOGFILE"

SECONDS=0
START_TIME=$(date +"%Y-%m-%d %H:%M:%S")

echo "========== Backup started at $START_TIME ==========" >> "$LOGFILE"

systemd-run \
  --pipe --wait --pty \
  --property=LoadCredentialEncrypted=proxmox-backup-client.password:/root/.config/proxmox-backup/my-api-token.cred \
  --property=LoadCredentialEncrypted=proxmox-backup-client.fingerprint:/root/.config/proxmox-backup/my-fingerprint.cred \
  proxmox-backup-client backup "$BACKUP_NAME:$SOURCE_DIR" \
    --repository "$REPO" \
    --change-detection-mode metadata \
    --skip-e2big-xattr \
  >> "$LOGFILE" 2>&1

# Captura el codigo de salida del backup
STATUS=$?
echo "Backup exit code: $STATUS" >> "$LOGFILE"
echo "========== Backup ended at $(date +"%Y-%m-%d %H:%M:%S") ==========" >> "$LOGFILE"

if [ $STATUS -ne 0 ]; then
    SUBJECT="❌ Error in backup of data"
else
    SUBJECT="✅ Backup of data completed successfully"
fi

msmtp -a "$MSMTP_ACCOUNT" "$RECIPIENT_EMAIL" <<EOF
From: $SENDER_EMAIL
To: $RECIPIENT_EMAIL
Subject: $SUBJECT

$(cat "$LOGFILE")
EOF
