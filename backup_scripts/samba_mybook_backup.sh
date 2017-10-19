#!/bin/bash

SLACK_URL="https://hooks.slack.com/services/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"
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

function slack_message() {
    curl -X POST --data-urlencode "payload={\"text\": \"${1}\"}" ${SLACK_URL} > /dev/null 2>&1
}

if [[ ! -d  ${LOG_DIRECTORY} ]]; then
    mkdir ${LOG_DIRECTORY}
fi

if [[ ! -e ${LOG} ]]; then
    touch ${LOG}
    log "Creating log file for backup"
fi

log "Beginning backup procedure"
slack_message "MyBook Backup: Starting Backup"
TARGET_HOST="wdmycloud"


ping -c 1 ${TARGET_HOST} > /dev/null 2>&1

if [[ ! $? -eq 0 ]]; then
    log_error "Unable to communicate with smb host"
    slack_message "MyBook Backup: Failed due to a connection issue"
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
        slack_message "MyBook Backup: Failed due to not being able to mount smb share"
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
        slack_message "MyBook Backup: Failed due to not being able to mount mybook"
        exit 3
    fi

    unmount_source=true
fi

for source_dir in Linux_Backups; do
    BACKUP_SOURCE_DIR="${BACKUP_SOURCE}/${source_dir}"

    tar -c --use-compress-program="pigz --best" -f "${BACKUP_TARGET}/${source_dir}.tar.gz" ${BACKUP_SOURCE_DIR}
done


# TODO: Create backup for Linux Backups directory <18-10-17, pascal> #
# TODO: Create backup for Game Save directory <18-10-17, pascal> #

if [[ "$unmount_source" = true ]]; then
    log "Unmounting mybook"
    unmount ${BACKUP_SOURCE}
fi

if [[ "$unmount_target" = true ]]; then
    log "Unmounting smb share"
    umount ${BACKUP_MOUNT}
fi

log "Finishing backup procedure"
slack_message "MyBook Backup: Backup succesful"
echo "" >> ${LOG}

