#!/bin/bash

SLACK_URL="https://hooks.slack.com/services/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"
LOG_DIRECTORY="/var/log/backup_logs"
LOG="$LOG_DIRECTORY/media.log"

function timestamp() {
    echo ["$(date '+%Y-%m-%d %H:%M:%S')"]
}

function log() {
    echo -e "$(timestamp) $1" >> $LOG
}

function log_error() {
    echo -e "$(timestamp) ERROR: $1" >> $LOG
}

function slack_message() {
    curl -X POST --data-urlencode "payload={\"text\": \"${1}\"}" ${SLACK_URL} > /dev/null 2>&1
}

if [[ ! -d ${LOG_DIRECTORY} ]]; then
    mkdir -p ${LOG_DIRECTORY}
    log "Creating backup log directory"
fi

log "Starting backup procedure"

BACKUP_MOUNT="/hdd/mybook"

if [[ ! -d ${BACKUP_MOUNT} ]]; then
    log "Creating mount point for backup device"
    mkdir -p ${BACKUP_MOUNT}
fi

unmount=false

if ! mountpoint -q ${BACKUP_MOUNT}; then
    log "Mounting backup device"

    if ! mount ${BACKUP_MOUNT}; then
        log_error "Unable to mount backup device"
        slack_message "$(hostname): Backup failed, unable to mount backup target."
        exit 2
    fi

    if ! mountpoint -q ${BACKUP_MOUNT}; then
        log_error "Unable to mount backup device"
        slack_message "$(hostname): Backup failed, unable to mount backup target."
        exit 2
    fi

    unmount=true
fi

BACKUP_DIR="${BACKUP_MOUNT}/HDD_Backups"

if [[ ! -d ${BACKUP_DIR} ]]; then
    log "Creating backup directory on backup device"
    mkdir -p ${BACKUP_DIR}
fi

EXCLUDE_FILE="/etc/backup_scripts/media_backup.exclude"
INFO="flist,stats2"

BACKUP_TARGET="${BACKUP_DIR}/media"
BACKUP_SRC="/hdd/media"


log "Creating backup"
rsync -aAHx --partail --delete --info=${INFO} --exclude-from=${EXCLUDE_FILE} "${BACKUP_SRC}" "${BACKUP_TARGET}" | ts '[%Y-%m-%d %H:%M:%S]' >> $LOG


if [[ "$unmount" = true ]]; then
    log "Unmounting backup device"
    umount ${BACKUP_MOUNT}
fi

log "Finishing backup procedure"
echo "" >> $LOG
