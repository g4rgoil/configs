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
TARGET_HOST="optiplex"  # 192.168.100.200 


ping -c 1 ${TARGET_HOST} > /dev/null 2>&1

if [[ ! $? -eq 0 ]]; then
    log_error "Unable to communicate with target host"
    slack_message "MyBook Backup: Failed, can't connect to target host"
    exit 1
fi

BACKUP_MOUNT="/mnt/optiplex"

if [[ ! -d ${BACKUP_MOUNT} ]]; then
    log "Creating mount point for target device"
    mkdir -p ${BACKUP_MOUNT}
fi

unmount_target=false

if ! mountpoint -q ${BACKUP_MOUNT}; then
    log "Mounting target device"
    mount ${BACKUP_MOUNT}

    if [[ ! $? -eq 0 ]]; then
        log_error "Unable to mount target device"
        slack_message "MyBook Backup: Failed, can't mount target device"
        exit 2
    fi

    unmount_target=true
fi

BACKUP_TARGET="${BACKUP_MOUNT}/mybook_backup"
BACKUP_SOURCE="/hdd/mybook/"

if [ ! -d ${BACKUP_TARGET} ]; then
    log "Creating backup directory on target_device"
    mkdir -p ${BACKUP_TARGET}
fi

unmount_source=false

if ! mountpoint -q ${BACKUP_SOURCE} ; then
    log "Mounting mybook for backup"
    mount ${BACKUP_SOURCE}

    if [[ ! $? -eq 0 ]]; then
        log_error "Unable to mount mybook"
        slack_message "MyBook Backup: Failed, can't mount mybook"
        exit 3
    fi

    unmount_source=true
fi

for source_dir in Linux_Backups; do
    BACKUP_SOURCE_DIR="${BACKUP_SOURCE}/${source_dir}"
    BACKUP_TARGET_ARCHIVE="${BACKUP_TARGET}/${source_dir}.tar.gz"

    tar -c --use-compress-program="pigz -2" ${BACKUP_SOURCE_DIR} > ${BACKUP_TARGET_ARCHIVE}
done


# TODO: Create backup for Linux Backups directory <18-10-17, pascal> #
# TODO: Create backup for Game Save directory <18-10-17, pascal> #

if [[ "$unmount_source" = true ]]; then
    log "Unmounting mybook"
    unmount ${BACKUP_SOURCE}
fi

if [[ "$unmount_target" = true ]]; then
    log "Unmounting target device"
    umount ${BACKUP_MOUNT}
fi

log "Finishing backup procedure"
slack_message "MyBook Backup: Backup succesful"
echo "" >> ${LOG}

