#!/bin/bash

# TODO: Add variable for location of scripts

SLACK_URL="https://hooks.slack.com/services/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"
LOG_DIRECTORY="/var/log/backup_logs"
LOG="$LOG_DIRECTORY/root.log"

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

TARGET_HOST="pascal_arch"
TARGET_DIR="/mybook"

# ping -c 1 ${TARGET_HOST} > /dev/null 2>&1

if ! ping -c 1 ${TARGET_HOST} > /dev/null 2>&1; then
    log_error "Unable to comunicate with nfs host"
    slack_message "$(hostname): Backup failed, unable to communicate with target host"
    exit 1
fi

BACKUP_MOUNT="/mnt/nfs/mybook"

if [[ ! -d ${BACKUP_MOUNT} ]]; then
    log "Creating mount point for backup device"
    mkdir -p "${BACKUP_MOUNT}"
fi

unmount=false

if ! mountpoint -q ${BACKUP_MOUNT}; then
    log "Mounting backup device"

    if ! mount ${BACKUP_MOUNT}; then
        log_error "Unable to mount backup device"
        slack_message "$(hostname): Backup failed, unable to mount backup target. "
        exit 2
    fi

    unmount=true
fi

# TODO: Make snapshot, mount snapshot and back it up <14-12-17, pascal> #
# TODO: Delete snapshot after backup <14-12-17, pascal> #
# TODO: Map local users to nfs share <14-12-17, pascal> #

VOLUME_GROUP="/dev/volgroup0"
VOLUME_NAME="root"
SOURCE_VOLUME="${VOLUME_GROUP}/${VOLUME_NAME}"
SNAPSHOT_NAME="temp-snap"
SNAPSHOT_VOLUME="${VOLUME_GROUP}/${SNAPSHOT_NAME}"

if ! lvcreate -L 2G -n "${SNAPSHOT_NAME}" -s ${SOURCE_VOLUME}; then
    log_error "Unable to create snapshot"
    slack_message "$(hostname): Backup failed, unable to create snapshot."
    exit 3
fi

SNAPSHOT_MOUNT="/mnt/snapshot"

if [[ ! -d ${SNAPSHOT_MOUNT} ]]; then
    mkdir -p "${SNAPSHOT_MOUNT}"
fi

if ! mount "${SNAPSHOT_VOLUME}" "${SNAPSHOT_MOUNT}"; then
    log_error "Unable to mount snapshot"
    slack_message "$(hostname): Backup failed, unable to mount snapshot"
    exit 2
fi



BACKUP_DIR="${BACKUP_MOUNT}/Linux_Backups/xps13_arch"

if [[ ! -d ${BACKUP_DIR} ]]; then
    log "Creating backup directory on backup device"
    mkdir -p ${BACKUP_DIR}
fi

EXCLUDE_FILE="/etc/backup_scripts/root_backup.exclude"
INFO="flist,stats2"

BACKUP_TARGET="${BACKUP_DIR}/xps13_arch_$(date '+%Y-%m-%d')"

if [[ ! "$(ls -A ${BACKUP_DIR})" ]]; then
    log "Creating initial backup as \"${BACKUP_TARGET}\""
    rsync -aAHX --partial --info=${INFO} --exclude-from=${EXCLUDE_FILE} / "${BACKUP_TARGET}" | ts '[%Y-%m-%d %H:%M:%S]' >> $LOG

else
    if [[ -d ${BACKUP_TARGET} ]]; then
        x=1
        while [[ -d "${BACKUP_TARGET}_${x}" ]]; do
            ((x++))
        done

        BACKUP_TARGET="${BACKUP_TARGET}_${x}"
    fi

    BACKUP_PARENT="${BACKUP_DIR}/$(ls -r1 "${BACKUP_DIR}" | head -n 1)"

    log "Creating incremental backup as \"${BACKUP_TARGET}\" based on \"${BACKUP_PARENT}\""
    rsync -aAHX --partial --delete --info=${INFO} --exclude-from=${EXCLUDE_FILE} --link-dest="${BACKUP_PARENT}" / "${BACKUP_TARGET}" | ts '[%Y-%m-%d %H:%M:%S]' >> $LOG
fi

for deprecated_backup in $(ls -1 "${BACKUP_DIR}" | head -n -10); do
    log "Deleting deprecated backup \"${deprecated_backup}\""
    rm -r "${BACKUP_DIR:?}/${deprecated_backup:?}"
done

if [[ "$unmount" = true ]]; then
    log "Unmounting backup device"
    umount ${BACKUP_MOUNT}
fi

log "Finishing backup procedure"
echo "" >> $LOG
