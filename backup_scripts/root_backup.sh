#!/bin/bash

LOG_DIRECTORY="/var/log/backup_logs"
LOG="$LOG_DIRECTORY/root.log"

function timestamp() {
    echo [$(date '+%Y-%m-%d %H:%M:%S')]
}

function log() {
    echo -e "$(timestamp) $1" >> $LOG
}

function log_error() {
    echo -e "$(timestamp) ERROR: $1" >> $LOG
}

if [[ ! -d ${LOG_DIRECTORY} ]]; then
    mkdir -p ${LOG_DIRECTORY}
    log "Creating backup log directory"
fi

log "Starting update procedure"

BACKUP_MOUNT="/hdd/mybook"

if [[ ! -d ${BACKUP_MOUNT} ]]; then
    log "Creating mount point for backup device"
    mkdir -p ${BACKUP_MOUNT}
fi

unmount=false

if ! mountpoint -q ${BACKUP_MOUNT}; then
    log "Mounting backup device"
    mount ${BACKUP_MOUNT}

    if [[ ! $? -eq 0 ]]; then
        log_error "Unable to mount backup device"
        exit 2
    fi

    unmount=true
fi

BACKUP_DIR="${BACKUP_MOUNT}/Linux_Backups/desktop_arch"

if [[ ! -d ${BACKUP_DIR} ]]; then
    log "Creating backup directory on backup device"
    mkdir -p ${BACKUP_DIR}
fi

EXCLUDE_FILE="/etc/backup_scripts/root_backup.exclude"
INFO="flist,stats2"

BACKUP_TARGET="${BACKUP_DIR}/desktop_arch_$(date '+%Y-%m-%d')"

if [[ ! "$(ls -A ${BACKUP_DIR})" ]]; then
    log "Creating initial backup as \"${BACKUP_TARGET}\""
    rsync -aAHX --partial --info=${INFO} --exclude-from=${EXCLUDE_FILE} / ${BACKUP_TARGET} | ts '[%Y-%m-%d %H:%M:%S]' >> $LOG

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
    rsync -aAHX --partial --delete --info=${INFO} --exclude-from=${EXCLUDE_FILE} --link-dest=${BACKUP_PARENT} / ${BACKUP_TARGET} | ts '[%Y-%m-%d %H:%M:%S]' >> $LOG
fi

for deprecated_backup in $(ls -1 "${BACKUP_DIR}" | head -n -10); do
    log "Deleting deprecated backup \"${deprecated_backup}\""
    rm -r "${BACKUP_DIR}/${deprecated_backup}"
done

# TODO: reactivate cronjob (/root/backup.cron) <05-10-17> #

if [[ "$unmount" = true ]]; then
    log "Unmounting backup device"
    umount ${BACKUP_MOUNT}
fi

log "Finishing backup procedure"
echo "" >> $LOG
