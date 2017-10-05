#!/bin/bash

LOG_DIRECTORY="/var/log/backup_logs"
LOG="${LOG_DIRECTORY}/mybook.log"

function timestamp() {
    echo [$(date '+%Y-%m-%d %H:%M:%S')]
}

function log() {
    echo -e "$(timestamp) $1" >> $LOG
}

function log_error() {
    echo -e "$(timestamp) ERROR: $1" >> $LOG
}

if [[ ! -d  ${LOG_DIRECTORY} ]]; then
    mkdir ${LOG_DIRECTORY}
fi

if [[ ! -e ${LOG} ]]; then
    touch ${LOG}
    log "Creating log file for backup"
fi

log "Beginning backup procedure"
TARGET_HOST="wdmycloud"


ping -c 1 ${TARGET_HOST} > /dev/null 2>&1

if [[ ! $? -eq 0 ]]; then
    log_error "Unable to communicate with smb host"
    exit 1
fi

BACKUP_MOUNT="/mnt/mycloud/pascal"

if [[ ! -d ${BACKUP_MOUNT} ]]; then
    log "Creating mount point for smb share"
    mkdir -p ${BACKUP_MOUNT}
fi

unmount_target=false

if ! mountpoint -q ${BACKUP_MOUNT}; then
    log "Mounting smb share"
    mount ${BACKUP_MOUNT}

    if [[ ! $? -eq 0 ]]; then
        log_error "Unable to mount backup device"
        exit 2
    fi

    unmount_target=true
fi

BACKUP_TARGET="${BACKUP_MOUNT}/Backups/mybook_backup"
BACKUP_SOURCE="/hdd/mybook/"

if [ ! -d ${BACKUP_TARGET} ]; then
    log "Creating backup directory on smb share"
    mkdir -p ${BACKUP_TARGET}
fi

unmount_source=false

if ! mountpoint -q ${BACKUP_SOURCE} ; then
    log "Mounting mybook for backup"
    mount ${BACKUP_SOURCE}

    if [[ ! $? -eq 0 ]]; then
        log_error "Unable to mount mybook"
        exit 3
    fi

    unmount_source=true
fi

INFO="flist,stats2"

rsync -aAX --partial --delete --info=${INFO} ${BACKUP_SOURCE} ${BACKUP_TARGET} | ts '[%Y-%m-%d %H:%M:%S]' >> ${LOG}

if [[ "$unmount_source" = true ]]; then
    log "Unmounting mybook"
    unmount ${BACKUP_SOURCE}
fi

if [[ "$unmount_target" = true ]]; then
    log "Unmounting smb share"
    umount ${BACKUP_MOUNT}
fi

log "Finishing backup procedure"
echo "" >> ${LOG}

