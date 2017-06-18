#!/bin/bash

LOG_DIRECTORY="/var/log/backup_logs"
LOG="/var/log/backup_logs/game_saves.log"

function timestamp() {
    echo [$(date '+%Y-%m-%d %H:%M:%S')]
}

function log() {
    echo -e "$(timestamp) $1" >> $LOG
}

function log_error() {
    echo -e "$(timestamp) ERROR: $1" >> $LOG
}

if [ ! -d ${LOG_DIRECTORY} ]; then
    mkdir -p ${LOG_DIRECTORY}
    log "Creating backup log directory"
fi

log "Starting backup procedure"

BACKUP_MOUNT="/hdd/mybook"

if [ ! -d ${BACKUP_MOUNT} ]; then
    log "Creating mount point for backup device"
    mkdir -p ${BACKUP_MOUNT}
fi

unmount=false

if ! mountpoint -q /hdd/mybook; then
    log "Mounting backup device"
    mount ${BACKUP_MOUNT}

    if [ ! $? -eq 0 ]; then
        log_error "Unable to mount backup device"
        exit 2
    fi

    unmount=true
fi

BACKUP_DIR="${BACKUP_MOUNT}/GameSaveManager"

if [ ! -d ${BACKUP_DIR} ]; then
    log "Creating backup directory on backup device"
    mkdir -p ${BACKUP_DIR}
fi

INFO="flist,stats2"

rsync -aAX --info=${INFO} /hdd/media/game_saves/ ${BACKUP_DIR} | ts '[%Y-%m-%d %H:%M:%S]' >> $LOG

if [ "$unmount" = true ]; then
    log "Unmounting backup device"
    umount ${BACKUP_MOUNT}
fi

log "Finishing backup procedure"
echo "" >> $LOG
